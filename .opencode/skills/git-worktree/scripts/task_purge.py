"""Human-only task erasure: inventory, policy, durable phases and narrow effects."""
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import stat
import sys
import uuid


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def task_snapshot(connection, board_id):
    connection.row_factory = sqlite3.Row
    item = connection.execute("SELECT * FROM planned_items WHERE id=?", (board_id,)).fetchone()
    if item is None:
        raise ValueError("canonical task does not exist")
    return {"item": dict(item), "criteria": [dict(row) for row in connection.execute(
        "SELECT * FROM acceptance_criteria WHERE plan_item_id=? ORDER BY position", (board_id,))],
        "active": [dict(row) for row in connection.execute(
            "SELECT * FROM active_work WHERE plan_item_id=?", (board_id,))]}


def validate_dependencies(rows, board_id):
    dependents = [row["id"] for row in rows if row["id"] != board_id
                  and board_id in re.findall(r"\bBOARD-\d+\b", row["blocked_by"])]
    if dependents:
        raise ValueError("dependent tasks: " + ", ".join(dependents))


def safe_path(path, root, allow_root=False):
    path, root = Path(path), Path(root)
    if ".." in path.parts or not path.is_absolute() or not root.is_absolute():
        raise ValueError("unsafe or traversal path")
    if not (path == root and allow_root) and root not in path.parents:
        raise ValueError("path outside selected boundary: %s" % path)
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ValueError("symbolic link refused: %s" % component)
    if path == root:
        return path
    for component in path.parents:
        if component == root:
            break
        if (component / ".git").exists():
            raise ValueError("foreign repository boundary: %s" % component)
    return path


def tree_stamp(path, root_marker=None):
    path = Path(path)
    info = path.lstat()
    metadata = stable_metadata(info)
    if stat.S_ISREG(info.st_mode):
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NOATIME", 0)
        with os.fdopen(os.open(path, flags), "rb") as stream:
            before = os.fstat(stream.fileno())
            content = hashlib.sha256()
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                content.update(chunk)
            if (stable_metadata(before) != stable_metadata(os.fstat(stream.fileno()))
                    or stable_metadata(path.lstat()) != stable_metadata(before)):
                raise ValueError("target changed during inventory")
        return [metadata, content.hexdigest()]
    if not stat.S_ISDIR(info.st_mode):
        raise ValueError("non-regular target refused: %s" % path)
    children = []
    for child in sorted(path.iterdir()):
        if child.name == ".git" and (child != root_marker or not child.is_file()):
            raise ValueError("nested repository refused: %s" % child)
        children.append([child.name, tree_stamp(child, root_marker)])
    after = path.lstat()
    if metadata != stable_metadata(after):
        raise ValueError("target changed during inventory")
    return [metadata, children]


def stable_metadata(info):
    return [info.st_dev, info.st_ino, info.st_mode, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns]


def load_guard():
    spec = importlib.util.spec_from_file_location("purge_guard", Path(__file__).with_name("guard.py"))
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    return guard


def protected_branches(repo, control):
    guard = load_guard()
    path = safe_path(control / ".opencode" / "policies" / "git-policy.json", control)
    policy = guard.load_policy(str(path)) if path.exists() else None
    return guard.protected_branch_names(str(repo), policy)


def checked_git(wt, repo, *args):
    code, output, error = wt.git(str(repo), *args)
    if code:
        raise ValueError("Git operation failed (%d): %s" % (code, error))
    return output.strip()


def targets_for_task(wt, control, rows, snapshot, orphan, repos):
    item = snapshot["item"]
    board_id = item["id"]
    allowed_repos = {name.strip() for name in item["repos"].split(",")}
    recorded = wt.row_worktrees(snapshot["active"][0]["branch_worktree"], str(control)) \
        if snapshot["active"] else []
    if orphan and item["terminal_outcome"] != "cancelled":
        raise ValueError("orphan evidence is only allowed for cancelled tasks")
    explicit = []
    for repo_id, path, branch in orphan:
        if repo_id not in allowed_repos:
            raise ValueError("orphan repository not owned by selected task")
        repo, error = wt.resolve_repo(str(control), repos, repo_id)
        if error:
            raise ValueError(error)
        explicit.append((path if os.path.isabs(path) else str(control / path), branch, repo_id))
    mapped = []
    for path, branch in recorded:
        matches = []
        for repo_id in allowed_repos:
            if repo_id not in repos:
                continue
            repo, error = wt.resolve_repo(str(control), repos, repo_id)
            if not error and Path(repo, wt.WORKTREES_DIR) in Path(path).parents:
                matches.append(repo_id)
        if len(matches) != 1:
            raise ValueError("ambiguous recorded worktree repository")
        mapped.append((path, branch, matches[0]))
    if len({path for path, _, _ in mapped + explicit}) != len(mapped + explicit):
        raise ValueError("duplicate or ambiguous worktree ownership")
    if item["terminal_outcome"] == "cancelled":
        claimed = {path for row in rows if row["id"] != board_id
                   for path, _ in wt.row_worktrees(row["branch_worktree"], str(control))}
        supplied = {path for path, _, _ in explicit}
        for repo_id in allowed_repos - {"-", ""}:
            repo, error = wt.resolve_repo(str(control), repos, repo_id)
            if error:
                raise ValueError(error)
            safe_path(repo, control, allow_root=True)
            for entry in wt.list_worktrees(repo):
                if entry["path"] != repo and entry["path"] not in claimed | supplied:
                    raise ValueError("unclaimed worktree; cancelled-task ownership needs explicit --orphan evidence")
    targets = []
    for path, branch, repo_id in mapped + explicit:
        repo, error = wt.resolve_repo(str(control), repos, repo_id)
        if error:
            raise ValueError(error)
        repo = safe_path(repo, control, allow_root=True)
        if Path(wt.repo_of_path(str(repo)) or "") != repo or not wt.is_git_repo(str(repo)):
            raise ValueError("mapped repository is not its primary checkout")
        path = safe_path(path, repo / wt.WORKTREES_DIR)
        if path.parent != repo / wt.WORKTREES_DIR:
            raise ValueError("worktree must be a direct child of the worktree root")
        base, error = wt.resolve_base(str(repo), None)
        if error or branch in protected_branches(repo, control) | {base}:
            raise ValueError("protected or unresolved branch")
        checked_git(wt, repo, "check-ref-format", "--branch", branch)
        ref = "refs/heads/" + branch
        tip = checked_git(wt, repo, "rev-parse", "--verify", ref)
        worktrees = wt.list_worktrees(str(repo))
        matching = [entry for entry in worktrees if entry["path"] == str(path)]
        if len(matching) != 1 or matching[0].get("branch") != branch:
            raise ValueError("worktree registration does not match evidence")
        if any(entry["path"] != str(path) and entry.get("branch") == branch for entry in worktrees):
            raise ValueError("branch is checked out in another worktree")
        for row in rows:
            if row["id"] == board_id:
                continue
            for other_path, other_branch in wt.row_worktrees(row["branch_worktree"], str(control)):
                if str(path) == other_path or branch == other_branch:
                    raise ValueError("another task claims path or branch")
        if Path(wt.repo_of_path(str(path)) or "") != repo:
            raise ValueError("foreign worktree repository")
        if checked_git(wt, path, "symbolic-ref", "--short", "HEAD") != branch:
            raise ValueError("worktree branch changed")
        targets.extend([{"kind": "worktree", "path": str(path), "repo": str(repo),
                         "branch": branch, "tip": tip, "stamp": digest(tree_stamp(path, path / ".git"))},
                        {"kind": "branch", "repo": str(repo), "branch": branch, "tip": tip}])
    return targets


def report_targets(control, board_id):
    targets = []
    for scope in ("web", "api", "mobile", "factory"):
        qa = safe_path(control / "artifacts" / scope / "qa", control)
        if not qa.exists():
            continue
        for day in sorted(qa.iterdir()):
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day.name):
                continue
            safe_path(day, control)
            if not day.is_dir():
                continue
            path = safe_path(day / board_id, control)
            if path.exists():
                targets.append({"kind": "file", "path": str(path), "stamp": digest(tree_stamp(path))})
    path = safe_path(control / ".factory-state" / "reviews" / (board_id + "-ledger.md"), control)
    if path.exists():
        targets.append({"kind": "file", "path": str(path), "stamp": digest(tree_stamp(path))})
    return targets


def read_inventory(connection, board_id):
    snapshot = task_snapshot(connection, board_id)
    rows = [dict(row) for row in connection.execute("SELECT p.id, p.blocked_by, a.branch_worktree "
            "FROM planned_items p LEFT JOIN active_work a ON a.plan_item_id=p.id")]
    validate_dependencies(rows, board_id)
    return snapshot, rows


def confirm(board_id):
    if not sys.stdin.isatty() or not sys.stderr.isatty():
        raise ValueError("purge requires a real interactive terminal")
    sys.stderr.write("Human-only purge; local deterrent, not an OS security boundary.\n"
                     "Type the exact task ID %s to erase it: " % board_id)
    sys.stderr.flush()
    answer = sys.stdin.readline()
    if answer != board_id + "\n":
        raise ValueError("confirmation did not match the exact task ID")


def save_manifest(wt, path, record):
    temporary = path.with_name(".manifest-%s.json" % uuid.uuid4().hex)
    wt.publish_finalize_journal(str(temporary), record)
    os.replace(temporary, path)
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def validate_manifest(wt, manifest, control, repos):
    board_id = manifest["board"]
    if (not isinstance(manifest.get("targets"), list)
            or not isinstance(manifest.get("complete"), bool)
            or not isinstance(manifest.get("task_digest"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", manifest["task_digest"])):
        raise ValueError("invalid purge manifest")
    seen = set()
    for target in manifest["targets"]:
        if not isinstance(target, dict):
            raise ValueError("invalid purge target")
        if target.get("phase") not in ("pending", "running", "done"):
            raise ValueError("invalid purge phase")
        kind = target.get("kind")
        if kind in ("branch", "worktree"):
            repo = safe_path(target["repo"], control, allow_root=True)
            registered = [wt.resolve_repo(str(control), repos, key)[0] for key in repos]
            if str(repo) not in registered or Path(wt.repo_of_path(str(repo)) or "") != repo:
                raise ValueError("manifest repository is not a registered primary checkout")
            base, error = wt.resolve_base(str(repo), None)
            if error or target["branch"] in protected_branches(repo, control) | {base}:
                raise ValueError("protected manifest branch")
            checked_git(wt, repo, "check-ref-format", "--branch", target["branch"])
            if not re.fullmatch(r"[0-9a-f]{40,64}", target["tip"]):
                raise ValueError("invalid manifest branch tip")
            if kind == "worktree":
                path = safe_path(target["path"], repo / wt.WORKTREES_DIR)
                if path.parent != repo / wt.WORKTREES_DIR:
                    raise ValueError("unsafe manifest worktree")
        elif kind == "file":
            path = safe_path(target["path"], control)
            relative = path.relative_to(control)
            parts = relative.parts
            artifact = (len(parts) == 5 and parts[0] == "artifacts" and
                        parts[1] in ("web", "api", "mobile", "factory") and parts[2] == "qa"
                        and re.fullmatch(r"\d{4}-\d{2}-\d{2}", parts[3]) and parts[4] == board_id)
            if not artifact and parts != (".factory-state", "reviews", board_id + "-ledger.md"):
                raise ValueError("unsafe manifest report/ledger ownership")
        else:
            raise ValueError("invalid manifest target kind")
        identity = (kind, target.get("path"), target.get("repo"), target.get("branch"))
        if identity in seen:
            raise ValueError("duplicate manifest target")
        seen.add(identity)


def copy_backup(source, target, state):
    info = source.lstat()
    if stat.S_ISREG(info.st_mode):
        state._copy_snapshot_file(str(source), str(target))
        os.chmod(target, 0o600)
    elif stat.S_ISDIR(info.st_mode):
        target.mkdir(mode=0o700)
        for child in source.iterdir():
            copy_backup(child, target / child.name, state)
    else:
        raise ValueError("backup refused non-regular content")


def content_identity(stamp):
    if stat.S_ISREG(stamp[0][2]):
        return ["file", stamp[1]]
    return ["directory", [[name, content_identity(child)] for name, child in stamp[1]]]


def backup_stamp(target, path=None):
    path = Path(path or target["path"])
    return tree_stamp(path, path / ".git" if target["kind"] == "worktree" else None)


def prepare_backup(wt, state, manifest_path, manifest, snapshot):
    backup = manifest["backup"]
    if not backup["enabled"]:
        return
    if backup["phase"] != "complete":
        attempt = "content-" + uuid.uuid4().hex
        backup["attempts"].append(attempt)
        backup.update(phase="copying", directory=attempt)
        save_manifest(wt, manifest_path, manifest)
        directory = manifest_path.parent / attempt
        directory.mkdir(mode=0o700)
        task_file = directory / "task.json"
        descriptor = os.open(task_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            json.dump(snapshot, stream)
            stream.flush()
            os.fsync(stream.fileno())
        content_digests = {}
        for index, target in enumerate(manifest["targets"]):
            if "path" not in target:
                continue
            revalidate_target(wt, target)
            copy_backup(Path(target["path"]), directory / str(index), state)
            revalidate_target(wt, target)
            if content_identity(backup_stamp(target, directory / str(index))) != content_identity(backup_stamp(target)):
                raise ValueError("backup content verification failed")
            content_digests[str(index)] = digest(content_identity(backup_stamp(target, directory / str(index))))
            for folder, _, files in os.walk(directory / str(index)):
                for name in files:
                    with open(Path(folder) / name, "rb") as stream:
                        os.fsync(stream.fileno())
                descriptor = os.open(folder, os.O_RDONLY)
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
            if (directory / str(index)).is_file():
                with open(directory / str(index), "rb") as stream:
                    os.fsync(stream.fileno())
        descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        backup["phase"] = "complete"
        backup["digests"] = content_digests
        save_manifest(wt, manifest_path, manifest)
    directory = safe_path(manifest_path.parent / backup["directory"], manifest_path.parent)
    if json.loads(safe_path(directory / "task.json", directory).read_text()) != snapshot:
        raise ValueError("backup task content changed")
    for index, target in enumerate(manifest["targets"]):
        if "path" in target:
            copied = content_identity(backup_stamp(target, directory / str(index)))
            if digest(copied) != backup["digests"].get(str(index)):
                raise ValueError("backup content changed")
            if Path(target["path"]).exists():
                revalidate_target(wt, target)
                if copied != content_identity(backup_stamp(target)):
                    raise ValueError("backup no longer matches source")


def revalidate_target(wt, target):
    if target["kind"] == "branch":
        tip = wt.git_out(target["repo"], "rev-parse", "--verify", "refs/heads/" + target["branch"])
        if not tip and target["phase"] in ("running", "done"):
            return False
        if tip != target["tip"] or target["phase"] == "done":
            raise ValueError("branch target changed")
        if any(entry.get("branch") == target["branch"] for entry in wt.list_worktrees(target["repo"])):
            raise ValueError("branch is still checked out")
        return True
    path = Path(target["path"])
    if not path.exists() and not path.is_symlink() and target["phase"] in ("running", "done"):
        return False
    if target["kind"] == "worktree":
        if wt.repo_of_path(str(path)) != target["repo"] or not any(
                entry["path"] == str(path) and entry.get("branch") == target["branch"]
                for entry in wt.list_worktrees(target["repo"])):
            raise ValueError("worktree registration changed")
        if checked_git(wt, path, "symbolic-ref", "--short", "HEAD") != target["branch"]:
            raise ValueError("worktree branch changed")
        if checked_git(wt, target["repo"], "rev-parse", "refs/heads/" + target["branch"]) != target["tip"]:
            raise ValueError("worktree tip changed")
    if target["phase"] == "done" or digest(backup_stamp(target)) != target["stamp"]:
        raise ValueError("filesystem target changed")
    return True


def execute_locked(wt, board, connection, control, manifest_path, manifest):
    board_id = manifest["board"]
    snapshot, rows = read_inventory(connection, board_id)
    if digest(snapshot) != manifest["task_digest"]:
        raise ValueError("canonical task changed since purge preview")
    expected = {(path, branch) for path, branch in wt.row_worktrees(
        snapshot["active"][0]["branch_worktree"], str(control))} if snapshot["active"] else set()
    expected |= {(path if os.path.isabs(path) else str(control / path), branch)
                 for _, path, branch in manifest["orphan"]}
    actual = {(target["path"], target["branch"]) for target in manifest["targets"]
              if target["kind"] == "worktree"}
    branches = {(target["repo"], target["branch"], target["tip"]) for target in manifest["targets"]
                if target["kind"] == "branch"}
    paired = {(target["repo"], target["branch"], target["tip"]) for target in manifest["targets"]
              if target["kind"] == "worktree"}
    if expected != actual or branches != paired:
        raise ValueError("manifest ownership does not match canonical task/evidence")
    inventoried_reports = {target["path"] for target in manifest["targets"] if target["kind"] == "file"}
    if any(target["path"] not in inventoried_reports for target in report_targets(control, board_id)):
        raise ValueError("new task report appeared after purge inventory")
    for target in manifest["targets"]:
        if target["kind"] in ("worktree", "branch"):
            for row in rows:
                if row["id"] != board_id and any(
                        path == target.get("path") or branch == target["branch"]
                        for path, branch in wt.row_worktrees(row["branch_worktree"], str(control))):
                    raise ValueError("another task now owns target")
        present = revalidate_target(wt, target)
        if target["phase"] == "done":
            continue
        if present:
            target["phase"] = "running"
            save_manifest(wt, manifest_path, manifest)
            if target["kind"] == "branch":
                checked_git(wt, target["repo"], "update-ref", "-d",
                            "refs/heads/" + target["branch"], target["tip"])
            elif target["kind"] == "worktree":
                checked_git(wt, target["repo"], "worktree", "remove", "--force", target["path"])
            elif Path(target["path"]).is_dir():
                shutil.rmtree(target["path"])
            else:
                os.unlink(target["path"])
        target["phase"] = "done"
        save_manifest(wt, manifest_path, manifest)
    board.reserve_plan_ids(connection)
    connection.execute("DELETE FROM planned_items WHERE id=?", (board_id,))
    board.persist_normalized_projection(connection)
    connection.commit()
    manifest["complete"] = True
    save_manifest(wt, manifest_path, manifest)


def command(args, cwd, wt):
    try:
        if not re.fullmatch(r"BOARD-\d+", args.board):
            raise ValueError("invalid task ID")
        board = wt.load_board_module(wt.script_root())
        state = board.runtime_state_module()
        control = Path(state.primary_checkout(wt.control_root(cwd)))
        database = safe_path(control / ".factory-state" / board.DATABASE_NAME, control)
        for suffix in ("-wal", "-shm", "-journal"):
            safe_path(str(database) + suffix, control)
        state.ensure_runtime_ready(str(control))
        safe_path(control / ".opencode" / "repos.json", control)
        repos, error = wt.load_repos(str(control))
        if error:
            raise ValueError(error)
        directory = safe_path(control / ".factory-state" / "purges" / args.board, control)
        manifest_path = safe_path(directory / "manifest.json", control)
        manifest = None
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            if (not isinstance(manifest, dict)
                    or manifest.get("format") != 1 or manifest.get("board") != args.board
                    or manifest.get("control") != str(control)
                    or manifest.get("orphan") != args.orphan):
                raise ValueError("purge manifest identity or orphan evidence changed")
        with board.readonly_connection(str(database)) as connection:
            board.require_normalized(connection)
            if manifest is None:
                snapshot, rows = read_inventory(connection, args.board)
                targets = targets_for_task(wt, control, rows, snapshot, args.orphan, repos)
                targets += report_targets(control, args.board)
                manifest = {"format": 1, "board": args.board, "control": str(control),
                            "task_digest": digest(snapshot), "orphan": args.orphan,
                             "repos_digest": digest(repos), "complete": False,
                            "backup": {"enabled": args.backup, "phase": "pending", "attempts": []},
                            "targets": [dict(target, phase="pending") for target in targets]}
            else:
                snapshot = None
            if manifest.get("repos_digest") != digest(repos):
                raise ValueError("repository registration changed")
        print(json.dumps(manifest, indent=2, sort_keys=True))
        print("Retained: Git objects/other refs (no history rewrite), historical/shared backups, generated exports and "
              "legacy copies. Cancelled orphan ownership is supplied by the human, not inferred.")
        print("Optional --backup retains private content in the purge recovery directory.")
        validate_manifest(wt, manifest, control, repos)
        backup = manifest.get("backup")
        if (not isinstance(backup, dict) or backup.get("enabled") != args.backup
                or backup.get("phase") not in ("pending", "copying", "complete")
                or not isinstance(backup.get("attempts"), list)
                or any(not re.fullmatch(r"content-[0-9a-f]{32}", name) for name in backup["attempts"])
                or (backup.get("phase") == "complete" and (
                    backup.get("directory") not in backup["attempts"]
                    or not isinstance(backup.get("digests"), dict)))):
            raise ValueError("backup policy or recovery metadata changed")
        if not args.apply:
            return wt.OK
        if Path(cwd) != control:
            raise ValueError("purge apply must run from the selected primary control checkout")
        confirm(args.board)
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        safe_path(directory, control)
        safe_path(directory / "lock", control)
        descriptor = os.open(directory / "lock", os.O_WRONLY | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(descriptor, "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            live_repos, error = wt.load_repos(str(control))
            if error or digest(live_repos) != manifest["repos_digest"]:
                raise ValueError("repository registration changed during confirmation")
            validate_manifest(wt, manifest, control, live_repos)
            if manifest_path.exists():
                if json.loads(manifest_path.read_text()) != manifest:
                    raise ValueError("purge manifest changed during confirmation")
            elif snapshot is None:
                raise ValueError("purge manifest disappeared")
            with board.connect(str(database)) as connection:
                connection.execute("BEGIN IMMEDIATE")
                if manifest["complete"]:
                    if connection.execute("SELECT 1 FROM planned_items WHERE id=?", (args.board,)).fetchone():
                        raise ValueError("completed purge task identity reappeared")
                    for target in manifest["targets"]:
                        if target["phase"] != "done" or revalidate_target(wt, target):
                            raise ValueError("completed purge target reappeared")
                    return wt.OK
                if not connection.execute("SELECT 1 FROM planned_items WHERE id=?", (args.board,)).fetchone():
                    if all(target["phase"] == "done" for target in manifest["targets"]):
                        for target in manifest["targets"]:
                            revalidate_target(wt, target)
                        manifest["complete"] = True
                        save_manifest(wt, manifest_path, manifest)
                        return wt.OK
                    raise ValueError("task missing before purge resources completed")
                current, rows = read_inventory(connection, args.board)
                if digest(current) != manifest["task_digest"]:
                    raise ValueError("task changed during confirmation")
                if not manifest_path.exists():
                    fresh = targets_for_task(wt, control, rows, current, args.orphan, repos)
                    fresh += report_targets(control, args.board)
                    if fresh != [{k: v for k, v in target.items() if k != "phase"}
                                 for target in manifest["targets"]]:
                        raise ValueError("targets changed during confirmation")
                    save_manifest(wt, manifest_path, manifest)
                prepare_backup(wt, state, manifest_path, manifest, current)
                execute_locked(wt, board, connection, control, manifest_path, manifest)
        print("Purged %s; durable operational metadata retained at %s" % (args.board, manifest_path))
        return wt.OK
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error, KeyboardInterrupt) as exc:
        print("refused: %s; retain recovery metadata and retry only after inspection" % exc, file=sys.stderr)
        return wt.REFUSED
