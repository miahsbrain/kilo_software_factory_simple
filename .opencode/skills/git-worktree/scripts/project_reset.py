"""Closed read-only clean-slate inventory; execution is intentionally unavailable."""
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import stat
import sys

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


def preview(args, cwd, wt):
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
    for relative in ("DOMAIN.md", "ROADMAP.md", "templates/project/AGENTS.md"):
        purge.safe_path(root / relative, root)
    kind = repository_kind((root / "DOMAIN.md").exists(), (root / "ROADMAP.md").exists(),
                           (root / "templates/project/AGENTS.md").is_file())
    templates = template_inventory()
    blockers = ["apply is not implemented in BOARD-153 chunk 1"]
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
                    target["logical_digest"] = purge.digest({name: connection.execute(
                        'SELECT * FROM "' + name + '" ORDER BY rowid').fetchall() for name in sorted(tables)})
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
            "repository_kind": kind, "backup_requested": args.backup,
            "template_version": "project-reset-v1", "targets": targets,
            "high_water_to_preserve": high_water, "preserved": list(PRESERVED),
            "retained_paths": retained, "blockers": blockers,
            "future_metadata": str(runtime / "clean-slates/<operation-id>/manifest.json"),
            "warning": "Project document reset leaves preserved application source undocumented."}


def command(args, cwd, wt):
    if args.apply:
        print("refused: clean-slate apply is not implemented; preview-only chunk 1", file=sys.stderr)
        return wt.REFUSED
    try:
        print(json.dumps(preview(args, cwd, wt), indent=2, sort_keys=True))
        return wt.OK
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as exc:
        print("refused: %s" % exc, file=sys.stderr)
        return wt.REFUSED
