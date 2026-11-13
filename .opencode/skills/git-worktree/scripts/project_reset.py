"""Closed clean-slate inventory and human-confirmed, resumable effects."""
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import sys
import uuid

import task_purge as purge


DOCUMENTS = ("DOMAIN.md", "ROADMAP.md") + tuple(
    "docs/" + name + ".md" for name in (
        "BOARD", "API_CONTRACTS", "ARCHITECTURE", "BUSINESS-LOGIC", "DECISIONS",
        "ENVIRONMENT", "HANDOVER", "PROJECT_STATE", "PROJECT_STRUCTURE", "RISKS", "STACK", "UI-UX"))
BUNDLE = Path(__file__).parent.parent / "templates" / "project-v1"
RECOVERY = ("cleanup-wt", "purges", "clean-slates", ".migration-complete.json")
PRESERVED = ("application source", "harness and templates", "Git history, refs and worktrees",
             "secrets", "unrelated repositories", "README files", "CHANGELOG.md",
             "custom documents", "docs/handover/", "docs/changelog/", "historical recovery copies")


def repository_kind(domain, roadmap, factory_marker):
    if domain and roadmap and not factory_marker:
        return "project"
    if not domain and not roadmap and factory_marker:
        return "factory"
    raise ValueError("ambiguous factory/project governance identifiers")


def validate_rows(items, active, repo_ids):
    ids = [row[0] for row in items]
    if len(set(ids)) != len(ids) or any(not re.fullmatch(r"BOARD-\d+", value) for value in ids):
        raise ValueError("ambiguous canonical task identity")
    blockers = []
    for identity, repositories, dependencies in items:
        owners = {name.strip() for name in repositories.split(",")}
        if not owners or not owners.issubset(repo_ids):
            blockers.append("unknown repository ownership for " + identity)
        if set(re.findall(r"\bBOARD-\d+\b", dependencies)) - set(ids):
            blockers.append("unresolved dependency ownership for " + identity)
    if any(identity not in ids for identity, _ in active):
        raise ValueError("orphan active-work identity")
    if any(value not in (None, "", "-", "- None.") for _, value in active):
        blockers.append("active worktree references must be resolved separately")
    return blockers


def checked_content(path, root):
    path = purge.safe_path(path, root)
    info = path.lstat()
    if stat.S_ISREG(info.st_mode):
        if info.st_nlink != 1:
            raise ValueError("hard-linked target refused: " + str(path))
        if (path.name.startswith(".env") or path.name.startswith("credentials")
                or path.name.startswith("id_rsa") or path.name == ".npmrc"
                or path.suffix in (".pem", ".key", ".p12")):
            raise ValueError("secret-like target refused without reading: " + str(path))
    elif stat.S_ISDIR(info.st_mode):
        for child in sorted(path.iterdir()):
            if child.name == ".git":
                raise ValueError("nested repository refused: " + str(child))
            checked_content(child, root)
    else:
        raise ValueError("non-regular target refused: " + str(path))
    return path


def file_target(path, root, kind="delete"):
    purge.safe_path(path, root)
    if not path.is_file():
        raise ValueError("file target must be a regular file")
    checked_content(path, root)
    return {"kind": kind, "path": str(path), "stamp": purge.digest(purge.tree_stamp(path))}


def inode(path):
    value = Path(path).lstat()
    return [value.st_dev, value.st_ino, value.st_mode]


def database_image(connection):
    schema = connection.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name").fetchall()
    tables = {row[1] for row in schema if row[0] == "table"}
    if (tables - {"planned_items", "acceptance_criteria", "active_work", "board", "plan_id_sequence"}
            or any(row[0] in ("trigger", "view") for row in schema)):
        raise ValueError("unrecognized database tables or executable schema")
    return purge.digest({"schema": schema, "rows": {name: connection.execute(
        'SELECT * FROM "' + name + '" ORDER BY rowid').fetchall() for name in sorted(tables)}})


def template_inventory():
    checked_content(BUNDLE, BUNDLE.parent)
    manifest = json.loads((BUNDLE / "manifest.json").read_text())
    if (not isinstance(manifest, dict) or manifest.get("format") != "project-reset-v1"
            or not isinstance(manifest.get("files"), dict)
            or set(manifest["files"]) != set(DOCUMENTS)):
        raise ValueError("missing or unrecognized portable template manifest")
    actual = {str(path.relative_to(BUNDLE)) for path in BUNDLE.rglob("*") if path.is_file()}
    if actual != set(DOCUMENTS) | {"manifest.json"}:
        raise ValueError("unrecognized portable template entries")
    hashes = {}
    for relative in DOCUMENTS:
        value = hashlib.sha256((BUNDLE / relative).read_bytes()).hexdigest()
        if value != manifest["files"][relative]:
            raise ValueError("portable template hash mismatch: " + relative)
        hashes[relative] = value
    return hashes


def evidence_inventory(root, identities):
    blockers, paths = [], []
    artifacts = purge.safe_path(root / "artifacts", root)
    if artifacts.exists():
        if not artifacts.is_dir():
            raise ValueError("artifact root is not a directory")
        for scope in sorted(artifacts.iterdir()):
            purge.safe_path(scope, root)
            if scope.name not in ("web", "api", "mobile", "factory") or not scope.is_dir():
                blockers.append("unknown artifact ownership: " + str(scope))
                continue
            for category in sorted(scope.iterdir()):
                purge.safe_path(category, root)
                if category.name != "qa" or not category.is_dir():
                    blockers.append("unknown artifact ownership: " + str(category))
                    continue
                for day in sorted(category.iterdir()):
                    purge.safe_path(day, root)
                    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day.name) or not day.is_dir():
                        blockers.append("unknown artifact ownership: " + str(day))
                        continue
                    for task in sorted(day.iterdir()):
                        purge.safe_path(task, root)
                        if task.name not in identities or not task.is_dir():
                            blockers.append("unknown artifact ownership: " + str(task))
                        else:
                            checked_content(task, root)
    reviews = purge.safe_path(root / ".factory-state/reviews", root)
    if reviews.exists():
        if not reviews.is_dir():
            raise ValueError("review root is not a directory")
        for ledger in sorted(reviews.iterdir()):
            purge.safe_path(ledger, root)
            if ledger.name not in {identity + "-ledger.md" for identity in identities}:
                blockers.append("unknown ledger ownership: " + str(ledger))
            else:
                checked_content(ledger, root)
    for identity in sorted(identities):
        paths.extend(dict(target, kind="delete") for target in purge.report_targets(root, identity))
    return paths, blockers


def selection(args, cwd, wt):
    board = wt.load_board_module(wt.script_root())
    if board is None:
        raise ValueError("required board reader is unavailable")
    state = board.runtime_state_module()
    origin = Path(state.primary_checkout(str(cwd)))
    mapping = purge.safe_path(origin / wt.REPOS_REL, origin)
    checked_content(mapping, origin)
    repos, error = wt.load_repos(str(origin))
    if error:
        raise ValueError(error)
    if args.repo not in repos or ".." in Path(repos[args.repo]).parts:
        raise ValueError("unknown repository or traversal mapping")
    selected, error = wt.resolve_repo(str(origin), repos, args.repo)
    if error:
        raise ValueError(error)
    root = purge.safe_path(Path(selected), origin, allow_root=True)
    if (not wt.is_git_repo(str(root)) or Path(state.primary_checkout(str(root))) != root):
        raise ValueError("selected root is not an independent primary checkout")
    local_map = purge.safe_path(root / wt.REPOS_REL, root)
    checked_content(local_map, root)
    local_repos, error = wt.load_repos(str(root))
    if error or local_repos.get("control") != ".":
        raise ValueError("app-only/shared-board scope refused: standalone control map required")
    return board, state, root, local_map, local_repos


def preview(args, cwd, wt):
    board, state, root, local_map, local_repos = selection(args, cwd, wt)
    for relative in ("DOMAIN.md", "ROADMAP.md", "templates/project/AGENTS.md"):
        purge.safe_path(root / relative, root)
    kind = repository_kind((root / "DOMAIN.md").exists(), (root / "ROADMAP.md").exists(),
                           (root / "templates/project/AGENTS.md").is_file())
    templates = template_inventory()
    blockers = []
    worktrees = wt.list_worktrees(str(root))
    if len(worktrees) != 1 or Path(worktrees[0]["path"]) != root:
        blockers.append("linked or unresolved worktrees must be resolved separately")
    runtime = purge.safe_path(root / ".factory-state", root)
    targets, retained = [], []
    identities = set()
    high_water = None
    if runtime.exists():
        if not runtime.is_dir():
            raise ValueError("runtime root is not a directory")
        known = {board.DATABASE_NAME, *state.BOARD_FILES, "reviews", *RECOVERY}
        for entry in sorted(runtime.iterdir()):
            purge.safe_path(entry, root)
            if entry.name in RECOVERY or entry.name.endswith((".bak", ".backup")):
                retained.append(str(entry))
            elif entry.name not in known:
                blockers.append("unknown or active runtime state: " + str(entry))
        database = purge.safe_path(runtime / board.DATABASE_NAME, root)
        if database.exists():
            target = file_target(database, root, "empty-board-preserve-high-water")
            target["inode"] = inode(database)
            target["clear"] = ["planned_items", "acceptance_criteria", "active_work", "board projection"]
            sidecars = [Path(str(database) + suffix) for suffix in ("-wal", "-shm", "-journal")]
            if any(path.exists() or path.is_symlink() for path in sidecars):
                for path in sidecars:
                    purge.safe_path(path, root)
                blockers.append("stop SQLite writers and resolve sidecars before inventory")
            else:
                with board.readonly_connection(str(database)) as connection:
                    board.require_normalized(connection)
                    items = connection.execute("SELECT id, repos, blocked_by FROM planned_items ORDER BY id").fetchall()
                    active = connection.execute("SELECT plan_item_id, branch_worktree FROM active_work ORDER BY plan_item_id").fetchall()
                    blockers.extend(validate_rows(items, active, set(local_repos)))
                    identities = {row[0] for row in items}
                    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                    if tables - {"planned_items", "acceptance_criteria", "active_work", "board", "plan_id_sequence"}:
                        raise ValueError("unrecognized database tables; reset scope is ambiguous")
                    if connection.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                        raise ValueError("canonical database integrity check failed")
                    if connection.execute("PRAGMA foreign_key_check").fetchall():
                        raise ValueError("orphan canonical database references")
                    sequence = connection.execute("SELECT high_water FROM plan_id_sequence WHERE singleton=1").fetchone() if "plan_id_sequence" in tables else None
                    if sequence is not None and (type(sequence[0]) is not int or sequence[0] < 0):
                        raise ValueError("invalid monotonic ID high-water")
                    high_water = max([int(value.split("-")[1]) for value in identities] + [sequence[0] if sequence else 0])
                    target["logical_digest"] = database_image(connection)
                if target["stamp"] != purge.digest(purge.tree_stamp(database)):
                    raise ValueError("database changed during inventory")
            targets.append(target)
        else:
            blockers.append("canonical database missing; preview never initializes it")
        for name in state.BOARD_FILES:
            path = purge.safe_path(runtime / name, root)
            if path.exists():
                if name == "factory-board-legacy-backup.md":
                    retained.append(str(path))
                else:
                    targets.append(file_target(path, root))
    else:
        blockers.append("runtime state missing; preview never creates it")
    evidence, unknown = evidence_inventory(root, identities)
    targets.extend(evidence)
    blockers.extend(unknown)
    if kind == "project":
        for relative in DOCUMENTS:
            path = purge.safe_path(root / relative, root)
            if not path.parent.is_dir():
                blockers.append("document parent directory missing: " + str(path.parent))
            target = file_target(path, root, "replace-document") if path.exists() else {
                "kind": "replace-document", "path": str(path), "stamp": None}
            if path.exists() and not path.is_file():
                raise ValueError("document target must be a regular file")
            targets.append(dict(target, template=relative, replacement_sha256=templates[relative]))
    else:
        retained.append(str(root / "docs"))
    for name in (*state.BOARD_FILES, state.BOARD_DATABASE, "reviews", "cleanup-wt"):
        path = purge.safe_path(root / ".git" / name, root)
        if path.exists():
            retained.append(str(path))
    return {"format": "project-reset-preview-v1", "repo": args.repo, "root": str(root),
            "root_inode": inode(root), "git_inode": inode(root / ".git"),
            "map_stamp": file_target(local_map, root)["stamp"],
            "identities": sorted(identities), "templates": templates,
            "repository_kind": kind, "backup_requested": args.backup,
            "template_version": "project-reset-v1", "targets": targets,
            "high_water_to_preserve": high_water, "preserved": list(PRESERVED),
            "retained_paths": retained, "blockers": blockers,
            "future_metadata": str(runtime / "clean-slates/<operation-id>/manifest.json"),
            "warning": "Project document reset leaves preserved application source undocumented."}


def require_terminal():
    if not sys.stdin.isatty() or not sys.stderr.isatty():
        raise ValueError("clean-slate requires a real interactive terminal; agents may preview only")


def confirm(repo, root):
    require_terminal()
    expected = repo + " " + str(root)
    sys.stderr.write("Human-only clean-slate; local deterrent, not an OS security boundary.\n"
                     "Type the exact repository ID and canonical path: " + expected + "\n> ")
    sys.stderr.flush()
    if sys.stdin.readline() != expected + "\n":
        raise ValueError("confirmation did not match exact repository ID and canonical path")


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def replacement_image(path, root):
    checked_content(path, root)
    stamp = purge.tree_stamp(path)
    return [stamp[0][:5], stamp[1]]


def expand_steps(plan):
    root = Path(plan["root"])
    steps = []
    for target in plan["targets"]:
        if target["kind"] == "empty-board-preserve-high-water":
            continue
        path = Path(target["path"])
        if target["kind"] == "replace-document":
            steps.append(dict(target, phase="pending"))
        else:
            checked_content(path, root)
            children = sorted(path.rglob("*"), key=lambda item: (-len(item.parts), str(item))) if path.is_dir() else []
            for node in children + [path]:
                steps.append({"kind": "rmdir" if node.is_dir() else "delete", "path": str(node),
                              "pre": inode(node) if node.is_dir() else file_target(node, root)["stamp"],
                              "phase": "pending"})
    return steps


def validate_record(record, root, repo, templates, database):
    plan = record["plan"]
    if (record.get("format") != "project-reset-operation-v1" or record.get("plan_digest") != purge.digest(plan)
            or plan["root"] != str(root) or plan["repo"] != repo
            or plan["root_inode"] != inode(root) or plan["git_inode"] != inode(root / ".git")
            or plan["templates"] != templates or plan["blockers"]
            or type(record.get("complete")) is not bool):
        raise ValueError("reset manifest identity or approved plan changed")
    roots, documents, db = set(), set(), []
    ids = plan["identities"]
    if any(not re.fullmatch(r"BOARD-\d+", value) for value in ids):
        raise ValueError("invalid recorded task ownership")
    for target in plan["targets"]:
        path = purge.safe_path(target["path"], root)
        relative = path.relative_to(root)
        if target["kind"] == "empty-board-preserve-high-water" and path == database:
            db.append(target)
        elif (target["kind"] == "replace-document" and plan["repository_kind"] == "project"
              and str(relative) in DOCUMENTS and target["template"] == str(relative)
              and target["replacement_sha256"] == templates[str(relative)]):
            documents.add(str(path))
        elif target["kind"] == "delete":
            parts = relative.parts
            artifact = (len(parts) == 5 and parts[0] == "artifacts" and parts[1] in ("web", "api", "mobile", "factory")
                        and parts[2] == "qa" and re.fullmatch(r"\d{4}-\d{2}-\d{2}", parts[3]) and parts[4] in ids)
            ledger = parts[:2] == (".factory-state", "reviews") and len(parts) == 3 and parts[2] in {
                identity + "-ledger.md" for identity in ids}
            if not artifact and not ledger and parts != (".factory-state", "factory-board-export.md"):
                raise ValueError("reset manifest delete authority refused")
            roots.add(path)
        else:
            raise ValueError("reset manifest target vocabulary refused")
    if len(db) != 1 or (plan["repository_kind"] == "project" and documents != {str(root / name) for name in DOCUMENTS}):
        raise ValueError("incomplete closed reset inventory")
    seen = set()
    for index, step in enumerate(record["steps"]):
        path = purge.safe_path(step["path"], root)
        if step["path"] in seen or step["phase"] not in ("pending", "running", "done"):
            raise ValueError("invalid reset step phase or duplicate")
        seen.add(step["path"])
        if step["kind"] == "replace-document":
            if (step["path"] not in documents or step["template"] != str(path.relative_to(root))
                    or step["replacement_sha256"] != templates[step["template"]]):
                raise ValueError("unapproved document step")
            attempts = step.get("replacement_attempts", [])
            if (not isinstance(attempts, list) or len(set(attempts)) != len(attempts)
                    or any(not isinstance(attempt, str) or not re.fullmatch(
                        "replacement-" + str(index) + r"-[a-f0-9]{32}", attempt) for attempt in attempts)):
                raise ValueError("invalid replacement preparation attempts")
        elif step["kind"] not in ("delete", "rmdir") or not any(path == parent or parent in path.parents for parent in roots):
            raise ValueError("unapproved delete step")
    if not ({str(path) for path in roots} | documents) <= seen:
        raise ValueError("reset manifest omitted targets")
    return db[0]


def validate_files(record, root):
    steps = record["steps"]
    for step in steps:
        path = purge.safe_path(step["path"], root)
        present = path.exists()
        if present:
            checked_content(path, root)
        if step["kind"] == "replace-document":
            if step["phase"] in ("running", "done") and present and replacement_image(path, root) == step.get("post"):
                if step["phase"] == "done" and file_target(path, root)["stamp"] != step["done_stamp"]:
                    raise ValueError("completed document changed")
                continue
            if step["phase"] == "done" or (file_target(path, root)["stamp"] if present else None) != step["stamp"]:
                raise ValueError("document pre/postimage changed")
        elif not present:
            if step["phase"] == "pending":
                raise ValueError("pending delete target disappeared")
        elif step["phase"] == "done":
            raise ValueError("completed delete target reappeared")
        elif step["kind"] == "rmdir":
            allowed = {Path(item["path"]).name for item in steps if Path(item["path"]).parent == path and item["phase"] != "done"}
            if inode(path) != step["pre"] or {child.name for child in path.iterdir()} - allowed:
                raise ValueError("directory identity or ownership changed")
        elif file_target(path, root)["stamp"] != step["pre"]:
            raise ValueError("delete target changed")
    evidence, blockers = evidence_inventory(root, set(record["plan"]["identities"]))
    original = {target["path"] for target in record["plan"]["targets"] if target["kind"] == "delete"}
    if blockers or any(target["path"] not in original for target in evidence):
        raise ValueError("new or unowned evidence appeared")
    export = root / ".factory-state" / "factory-board-export.md"
    if (export.exists() or export.is_symlink()) and str(export) not in original:
        raise ValueError("new generated board export appeared")


def empty_database(connection, board, high_water):
    if board.reserve_plan_ids(connection) != high_water:
        raise ValueError("monotonic ID high-water changed")
    for table in ("acceptance_criteria", "active_work", "planned_items"):
        connection.execute("DELETE FROM " + table)
    row = connection.execute("SELECT revision FROM board WHERE id=1").fetchone()
    if row is None or connection.execute("SELECT count(*) FROM board").fetchone()[0] != 1:
        raise ValueError("unsupported board projection identity")
    connection.execute("UPDATE board SET markdown=?, revision=? WHERE id=1", (board.empty_board(), row[0] + 1))


def backup_record(record, operation, manifest, wt, state, board):
    if not record["plan"]["backup_requested"]:
        return
    if not record.get("backup_complete"):
        attempt = "content-" + uuid.uuid4().hex
        record.setdefault("backup_attempts", []).append(attempt)
        purge.save_manifest(wt, manifest, record)
        destination = operation / attempt
        destination.mkdir(mode=0o700)
        sync_directory(operation)
        copies = []
        for index, target in enumerate(record["plan"]["targets"]):
            if target["stamp"] is None:
                continue
            source = Path(target["path"])
            copy = destination / str(index)
            if target["kind"] == "empty-board-preserve-high-water":
                state._backup_database(str(source), str(copy), source.stat().st_mode & 0o777)
                os.chmod(copy, 0o600)
                with board.readonly_connection(str(copy)) as reader:
                    if database_image(reader) != target["logical_digest"]:
                        raise ValueError("SQLite backup logical verification failed")
            else:
                checked_content(source, Path(record["plan"]["root"]))
                if purge.digest(purge.tree_stamp(source)) != target["stamp"]:
                    raise ValueError("backup source changed")
                purge.copy_backup(source, copy, state)
                if purge.content_identity(purge.tree_stamp(source)) != purge.content_identity(purge.tree_stamp(copy)):
                    raise ValueError("backup content verification failed")
            checked_content(copy, operation)
            copies.append({"path": str(copy.relative_to(operation)),
                           "digest": purge.digest(purge.content_identity(purge.tree_stamp(copy)))})
        for directory in sorted((path for path in destination.rglob("*") if path.is_dir()),
                                key=lambda path: -len(path.parts)) + [destination]:
            sync_directory(directory)
        record["backup_copies"] = copies
        record["backup_complete"] = True
        purge.save_manifest(wt, manifest, record)
    for copy in record["backup_copies"]:
        parts = Path(copy["path"]).parts
        if len(parts) != 2 or not re.fullmatch(r"content-[a-f0-9]{32}", parts[0]) or not parts[1].isdigit():
            raise ValueError("invalid backup manifest path")
        path = purge.safe_path(operation / copy["path"], operation)
        checked_content(path, operation)
        if purge.digest(purge.content_identity(purge.tree_stamp(path))) != copy["digest"]:
            raise ValueError("retained backup changed")


def execute_step(step, index, record, operation, manifest, wt, root):
    path = Path(step["path"])
    if step["phase"] == "done":
        return
    if step["kind"] == "replace-document":
        if step["phase"] == "running" and path.exists() and replacement_image(path, root) == step["post"]:
            pass
        else:
            source = BUNDLE / step["template"]
            content = source.read_bytes()
            if hashlib.sha256(content).hexdigest() != step["replacement_sha256"]:
                raise ValueError("replacement template changed")
            if step["phase"] == "pending":
                attempt = "replacement-" + str(index) + "-" + uuid.uuid4().hex
                step.setdefault("replacement_attempts", []).append(attempt)
                purge.save_manifest(wt, manifest, record)
                staged = purge.safe_path(operation / attempt, operation)
                descriptor = os.open(staged, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(content)
                    stream.flush()
                    os.fsync(stream.fileno())
                sync_directory(operation)
            else:
                attempts = step.get("replacement_attempts", [])
                staged = purge.safe_path(operation / (attempts[-1] if attempts else "replacement-" + str(index)), operation)
            checked_content(staged, root)
            post = replacement_image(staged, root)
            if post[1] != step["replacement_sha256"] or (step.get("post") is not None and step["post"] != post):
                raise ValueError("staged replacement changed")
            step["post"], step["phase"] = post, "running"
            purge.save_manifest(wt, manifest, record)
            validate_files(record, root)
            os.replace(staged, path)
            sync_directory(path.parent)
            sync_directory(operation)
        step["done_stamp"] = file_target(path, root)["stamp"]
    else:
        step["phase"] = "running"
        purge.save_manifest(wt, manifest, record)
        validate_files(record, root)
        if path.exists():
            if step["kind"] == "rmdir":
                path.rmdir()
            else:
                path.unlink()
            sync_directory(path.parent)
    step["phase"] = "done"
    purge.save_manifest(wt, manifest, record)


def apply_locked(record, operation, manifest, root, wt, board, state, connection):
    database = root / ".factory-state" / "factory-board.sqlite3"
    target = validate_record(record, root, record["plan"]["repo"], template_inventory(), database)
    if file_target(root / ".opencode" / "repos.json", root)["stamp"] != record["plan"]["map_stamp"]:
        raise ValueError("repository registration changed")
    if (root / ".git" / "worktrees").exists() and any((root / ".git" / "worktrees").iterdir()):
        raise ValueError("linked worktrees exist; clean-slate refused")
    checked_content(database, root)
    if inode(database) != target["inode"]:
        raise ValueError("database identity changed")
    image = database_image(connection)
    if image not in (target["logical_digest"], record.get("database_post")):
        raise ValueError("database pre/postimage changed")
    validate_files(record, root)
    if record["complete"]:
        if image != record["database_post"] or any(step["phase"] != "done" for step in record["steps"]):
            raise ValueError("completed reset diverged")
        backup_record(record, operation, manifest, wt, state, board)
        connection.execute("ROLLBACK")
        return
    if image == target["logical_digest"] and not record.get("database_post"):
        connection.execute("SAVEPOINT reset_postimage")
        empty_database(connection, board, record["plan"]["high_water_to_preserve"])
        record["database_post"] = database_image(connection)
        connection.execute("ROLLBACK TO reset_postimage")
        connection.execute("RELEASE reset_postimage")
        purge.save_manifest(wt, manifest, record)
    if image == record["database_post"] and any(step["phase"] != "done" for step in record["steps"]):
        raise ValueError("database committed before filesystem steps completed")
    backup_record(record, operation, manifest, wt, state, board)
    validate_files(record, root)
    for index, step in enumerate(record["steps"]):
        execute_step(step, index, record, operation, manifest, wt, root)
    validate_files(record, root)
    if image == target["logical_digest"]:
        empty_database(connection, board, record["plan"]["high_water_to_preserve"])
        if database_image(connection) != record["database_post"]:
            raise ValueError("database postimage mismatch")
    record["database_phase"] = "committing"
    purge.save_manifest(wt, manifest, record)
    connection.execute("COMMIT")
    record["database_phase"], record["complete"] = "committed", True
    purge.save_manifest(wt, manifest, record)


def command(args, cwd, wt):
    try:
        if args.apply:
            require_terminal()
        if getattr(args, "resume", None) and not args.apply:
            raise ValueError("--resume requires --apply and fresh named confirmation")
        if not args.apply:
            print(json.dumps(preview(args, cwd, wt), indent=2, sort_keys=True))
            return wt.OK
        board, state, root, _, _ = selection(args, cwd, wt)
        if Path(cwd).resolve() != root:
            raise ValueError("apply must run in the selected independent primary checkout")
        recovery = purge.safe_path(root / ".factory-state" / "clean-slates", root)
        resume = getattr(args, "resume", None)
        if resume:
            if not re.fullmatch(r"[a-f0-9]{32}", resume):
                raise ValueError("invalid explicit operation ID")
            operation = purge.safe_path(recovery / resume, root)
            manifest = purge.safe_path(operation / "manifest.json", root)
            checked_content(manifest, root)
            record = json.loads(manifest.read_text())
            if args.backup != record["plan"]["backup_requested"]:
                raise ValueError("resume must preserve the original --backup choice")
            validate_record(record, root, args.repo, template_inventory(), root / ".factory-state" / "factory-board.sqlite3")
        else:
            plan = preview(args, cwd, wt)
            print(json.dumps(plan, indent=2, sort_keys=True))
            if plan["blockers"]:
                raise ValueError("clean-slate preview has blockers")
            if recovery.exists():
                for directory in recovery.iterdir():
                    purge.safe_path(directory, root)
                    if not directory.is_dir() or not re.fullmatch(r"[a-f0-9]{32}", directory.name):
                        raise ValueError("unrecognized reset recovery entry")
                    existing = directory / "manifest.json"
                    checked_content(existing, root)
                    if json.loads(existing.read_text()).get("complete") is not True:
                        raise ValueError("unfinished reset requires explicit --resume " + directory.name)
            record = {"format": "project-reset-operation-v1", "plan": plan, "plan_digest": purge.digest(plan),
                      "steps": expand_steps(plan), "complete": False, "database_phase": "pending"}
            operation = recovery / uuid.uuid4().hex
            manifest = operation / "manifest.json"
        confirm(args.repo, root)
        if resume:
            checked_content(manifest, root)
            if json.loads(manifest.read_text()) != record:
                raise ValueError("reset manifest changed after confirmation")
        if not resume and preview(args, cwd, wt) != record["plan"]:
            raise ValueError("reset targets changed after confirmation")
        if not resume:
            recovery.mkdir(mode=0o700, exist_ok=True)
            sync_directory(recovery.parent)
            operation.mkdir(mode=0o700)
            sync_directory(recovery)
            purge.save_manifest(wt, manifest, record)
        print("Recovery manifest: " + str(manifest), file=sys.stderr)
        database = root / ".factory-state" / "factory-board.sqlite3"
        checked_content(database, root)
        if not database.is_file():
            raise ValueError("existing canonical database required")
        with board.connect(database) as connection:
            connection.execute("BEGIN IMMEDIATE")
            apply_locked(record, operation, manifest, root, wt, board, state, connection)
        print("Clean slate complete; retained recovery manifest: " + str(manifest))
        return wt.OK
    except (OSError, ValueError, KeyError, TypeError, AttributeError, sqlite3.Error) as exc:
        print("refused: %s" % exc, file=sys.stderr)
        return wt.REFUSED
