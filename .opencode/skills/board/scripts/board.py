#!/usr/bin/env python3
"""Manipulate the SQLite-backed board, with Markdown import/export.

    board.py show [ID]
    board.py add --id BOARD-00X --task "..." --type Feature --status Backlog
                 --priority P1 --risk "🟢 low — one line" [--blocked-by "..."]
                 [--repos "api,control"] [--branch-worktree "..."] [--note "..."]
                 [--fingerprint "kind|category|route|subject"]
    board.py add-column --name Repos [--after "Blocked by"]
    board.py note <ID> --value "..." [--escalate]
    board.py set-status <ID> "<new status>"
    board.py set-field <ID> --field risk|priority|blocked-by|repos|branch-worktree|notes --value "..."
    board.py remove <ID>
    board.py lanes

The columns are ID | Task | Type | Status | Priority | Risk | Blocked by |
Repos | Branch/Worktree | Notes. `Repos` holds the repo ids from
.opencode/repos.json that the row touches, comma separated. `add-column` inserts a
column into an existing table without a hand edit; it is the only way the table
changes shape.

The SQLite database lives in the primary checkout's `.factory-state`, shared across worktrees.
On first initialization it imports the main checkout's legacy Markdown once.
The existing table parser and cell API remain available for lifecycle callers.
Writes merge disjoint cell edits under a SQLite transaction and refuse conflicts.
`export` publishes a Markdown snapshot outside tracked paths on demand.

A Fix row may carry a fingerprint — kind|category|route|subject — so the same
complaint about the same thing is recognised when it is filed again. A row with
a fingerprint that is already open is refused; the repeat is appended to the
existing row with `board.py note`.

Exit codes: 0 ok, 1 refusal, 2 usage error, 66 invalid input.
"""
import argparse
import contextlib
import importlib.util
import json
import os
import re
import sqlite3
import stat
import subprocess
import sys
import tempfile
import threading

BOARD_PATH = os.path.join("docs", "BOARD.md")
DATABASE_NAME = "factory-board.sqlite3"
EXPORT_NAME = "factory-board-export.md"
LEGACY_BACKUP_NAME = "factory-board-legacy-backup.md"
_snapshots = threading.local()
TYPES = ["Feature", "Fix", "Chore", "Docs", "Research"]
STATUSES = ["Backlog", "Ready", "In Progress", "In Review", "Pending Merge",
            "Merged", "Blocked", "Dropped"]
PRIORITIES = ["P1", "P2", "P3", "P4"]
FIELDS = {"risk": 5, "priority": 4, "blocked-by": 6, "repos": 7, "branch-worktree": 8, "notes": 9}
COLUMNS = ["ID", "Task", "Type", "Status", "Priority", "Risk", "Blocked by",
           "Repos", "Branch/Worktree", "Notes"]
COLUMN_FOR_FIELD = {"risk": "Risk", "priority": "Priority", "blocked-by": "Blocked by",
                    "repos": "Repos", "branch-worktree": "Branch/Worktree", "notes": "Notes"}
OPEN_STATUSES = ("Backlog", "Ready", "In Progress", "In Review", "Pending Merge", "Blocked")
FINGERPRINT_PREFIX = "fp="
NORMALIZED_TABLES = ("planned_items", "acceptance_criteria", "active_work")

OK = 0
REFUSED = 1
USAGE = 2
INVALID = 66


def control_root(cwd):
    path = os.path.join(os.path.dirname(__file__), "..", "..", "git-worktree", "scripts", "worktree.py")
    spec = importlib.util.spec_from_file_location("board_worktree", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.control_root(cwd)


def board_path(explicit):
    return explicit or os.path.join(control_root(os.getcwd()), BOARD_PATH)


def empty_board() -> str:
    return ("# BOARD\n\n"
            "Generated view of local SQLite state. Edit rows through board.py.\n\n"
            "| " + " | ".join(COLUMNS) + " |\n"
            "|" + "|".join("---" for _ in COLUMNS) + "|\n")


def initialize_board(root: str) -> str:
    """Import the main checkout's legacy board once without modifying its bytes."""
    path = os.path.join(root, BOARD_PATH)
    with connect(database_path(root)) as connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("CREATE TABLE IF NOT EXISTS board (id INTEGER PRIMARY KEY CHECK (id = 1), "
                           "markdown TEXT NOT NULL, source_bytes BLOB, revision INTEGER NOT NULL)")
        if connection.execute("SELECT id FROM board WHERE id = 1").fetchone() is None:
            source = None
            try:
                info = os.lstat(path)
            except FileNotFoundError:
                pass
            else:
                if not stat.S_ISREG(info.st_mode):
                    raise OSError("refusing non-regular board: %s" % path)
                with open(path, "rb") as stream:
                    source = stream.read()
            content = source.decode("utf-8") if source is not None else empty_board()
            parsed, error = parse_table(content, path)
            if parsed is None:
                raise ValueError(error)
            connection.execute("INSERT INTO board VALUES (1, ?, ?, 0)", (content, source))
    return path


def cmd_pre_merge_check(root):
    """Verify the legacy import and retain its exact bytes before the human merge."""
    source_path = os.path.join(root, BOARD_PATH)
    try:
        info = os.lstat(source_path)
        if not stat.S_ISREG(info.st_mode):
            raise OSError("refusing non-regular legacy board: %s" % source_path)
        with open(source_path, "rb") as stream:
            source = stream.read()
        parsed, error = parse_table(source.decode("utf-8"), source_path)
        if parsed is None:
            raise ValueError(error)
        db = database_path(root)
        initialize_board(root)
        with connect(db) as connection:
            row = connection.execute("SELECT source_bytes, markdown FROM board WHERE id = 1").fetchone()
        if row is None or row[0] is None or row[0] != source:
            raise ValueError("legacy board differs from its SQLite import (or was never imported); "
                             "stop board writers and reconcile before merging")
        backup = os.path.join(os.path.dirname(db), LEGACY_BACKUP_NAME)
        export = os.path.join(os.path.dirname(db), EXPORT_NAME)
        write_export(backup, source)
        with open(backup, "rb") as stream:
            if stream.read() != source:
                raise OSError("legacy byte backup verification failed: %s" % backup)
        write_export(export, row[1])
    except (OSError, UnicodeError, ValueError, sqlite3.Error) as exc:
        print("pre-merge check refused: %s" % exc, file=sys.stderr)
        return REFUSED
    print("legacy import verified: %s" % source_path)
    print("SQLite board: %s" % db)
    print("byte-exact legacy backup: %s" % backup)
    print("current board export: %s" % export)
    return OK


def database_path(root):
    runtime_state = runtime_state_module()
    runtime_state.ensure_runtime_ready(root)
    return os.path.join(runtime_state.state_root(root), DATABASE_NAME)


def runtime_state_module():
    state_file = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                              "../../runtime-state/scripts/state.py"))
    spec = importlib.util.spec_from_file_location("factory_runtime_state", state_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def connect(path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    connection = sqlite3.connect(path, timeout=10, isolation_level=None)
    try:
        connection.execute("PRAGMA busy_timeout=10000")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        yield connection
        if connection.in_transaction:
            connection.commit()
    except BaseException:
        if connection.in_transaction:
            connection.rollback()
        raise
    finally:
        connection.close()


def normalized_schema(connection):
    statements = ("""CREATE TABLE IF NOT EXISTS planned_items (
            id TEXT PRIMARY KEY,
            task TEXT NOT NULL,
            type TEXT NOT NULL,
            priority TEXT NOT NULL,
            risk TEXT NOT NULL,
            blocked_by TEXT NOT NULL,
            repos TEXT NOT NULL,
            notes TEXT NOT NULL,
            user_story TEXT,
            queue_position INTEGER UNIQUE,
            terminal_outcome TEXT CHECK (terminal_outcome IN ('completed', 'cancelled')),
            display_position INTEGER NOT NULL UNIQUE
        )""", """CREATE TABLE IF NOT EXISTS acceptance_criteria (
            plan_item_id TEXT NOT NULL REFERENCES planned_items(id) ON DELETE CASCADE,
            position INTEGER NOT NULL,
            text TEXT NOT NULL,
            verified INTEGER NOT NULL DEFAULT 0 CHECK (verified IN (0, 1)),
            proof TEXT,
            PRIMARY KEY (plan_item_id, position)
        )""", """CREATE TABLE IF NOT EXISTS active_work (
            plan_item_id TEXT PRIMARY KEY REFERENCES planned_items(id) ON DELETE CASCADE,
            status TEXT NOT NULL CHECK (status IN ('Ready', 'In Progress', 'In Review', 'Pending Merge', 'Blocked')),
            branch_worktree TEXT
        )""")
    for statement in statements:
        connection.execute(statement)


def normalized_enabled(connection):
    tables = {row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    return all(name in tables for name in NORMALIZED_TABLES)


def normalized_markdown(connection, markdown, active_only=False):
    parsed, error = parse_table(markdown)
    if parsed is None:
        raise ValueError(error)
    headers = [cell.strip() for cell in header_cells(parsed)]
    active_filter = "WHERE a.plan_item_id IS NOT NULL" if active_only else ""
    rows = connection.execute("""SELECT p.id, p.task, p.type, p.priority, p.risk,
        p.blocked_by, p.repos, p.notes, p.display_position, p.queue_position,
        p.terminal_outcome, a.status, a.branch_worktree
        FROM planned_items p LEFT JOIN active_work a ON a.plan_item_id=p.id
        %s ORDER BY p.display_position""" % active_filter).fetchall()
    table_rows = []
    for row in rows:
        (board_id, task, item_type, priority, risk, blocked_by, repos, notes, _display,
         queue_position, terminal, active_status, branch) = row
        status = active_status or ("Backlog" if queue_position is not None else
                                   "Merged" if terminal == "completed" else
                                   "Dropped" if terminal == "cancelled" else None)
        if status is None:
            raise ValueError("planned item %s has no lifecycle reference" % board_id)
        fields = {"ID": board_id, "Task": task, "Type": item_type, "Status": status,
                  "Priority": priority, "Risk": risk, "Blocked by": blocked_by,
                  "Repos": repos, "Branch/Worktree": branch or "-", "Notes": notes}
        table_rows.append("| " + " | ".join(fields.get(header, "-").replace("|", "\\|")
                                             for header in headers) + " |")
    lines = list(parsed["lines"][:parsed["header"] + 2])
    lines.extend(table_rows)
    lines.extend(parsed["lines"][parsed["rows"][-1] + 1:] if parsed["rows"] else
                 parsed["lines"][parsed["header"] + 2:])
    return "\n".join(lines)


def sync_normalized(connection, markdown, allow_completion=False):
    parsed, error = parse_table(markdown)
    if parsed is None:
        raise ValueError(error)
    headers = [cell.strip() for cell in header_cells(parsed)]
    existing = {row[0]: row[1:] for row in connection.execute("""SELECT p.id, p.queue_position,
        p.terminal_outcome, p.display_position, a.status, a.branch_worktree
        FROM planned_items p LEFT JOIN active_work a ON a.plan_item_id=p.id""")}
    seen = set()
    for line_index in parsed["rows"]:
        values = dict(zip(headers, cell_texts(parsed["lines"], line_index)))
        board_id = values.get("ID", "")
        if not board_id or board_id in seen:
            raise ValueError("duplicate or empty board ID")
        seen.add(board_id)
        status = values.get("Status", "")
        if board_id not in existing:
            raise ValueError("new planned items must be created with 'board.py plan accept'")
        queue, terminal, _item_display, active_status, _active_branch = existing[board_id]
        if queue is not None:
            if status != "Backlog":
                raise ValueError("queued items require 'board.py plan promote' to become active")
        elif active_status is not None:
            if status == "Merged" and allow_completion:
                connection.execute("DELETE FROM active_work WHERE plan_item_id=?", (board_id,))
                connection.execute("UPDATE planned_items SET queue_position=NULL, "
                                   "terminal_outcome='completed' WHERE id=?", (board_id,))
            elif status not in OPEN_STATUSES[1:]:
                raise ValueError("active items require plan lifecycle commands for terminal transitions")
            else:
                branch = values.get("Branch/Worktree", "-")
                connection.execute("UPDATE active_work SET status=?, branch_worktree=? WHERE plan_item_id=?",
                                   (status, None if branch == "-" else branch, board_id))
        elif terminal is not None:
            expected_status = "Merged" if terminal == "completed" else "Dropped"
            if status != expected_status:
                raise ValueError("terminal history cannot be reopened through compatibility writes")
        else:
            raise ValueError("planned item %s has no lifecycle reference" % board_id)
        connection.execute("""UPDATE planned_items SET task=?, type=?, priority=?, risk=?,
            blocked_by=?, repos=?, notes=? WHERE id=?""",
                           (values.get("Task", ""), values.get("Type", ""),
                            values.get("Priority", ""), values.get("Risk", ""),
                            values.get("Blocked by", ""), values.get("Repos", ""),
                            values.get("Notes", ""), board_id))
    for board_id in existing.keys() - seen:
        queue, terminal, _display, active_status, _branch = existing[board_id]
        if terminal is not None:
            continue
        if queue is None and active_status is None:
            raise ValueError("planned item %s has no lifecycle reference" % board_id)
        connection.execute("DELETE FROM active_work WHERE plan_item_id=?", (board_id,))
        connection.execute("UPDATE planned_items SET queue_position=NULL, terminal_outcome='cancelled' "
                           "WHERE id=?", (board_id,))


class PlanValidationError(ValueError):
    pass


def validate_plan_batch(items, existing_ids):
    """Validate and assign IDs to an accepted JSON batch without performing I/O."""
    if not isinstance(items, list) or not items:
        raise PlanValidationError("accepted batch must be a non-empty JSON array")
    required = {"key", "task", "type", "priority", "risk", "user_story", "acceptance_criteria"}
    allowed = required | {"blocked_by", "repos", "notes"}
    keys = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise PlanValidationError("item %d must be a JSON object" % (index + 1))
        missing = required - item.keys()
        unknown = item.keys() - allowed
        if missing:
            raise PlanValidationError("item %d missing fields: %s" %
                                      (index + 1, ", ".join(sorted(missing))))
        if unknown:
            raise PlanValidationError("item %d has unknown fields: %s" %
                                      (index + 1, ", ".join(sorted(unknown))))
        key = item["key"]
        if not isinstance(key, str) or not key.strip() or re.fullmatch(r"BOARD-\d+", key):
            raise PlanValidationError("item %d has an invalid temporary key" % (index + 1))
        if key in keys:
            raise PlanValidationError("duplicate temporary key %r" % key)
        keys.append(key)
        for name in ("task", "risk", "user_story"):
            value = item[name]
            if not isinstance(value, str) or not value.strip():
                raise PlanValidationError("item %d requires non-empty %s" % (index + 1, name))
        if any(char in item["task"] or char in item["risk"] for char in "\n\r|"):
            raise PlanValidationError("task and risk must be single-line values without pipes")
        if not isinstance(item["type"], str) or item["type"] not in TYPES:
            raise PlanValidationError("item %d has invalid type %r" % (index + 1, item["type"]))
        if not isinstance(item["priority"], str) or item["priority"] not in PRIORITIES:
            raise PlanValidationError("item %d has invalid priority %r" %
                                      (index + 1, item["priority"]))
        criteria = item["acceptance_criteria"]
        if not isinstance(criteria, list) or not 2 <= len(criteria) <= 5:
            raise PlanValidationError("item %d requires 2 to 5 acceptance criteria" % (index + 1))
        if any(not isinstance(text, str) or not text.strip() for text in criteria):
            raise PlanValidationError("item %d criteria must be non-empty strings" % (index + 1))
        dependencies = item.get("blocked_by", [])
        if not isinstance(dependencies, list) or any(
                not isinstance(ref, str) or not ref.strip() for ref in dependencies):
            raise PlanValidationError("item %d blocked_by must be an array of references" % (index + 1))
        if len(dependencies) != len(set(dependencies)):
            raise PlanValidationError("item %d has duplicate dependencies" % (index + 1))
        repos = item.get("repos", [])
        if not isinstance(repos, list) or any(
                not isinstance(repo, str) or not repo.strip() or "," in repo for repo in repos):
            raise PlanValidationError("item %d repos must be an array of repository IDs" % (index + 1))
        if len(repos) != len(set(repos)):
            raise PlanValidationError("item %d has duplicate repository IDs" % (index + 1))
        notes = item.get("notes", "")
        if not isinstance(notes, str) or any(char in notes for char in "\n\r|"):
            raise PlanValidationError("item %d notes must be a single-line value without pipes" %
                                      (index + 1))

    next_number = max((int(match.group(1)) for value in existing_ids
                       for match in [re.fullmatch(r"BOARD-(\d+)", value)] if match), default=0) + 1
    assigned = {key: "BOARD-%03d" % (next_number + index) for index, key in enumerate(keys)}
    result = []
    known_ids = set(existing_ids)
    key_set = set(keys)
    for item in items:
        dependencies = []
        for ref in item.get("blocked_by", []):
            if ref in key_set:
                if ref == item["key"]:
                    raise PlanValidationError("item %r cannot depend on itself" % ref)
                dependencies.append(assigned[ref])
            elif ref in known_ids:
                dependencies.append(ref)
            else:
                raise PlanValidationError("unknown dependency reference %r" % ref)
        result.append({
            "id": assigned[item["key"]],
            "key": item["key"],
            "task": item["task"],
            "type": item["type"],
            "priority": item["priority"],
            "risk": item["risk"],
            "blocked_by": ",".join(dependencies) if dependencies else "- None.",
            "repos": ",".join(item.get("repos", [])) or "-",
            "notes": item.get("notes", "-"),
            "user_story": item["user_story"],
            "acceptance_criteria": item["acceptance_criteria"],
        })
    return result


def require_normalized(connection):
    if not normalized_enabled(connection):
        raise ValueError("normalized board storage is required; apply the explicit migration first")


def persist_normalized_projection(connection):
    markdown, revision = connection.execute(
        "SELECT markdown, revision FROM board WHERE id=1").fetchone()
    projection = normalized_markdown(connection, markdown)
    connection.execute("UPDATE board SET markdown=?, revision=? WHERE id=1",
                        (projection, revision + 1))


def write_connection_snapshot(connection, markdown, revision, allow_completion=False):
    current_revision = connection.execute("SELECT revision FROM board WHERE id=1").fetchone()
    if current_revision is None or current_revision[0] != revision:
        raise ValueError("board revision changed during the transaction")
    parsed, error = parse_table(markdown)
    if parsed is None:
        raise ValueError(error)
    if normalized_enabled(connection):
        sync_normalized(connection, markdown, allow_completion=allow_completion)
        markdown = normalized_markdown(connection, markdown)
    connection.execute("UPDATE board SET markdown=?, revision=? WHERE id=1",
                       (markdown, revision + 1))


def accept_plan_batch(path, items):
    with connect(path) as connection:
        require_normalized(connection)
        connection.execute("BEGIN IMMEDIATE")
        existing_ids = {row[0] for row in connection.execute("SELECT id FROM planned_items")}
        accepted = validate_plan_batch(items, existing_ids)
        queue_position = connection.execute(
            "SELECT COALESCE(MAX(queue_position), -1)+1 FROM planned_items").fetchone()[0]
        display_position = connection.execute(
            "SELECT COALESCE(MAX(display_position), -1)+1 FROM planned_items").fetchone()[0]
        for offset, item in enumerate(accepted):
            connection.execute("""INSERT INTO planned_items
                (id, task, type, priority, risk, blocked_by, repos, notes, user_story,
                 queue_position, terminal_outcome, display_position)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)""",
                               (item["id"], item["task"], item["type"], item["priority"],
                                item["risk"], item["blocked_by"], item["repos"], item["notes"],
                                item["user_story"], queue_position + offset,
                                display_position + offset))
            connection.executemany("""INSERT INTO acceptance_criteria
                (plan_item_id, position, text, verified, proof) VALUES (?, ?, ?, 0, NULL)""",
                                  ((item["id"], position, text)
                                   for position, text in enumerate(item["acceptance_criteria"])))
        persist_normalized_projection(connection)
        return [{"key": item["key"], "id": item["id"]} for item in accepted]


def plan_rows(path, view):
    if view not in ("queue", "history"):
        raise ValueError("unknown planned-work view %r" % view)
    with connect(path) as connection:
        require_normalized(connection)
        connection.execute("BEGIN")
        order_column = "queue_position" if view == "queue" else "display_position"
        predicate = "queue_position IS NOT NULL" if view == "queue" else "terminal_outcome IS NOT NULL"
        rows = connection.execute("""SELECT p.id, p.task, p.type, p.priority, p.risk,
            p.blocked_by, p.repos, p.notes, p.user_story, p.queue_position,
            p.terminal_outcome, a.status, p.display_position
            FROM planned_items p LEFT JOIN active_work a ON a.plan_item_id=p.id
            WHERE %s ORDER BY p.%s""" % (predicate, order_column)).fetchall()
        items = []
        for row in rows:
            criteria = connection.execute("""SELECT position, text, verified, proof
                FROM acceptance_criteria WHERE plan_item_id=? ORDER BY position""", (row[0],)).fetchall()
            items.append({
                "id": row[0], "task": row[1], "type": row[2], "priority": row[3],
                "risk": row[4], "blocked_by": row[5], "repos": row[6], "notes": row[7],
                "user_story": row[8], "queue_position": row[9], "terminal_outcome": row[10],
                "status": row[11] or ("Backlog" if view == "queue" else
                                      "Merged" if row[10] == "completed" else "Dropped"),
                "display_position": row[12], "acceptance_criteria": [
                    {"position": criterion[0], "text": criterion[1],
                     "verified": bool(criterion[2]), "proof": criterion[3]}
                    for criterion in criteria],
            })
        return items


def transition_plan_item(path, board_id, action):
    with connect(path) as connection:
        require_normalized(connection)
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute("""SELECT p.queue_position, p.terminal_outcome, a.status,
            a.branch_worktree
            FROM planned_items p LEFT JOIN active_work a ON a.plan_item_id=p.id WHERE p.id=?""",
                                 (board_id,)).fetchone()
        if row is None:
            raise ValueError("no planned item with ID %s" % board_id)
        queue_position, terminal, status, branch_worktree = row
        if terminal is not None:
            raise ValueError("%s is already in terminal history" % board_id)
        if action == "promote":
            if queue_position is None or status is not None:
                raise ValueError("%s is not queued" % board_id)
            connection.execute("UPDATE planned_items SET queue_position=NULL WHERE id=?", (board_id,))
            connection.execute("INSERT INTO active_work (plan_item_id, status, branch_worktree) "
                                "VALUES (?, 'Ready', NULL)", (board_id,))
        elif action == "complete":
            if status is None or queue_position is not None:
                raise ValueError("%s is not active" % board_id)
            if branch_worktree is not None or status == "Pending Merge":
                raise ValueError("%s must be completed through human-only worktree finalization" %
                                 board_id)
            connection.execute("DELETE FROM active_work WHERE plan_item_id=?", (board_id,))
            connection.execute("UPDATE planned_items SET terminal_outcome='completed' WHERE id=?",
                               (board_id,))
        elif action == "cancel":
            if status is None and queue_position is None:
                raise ValueError("%s has no cancellable lifecycle reference" % board_id)
            connection.execute("DELETE FROM active_work WHERE plan_item_id=?", (board_id,))
            connection.execute("UPDATE planned_items SET queue_position=NULL, "
                               "terminal_outcome='cancelled' WHERE id=?", (board_id,))
        else:
            raise ValueError("unknown planned-work transition %r" % action)
        persist_normalized_projection(connection)


def format_plan_items(items, view):
    def display_cell(value):
        return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")

    rows = []
    for item in items:
        criteria = "; ".join("%d: [%s] %s%s" % (
            value["position"] + 1, "x" if value["verified"] else " ", value["text"],
            " (Proof: %s)" % value["proof"] if value["proof"] else "")
                              for value in item["acceptance_criteria"])
        position = item["queue_position"] if view == "queue" else item["display_position"]
        end = "queue_position" if view == "queue" else "display_position"
        values = [item["id"], item["task"], item["type"], item["status"], item["priority"],
                  item["risk"], item["blocked_by"], item["repos"], item["user_story"],
                  criteria, item["notes"], "%s=%s" % (end, position)]
        rows.append(" | ".join(display_cell(value) for value in values))
    return "\n".join(rows)


def criteria_from_notes(notes):
    """Extract explicit Markdown checklist entries and their immediately-following proof lines."""
    items = []
    lines = (notes or "").splitlines()
    for index, line in enumerate(lines):
        checkboxes = list(re.finditer(
            r"(?:^\s*|;\s+)([-*]\s+\[([ xX])\]\s+.*?)(?=;\s+[-*]\s+\[[ xX]\]\s+|$)",
            line))
        for checkbox_index, checkbox in enumerate(checkboxes):
            match = re.match(r"[-*]\s+\[([ xX])\]\s+(.+?)\s*$", checkbox.group(1))
            proof = None
            text = match.group(2)
            inline_proof = re.match(r"^(.*?)\s*;\s*Proof:\s*(.+?)\s*$", text, re.IGNORECASE)
            if inline_proof:
                text, proof = inline_proof.groups()
            if checkbox_index == len(checkboxes) - 1 and index + 1 < len(lines):
                proof_match = re.match(r"^\s{2,}(?:[-*]\s+)?Proof:\s*(.+?)\s*$",
                                       lines[index + 1], re.IGNORECASE)
                if proof_match and proof is None:
                    proof = proof_match.group(1)
            items.append((text, match.group(1).strip().lower() == "x", proof))
    return items


def migrate_normalized(path, apply=False):
    """Explicitly normalize the imported Markdown snapshot; dry-run does not write."""
    if apply:
        connection_context = connect(path)
    else:
        connection_context = contextlib.closing(sqlite3.connect(
            "file:" + os.path.abspath(path) + "?mode=ro", uri=True))
    with connection_context as connection:
        if apply:
            connection.execute("BEGIN IMMEDIATE")
        if connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='board'").fetchone() is None:
            raise ValueError("legacy board snapshot is missing")
        if normalized_enabled(connection):
            raise ValueError("normalized board schema already exists; refusing repeat migration")
        row = connection.execute("SELECT markdown, revision FROM board WHERE id=1").fetchone()
        if row is None:
            raise ValueError("legacy board snapshot is missing")
        parsed, error = parse_table(row[0], path)
        if parsed is None:
            raise ValueError(error)
        records = []
        headers = [cell.strip() for cell in header_cells(parsed)]
        for position, line_index in enumerate(parsed["rows"]):
            cells = cell_texts(parsed["lines"], line_index)
            values = dict(zip(headers, cells))
            status = values.get("Status", "")
            if status not in STATUSES:
                raise ValueError("unsupported legacy status %r for %s" % (status, values.get("ID")))
            records.append((values, status, position))
        if not apply:
            return {"items": len(records), "queued": sum(s == "Backlog" for _, s, _ in records),
                    "active": sum(s in OPEN_STATUSES[1:] for _, s, _ in records),
                    "completed": sum(s == "Merged" for _, s, _ in records),
                    "cancelled": sum(s == "Dropped" for _, s, _ in records)}

        backup_path = path + ".pre-normalized.bak"
        if os.path.exists(backup_path):
            raise ValueError("migration backup already exists; refusing to overwrite it")
        backup = sqlite3.connect(backup_path)
        try:
            source = sqlite3.connect(
                "file:" + os.path.abspath(path) + "?mode=ro", uri=True)
            try:
                source.backup(backup)
            finally:
                source.close()
            result = backup.execute("PRAGMA integrity_check").fetchone()[0]
            if result != "ok":
                raise sqlite3.DatabaseError("backup integrity check failed: %s" % result)
            if backup.execute("SELECT markdown, revision FROM board WHERE id=1").fetchone() != row:
                raise sqlite3.DatabaseError("backup does not match locked legacy snapshot")
        except BaseException:
            backup.close()
            if os.path.exists(backup_path):
                os.unlink(backup_path)
            raise
        else:
            backup.close()

        normalized_schema(connection)
        queue_position = 0
        for values, status, source_position in records:
            board_id = values.get("ID", "")
            branch = values.get("Branch/Worktree", "-")
            item_values = (board_id, values.get("Task", ""), values.get("Type", ""),
                           values.get("Priority", ""), values.get("Risk", ""),
                           values.get("Blocked by", ""), values.get("Repos", ""),
                           values.get("Notes", ""), source_position)
            queued_at = queue_position if status == "Backlog" else None
            if queued_at is not None:
                queue_position += 1
            terminal = "completed" if status == "Merged" else "cancelled" if status == "Dropped" else None
            connection.execute("""INSERT INTO planned_items
                (id, task, type, priority, risk, blocked_by, repos, notes, display_position,
                 user_story, queue_position, terminal_outcome)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)""",
                               item_values[:8] + (item_values[8], queued_at, terminal))
            if status in OPEN_STATUSES[1:]:
                connection.execute("INSERT INTO active_work VALUES (?, ?, ?)",
                                   (board_id, status, None if branch == "-" else branch))
            for criterion_position, (text, verified, proof) in enumerate(
                    criteria_from_notes(values.get("Notes", ""))):
                connection.execute("""INSERT INTO acceptance_criteria
                    (plan_item_id, position, text, verified, proof) VALUES (?, ?, ?, ?, ?)""",
                                   (board_id, criterion_position, text, int(verified), proof))
        connection.execute("UPDATE board SET revision=revision+1 WHERE id=1")
        connection.commit()
        return {"items": len(records), "queued": sum(s == "Backlog" for _, s, _ in records),
                "active": sum(s in OPEN_STATUSES[1:] for _, s, _ in records),
                "completed": sum(s == "Merged" for _, s, _ in records),
                "cancelled": sum(s == "Dropped" for _, s, _ in records),
                "backup": backup_path}


def live_database(path):
    candidate = os.path.abspath(path)
    root = os.path.dirname(os.path.dirname(candidate))
    if candidate != os.path.join(root, BOARD_PATH):
        return None
    result = subprocess.run(["git", "-C", root, "rev-parse", "--show-toplevel"],
                            capture_output=True, text=True, timeout=10)
    if result.returncode or os.path.realpath(result.stdout.strip()) != os.path.realpath(root):
        return None
    if candidate != os.path.abspath(os.path.join(control_root(root), BOARD_PATH)):
        return None
    return database_path(root)


def read_table(path, active_only=False):
    """(lines, header_index, row_indexes) for the board table, or None when it cannot be parsed."""
    try:
        db = live_database(path)
        if db:
            initialize_board(os.path.dirname(os.path.dirname(os.path.abspath(path))))
            with connect(db) as connection:
                content, revision = connection.execute(
                    "SELECT markdown, revision FROM board WHERE id = 1").fetchone()
                if normalized_enabled(connection):
                    content = normalized_markdown(connection, content, active_only=active_only)
            if not active_only:
                if not hasattr(_snapshots, "values"):
                    _snapshots.values = {}
                _snapshots.values[db] = (content, revision)
        else:
            with open(path, encoding="utf-8") as stream:
                content = stream.read()
        return parse_table(content, path)
    except (OSError, UnicodeError, sqlite3.Error, ValueError) as exc:
        return None, "cannot read %s: %s" % (path, exc)


def parse_table(content, path="board"):
    lines = content.split("\n")

    header = None
    for i, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            continue
        cells = split_row(line)
        if cells and [c.strip() for c in cells[:2]] == ["ID", "Task"]:
            header = i
            break
    if header is None:
        return None, "no board table found in %s (expected a header row starting with | ID | Task |)" % path
    if header + 1 >= len(lines):
        return None, "the board table has no separator row"
    sep = split_row(lines[header + 1])
    if not sep or not all(re.fullmatch(r":?-{2,}:?", c.strip()) for c in sep):
        return None, "the row after the board header is not a separator row"

    rows = []
    width = len(split_row(lines[header]))
    for i in range(header + 2, len(lines)):
        if not lines[i].lstrip().startswith("|"):
            break
        cells = split_row(lines[i])
        if cells and cells[0].strip():
            if len(cells) != width:
                return None, ("row %d has %d cells, the header has %d; refusing to touch %s"
                              % (i + 1, len(cells), width, path))
            rows.append(i)
    return {"lines": lines, "header": header, "rows": rows}, None


def split_row(line):
    """The cells of a markdown table row. A pipe escaped with a backslash stays in its cell."""
    stripped = line.strip()
    if not stripped.startswith("|"):
        return []
    parts = re.split(r"(?<!\\)\|", stripped)
    if parts and parts[0].strip() == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return parts


def cell_texts(lines, index):
    return [c.strip().replace("\\|", "|") for c in split_row(lines[index])]


def header_cells(table):
    """The raw header cells of the table."""
    return split_row(table["lines"][table["header"]])


def column_index(table, name):
    """The index of a named column, or None when the table has no such column."""
    for i, cell in enumerate(header_cells(table)):
        if cell.strip().lower() == name.strip().lower():
            return i
    return None


def field_index(table, field):
    """The index of the column a field lives in, or None when the table lacks it."""
    name = COLUMN_FOR_FIELD.get(field)
    return column_index(table, name) if name else None


def insert_cell(line, index, value):
    """The same row with a new cell at `index`; every other cell keeps its bytes."""
    stripped = line.strip()
    lead = line[:len(line) - len(line.lstrip())]
    parts = re.split(r"(?<!\\)\|", stripped)
    leading_pipe = bool(parts) and parts[0].strip() == ""
    if leading_pipe:
        parts = parts[1:]
    trailing_pipe = bool(parts) and parts[-1].strip() == ""
    if trailing_pipe:
        parts = parts[:-1]
    parts.insert(index, value)
    return lead + ("|" if leading_pipe else "") + "|".join(parts) + ("|" if trailing_pipe else "")


def replace_cell(line, index, value):
    """The same row with only cell `index` changed; every other byte stays as it was."""
    stripped = line.strip()
    lead = line[:len(line) - len(line.lstrip())]
    parts = re.split(r"(?<!\\)\|", stripped)
    leading_pipe = bool(parts) and parts[0].strip() == ""
    if leading_pipe:
        parts = parts[1:]
    trailing_pipe = bool(parts) and parts[-1].strip() == ""
    if trailing_pipe:
        parts = parts[:-1]
    if index is None or index >= len(parts):
        return line
    raw = parts[index]
    left = raw[:len(raw) - len(raw.lstrip())]
    right = raw[len(raw.rstrip()):]
    parts[index] = left + value.replace("|", "\\|") + right
    return lead + ("|" if leading_pipe else "") + "|".join(parts) + ("|" if trailing_pipe else "")


def write_atomic(path, lines, allow_completion=False):
    db = live_database(path)
    if db:
        snapshot = getattr(_snapshots, "values", {}).pop(db, None)
        if snapshot is None:
            raise ValueError("read_table must precede a board mutation")
        baseline, _ = snapshot
        proposed = "\n".join(lines)
        parsed, error = parse_table(proposed, path)
        if parsed is None:
            raise ValueError(error)
        with connect(db) as connection:
            connection.execute("BEGIN IMMEDIATE")
            latest, revision = connection.execute(
                "SELECT markdown, revision FROM board WHERE id = 1").fetchone()
            if normalized_enabled(connection):
                latest = normalized_markdown(connection, latest)
            merged = merge_board_changes(baseline, proposed, latest)
            if normalized_enabled(connection):
                sync_normalized(connection, merged, allow_completion=allow_completion)
                merged = normalized_markdown(connection, latest)
            connection.execute("UPDATE board SET markdown = ?, revision = ? WHERE id = 1",
                               (merged, revision + 1))
        return
    directory = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".board.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write("\n".join(lines))
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def merge_board_changes(baseline, proposed, latest):
    """Apply changed cells by ID; refuse overlapping edits instead of losing updates."""
    original, error = parse_table(baseline)
    updated, update_error = parse_table(proposed)
    current, current_error = parse_table(latest)
    if original is None or updated is None or current is None:
        raise ValueError(error or update_error or current_error)
    before = {cell_texts(original["lines"], i)[0]: original["lines"][i] for i in original["rows"]}
    after = {cell_texts(updated["lines"], i)[0]: updated["lines"][i] for i in updated["rows"]}
    if len(before) != len(original["rows"]) or len(after) != len(updated["rows"]):
        raise ValueError("duplicate board ID")
    if (header_cells(original) != header_cells(updated)
            or original["lines"][original["header"] + 1] != updated["lines"][updated["header"] + 1]):
        if latest != baseline:
            raise ValueError("board columns changed concurrently; retry")
        return proposed
    result = list(current["lines"])
    indexes = {cell_texts(result, i)[0]: i for i in current["rows"]}
    if len(indexes) != len(current["rows"]):
        raise ValueError("duplicate board ID in live state")
    for row_id, raw in before.items():
        if row_id not in after:
            if row_id not in indexes or result[indexes[row_id]] != raw:
                raise ValueError("row %s changed concurrently; retry" % row_id)
            result[indexes[row_id]] = None
        elif raw != after[row_id]:
            if row_id not in indexes:
                raise ValueError("row %s removed concurrently; retry" % row_id)
            old_cells = split_row(raw)
            new_cells = split_row(after[row_id])
            live_cells = split_row(result[indexes[row_id]])
            if len(old_cells) != len(new_cells) or len(live_cells) != len(old_cells):
                raise ValueError("board columns changed concurrently; retry")
            for n, (old, new) in enumerate(zip(old_cells, new_cells)):
                if old != new:
                    if live_cells[n] != old:
                        raise ValueError("row %s cell changed concurrently; retry" % row_id)
                    result[indexes[row_id]] = replace_cell(result[indexes[row_id]], n, new.strip().replace("\\|", "|"))
                    live_cells = split_row(result[indexes[row_id]])
    result = [line for line in result if line is not None]
    additions = [after[cell_texts(updated["lines"], i)[0]] for i in updated["rows"]
                 if cell_texts(updated["lines"], i)[0] not in before]
    for row in additions:
        row_id = cell_texts([row], 0)[0]
        if row_id in indexes:
            raise ValueError("row %s added concurrently; retry" % row_id)
    insert_at = (max((i for i, line in enumerate(result) if line.lstrip().startswith("|")
                      and cell_texts(result, i)[0] in indexes), default=current["header"] + 1) + 1)
    result[insert_at:insert_at] = additions
    return "\n".join(result)


def note_uncommitted(path):
    if live_database(path):
        return
    try:
        r = subprocess.run(["git", "status", "--short", "--", os.path.relpath(path)],
                           capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return
    if r.returncode == 0 and r.stdout.strip():
        print("note: %s has uncommitted changes" % os.path.relpath(path))


def row_by_id(table, board_id):
    for i in table["rows"]:
        cells = cell_texts(table["lines"], i)
        if cells and cells[0] == board_id:
            return i
    return None


def normalized_path(path):
    db = live_database(path)
    if not db:
        return None
    with connect(db) as connection:
        return db if normalized_enabled(connection) else None


def normalized_state(path, board_id):
    db = normalized_path(path)
    if not db:
        return None
    with connect(db) as connection:
        row = connection.execute("""SELECT p.queue_position, p.terminal_outcome, a.status
            FROM planned_items p LEFT JOIN active_work a ON a.plan_item_id=p.id WHERE p.id=?""",
                                 (board_id,)).fetchone()
    if row is None:
        return None
    queue_position, terminal, status = row
    kind = "queued" if queue_position is not None else "active" if status is not None else \
        "terminal" if terminal is not None else "invalid"
    return {"kind": kind, "queue_position": queue_position, "terminal_outcome": terminal,
            "status": status}


def reject_unsafe_value(name, value):
    if any(char in value for char in "\n\r|"):
        print("invalid %s: the value must be on one line and must not contain a pipe; "
              "use a middle dot (·), a comma, or a semicolon instead" % name,
              file=sys.stderr)
        return True
    return False


def reject_unsafe_fingerprint(value):
    if any(char in value for char in "\n\r"):
        print("invalid --fingerprint: the value must be on one line", file=sys.stderr)
        return True
    return False


def normalize_fingerprint(value):
    """The canonical fingerprint: kind|category|route|subject, lowercased and trimmed."""
    parts = [part.strip().lower() for part in (value or "").split("|")]
    while len(parts) < 4:
        parts.append("-")
    return "|".join(parts[:4])


def row_fingerprint(cells, notes_index):
    """The fingerprint carried by a row's Notes cell, or an empty string."""
    notes = cells[notes_index] if notes_index is not None and len(cells) > notes_index else ""
    match = re.search(re.escape(FINGERPRINT_PREFIX) + r"([^\s|·]+\|[^\s|·]+\|[^\s|·]+\|[^\s|·]+)", notes)
    return normalize_fingerprint(match.group(1)) if match else ""


def fingerprint_notes(fingerprint, note):
    """The Notes cell text for a row that carries a fingerprint."""
    if not fingerprint:
        return note or "-"
    token = FINGERPRINT_PREFIX + fingerprint
    if not note:
        return token
    return token + " · " + note


def find_open_fingerprint(table, fingerprint):
    """(id, status) of the open row carrying this fingerprint, or (None, None)."""
    notes_index = field_index(table, "notes")
    for i in table["rows"]:
        cells = cell_texts(table["lines"], i)
        if len(cells) < 4:
            continue
        if cells[3] not in OPEN_STATUSES:
            continue
        if row_fingerprint(cells, notes_index) == fingerprint:
            return cells[0], cells[3]
    return None, None


def cmd_show(args, path):
    table, err = read_table(path, active_only=True)
    if table is None:
        print(err, file=sys.stderr)
        return REFUSED
    width = len(header_cells(table))
    wanted = args.id
    found = False
    for i in table["rows"]:
        cells = cell_texts(table["lines"], i)
        if len(cells) < width:
            print("skipping malformed row %d: %d cells" % (i + 1, len(cells)), file=sys.stderr)
            continue
        if wanted and cells[0] != wanted:
            continue
        found = True
        print(" | ".join(cells[:-1]))
    if wanted and not found:
        print("no row with ID %s" % wanted, file=sys.stderr)
        return REFUSED
    return OK


def escalate_repeat(table, existing_id, fingerprint):
    """A repeat finding: the existing row carries it and is escalated to Blocked."""
    index = row_by_id(table, existing_id)
    if index is None:
        return
    notes_index = field_index(table, "notes")
    cells = cell_texts(table["lines"], index)
    notes = cells[notes_index] if notes_index is not None and len(cells) > notes_index else ""
    merged = notes + " · repeat finding: fingerprint " + fingerprint
    table["lines"][index] = replace_cell(table["lines"][index], notes_index, merged)
    table["lines"][index] = replace_cell(table["lines"][index], 3, "Blocked")


def cmd_add(args, path):
    named_values = [("--id", args.id), ("--task", args.task), ("--risk", args.risk),
                     ("--blocked-by", args.blocked_by), ("--repos", args.repos),
                     ("--branch-worktree", args.branch_worktree), ("--note", args.note)]
    for name, value in named_values:
        if value is not None and reject_unsafe_value(name, value):
            return REFUSED
    if args.fingerprint is not None and reject_unsafe_fingerprint(args.fingerprint):
        return REFUSED
    fingerprint = normalize_fingerprint(args.fingerprint) if args.fingerprint else ""
    table, err = read_table(path)
    if table is None:
        print(err, file=sys.stderr)
        return REFUSED
    if normalized_path(path):
        print("normalized planned items must be created with 'board.py plan accept'", file=sys.stderr)
        return REFUSED
    if row_by_id(table, args.id) is not None:
        print("ID %s already exists on the board" % args.id, file=sys.stderr)
        return REFUSED
    if fingerprint:
        existing_id, existing_status = find_open_fingerprint(table, fingerprint)
        if existing_id is not None:
            escalate_repeat(table, existing_id, fingerprint)
            note_uncommitted(path)
            write_atomic(path, table["lines"])
            print("refused: fingerprint %s is already open on %s (status: %s)" %
                  (fingerprint, existing_id, existing_status), file=sys.stderr)
            print("this is a repeat finding: %s now carries it and is Blocked" % existing_id,
                  file=sys.stderr)
            print("add the new evidence to it with:", file=sys.stderr)
            print("  python3 %s note %s --value \"<the new evidence>\"" %
                  (sys.argv[0], existing_id), file=sys.stderr)
            return REFUSED
    by_column = {
        "ID": args.id,
        "Task": args.task,
        "Type": args.type,
        "Status": args.status,
        "Priority": args.priority,
        "Risk": args.risk,
        "Blocked by": args.blocked_by or "- None.",
        "Repos": args.repos or "-",
        "Branch/Worktree": args.branch_worktree or "-",
        "Notes": fingerprint_notes(fingerprint, args.note),
    }
    values = [by_column.get(cell.strip(), "-") for cell in header_cells(table)]
    if args.repos and column_index(table, "Repos") is None:
        print("note: the board has no Repos column, so --repos was not written; add it with "
              "'board.py add-column --name Repos --after \"Blocked by\"'")
    new_row = "| " + " | ".join(v.replace("|", "\\|") for v in values) + " |"
    lines = list(table["lines"])
    insert_at = (table["rows"][-1] + 1) if table["rows"] else table["header"] + 2
    lines.insert(insert_at, new_row)
    note_uncommitted(path)
    write_atomic(path, lines)
    print("added %s (%s, %s)" % (args.id, args.type, args.status))
    if fingerprint:
        print("fingerprint: %s" % fingerprint)
    return OK


def cmd_add_column(args, path):
    """Insert a column into the table; every row gets an empty cell in it."""
    if "|" in args.name or "\n" in args.name:
        print("invalid --name: the column name must be on one line and must not contain a pipe",
              file=sys.stderr)
        return INVALID
    if normalized_path(path):
        print("normalized board columns are fixed by the SQLite schema", file=sys.stderr)
        return REFUSED
    table, err = read_table(path)
    if table is None:
        print(err, file=sys.stderr)
        return REFUSED
    lines = list(table["lines"])
    header = table["header"]
    names = [cell.strip() for cell in split_row(lines[header])]
    width = len(names)
    if args.name.strip() in names:
        print("column %s already exists" % args.name, file=sys.stderr)
        return REFUSED
    if args.after:
        after = args.after.strip().lower()
        index = None
        for i, name in enumerate(names):
            if name.lower() == after:
                index = i
                break
        if index is None:
            print("no column named %r; the table has: %s" % (args.after, ", ".join(names)),
                  file=sys.stderr)
            return REFUSED
        at = index + 1
    else:
        at = width
    for i in table["rows"]:
        cells = split_row(lines[i])
        if len(cells) != width:
            print("row %d has %d cells, the header has %d; refusing to touch the file"
                  % (i + 1, len(cells), width), file=sys.stderr)
            return REFUSED
    lines[header] = insert_cell(lines[header], at, " %s " % args.name.strip())
    lines[header + 1] = insert_cell(lines[header + 1], at, "---")
    for i in table["rows"]:
        lines[i] = insert_cell(lines[i], at, " ")
    note_uncommitted(path)
    write_atomic(path, lines)
    print("added column %s%s" % (args.name.strip(),
                                 " after %s" % args.after.strip() if args.after else " at the end"))
    print("rows updated: %d" % len(table["rows"]))
    return OK


def cmd_note(args, path):
    if reject_unsafe_value("--value", args.value):
        return REFUSED
    table, err = read_table(path)
    if table is None:
        print(err, file=sys.stderr)
        return REFUSED
    index = row_by_id(table, args.id)
    if index is None:
        print("no row with ID %s" % args.id, file=sys.stderr)
        return REFUSED
    if args.escalate:
        state = normalized_state(path, args.id)
        if state is not None and state["kind"] != "active":
            print("only active items can be escalated with --escalate", file=sys.stderr)
            return REFUSED
    cells = cell_texts(table["lines"], index)
    notes_index = field_index(table, "notes")
    notes = cells[notes_index] if notes_index is not None and len(cells) > notes_index else ""
    if notes in ("", "-"):
        merged = args.value
    else:
        merged = notes + " · " + args.value
    lines = list(table["lines"])
    lines[index] = replace_cell(lines[index], notes_index, merged)
    if args.escalate:
        lines[index] = replace_cell(lines[index], 3, "Blocked")
    note_uncommitted(path)
    write_atomic(path, lines)
    print("%s notes updated%s" % (args.id, " and escalated to Blocked" if args.escalate else ""))
    return OK


def cmd_set_status(args, path):
    table, err = read_table(path)
    if table is None:
        print(err, file=sys.stderr)
        return REFUSED
    index = row_by_id(table, args.id)
    if index is None:
        print("no row with ID %s" % args.id, file=sys.stderr)
        return REFUSED
    state = normalized_state(path, args.id)
    if state is not None:
        if state["kind"] != "active" or args.status not in OPEN_STATUSES[1:]:
            print("set-status only changes an active item to another active status; use plan commands "
                  "for lifecycle transitions", file=sys.stderr)
            return REFUSED
    lines = list(table["lines"])
    lines[index] = replace_cell(lines[index], 3, args.status)
    note_uncommitted(path)
    write_atomic(path, lines)
    print("%s status set to %s" % (args.id, args.status))
    return OK


def cmd_set_field(args, path):
    if reject_unsafe_value("--value", args.value):
        return REFUSED
    table, err = read_table(path)
    if table is None:
        print(err, file=sys.stderr)
        return REFUSED
    index = row_by_id(table, args.id)
    if index is None:
        print("no row with ID %s" % args.id, file=sys.stderr)
        return REFUSED
    state = normalized_state(path, args.id)
    if args.field == "branch-worktree" and state is not None and state["kind"] != "active":
        print("branch-worktree can only be set on active items", file=sys.stderr)
        return REFUSED
    column = field_index(table, args.field)
    if column is None:
        print("the board has no %s column; add it with 'board.py add-column --name %s'"
              % (COLUMN_FOR_FIELD[args.field], COLUMN_FOR_FIELD[args.field]), file=sys.stderr)
        return REFUSED
    lines = list(table["lines"])
    lines[index] = replace_cell(lines[index], column, args.value)
    note_uncommitted(path)
    write_atomic(path, lines)
    print("%s %s set" % (args.id, args.field))
    return OK


def cmd_remove(args, path):
    state = normalized_state(path, args.id)
    if state is not None:
        try:
            transition_plan_item(path, args.id, "cancel")
        except (ValueError, sqlite3.Error) as exc:
            print("cannot cancel %s: %s" % (args.id, exc), file=sys.stderr)
            return REFUSED
        print("cancelled %s" % args.id)
        return OK
    table, err = read_table(path)
    if table is None:
        print(err, file=sys.stderr)
        return REFUSED
    index = row_by_id(table, args.id)
    if index is None:
        print("no row with ID %s" % args.id, file=sys.stderr)
        return REFUSED
    cells = cell_texts(table["lines"], index)
    if cells[3] in ("Merged", "Dropped"):
        print("%s is already terminal; its history is retained" % args.id, file=sys.stderr)
        return REFUSED
    lines = list(table["lines"])
    lines[index] = replace_cell(lines[index], 3, "Dropped")
    note_uncommitted(path)
    write_atomic(path, lines)
    print("cancelled %s" % args.id)
    return OK


def cmd_plan(args, path):
    if args.plan_command == "accept":
        try:
            items = json.load(sys.stdin)
            accepted = accept_plan_batch(path, items)
        except json.JSONDecodeError as exc:
            print("invalid plan JSON: %s" % exc, file=sys.stderr)
            return INVALID
        except PlanValidationError as exc:
            print("invalid plan batch: %s" % exc, file=sys.stderr)
            return INVALID
        except (ValueError, sqlite3.Error) as exc:
            print("plan acceptance refused: %s" % exc, file=sys.stderr)
            return REFUSED
        for item in accepted:
            print("accepted %s as %s" % (item["key"], item["id"]))
        return OK
    if args.plan_command in ("queue", "history"):
        try:
            items = plan_rows(path, args.plan_command)
        except (ValueError, sqlite3.Error) as exc:
            print("planned-work view refused: %s" % exc, file=sys.stderr)
            return REFUSED
        if not items:
            print("No %s items." % ("queued" if args.plan_command == "queue" else "historical"))
        else:
            print(format_plan_items(items, args.plan_command))
        return OK
    try:
        transition_plan_item(path, args.id, args.plan_command)
    except (ValueError, sqlite3.Error) as exc:
        print("planned-work transition refused: %s" % exc, file=sys.stderr)
        return REFUSED
    labels = {"promote": "promoted to Ready", "complete": "completed", "cancel": "cancelled"}
    print("%s %s" % (args.id, labels[args.plan_command]))
    return OK


def cmd_lanes(args, path):
    table, err = read_table(path, active_only=True)
    if table is None:
        print(err, file=sys.stderr)
        return REFUSED
    counts = {s: 0 for s in STATUSES}
    for i in table["rows"]:
        cells = cell_texts(table["lines"], i)
        if len(cells) > 3:
            counts[cells[3]] = counts.get(cells[3], 0) + 1
    for s in STATUSES:
        print("%s: %d" % (s, counts.get(s, 0)))
    others = [k for k in counts if k not in STATUSES]
    for k in sorted(others):
        print("%s: %d" % (k, counts[k]))
    print("total: %d" % len(table["rows"]))
    return OK


def cmd_export(path):
    table, error = read_table(path, active_only=True)
    if table is None:
        print(error, file=sys.stderr)
        return REFUSED
    database = live_database(path)
    if not database:
        print("export requires the live SQLite board", file=sys.stderr)
        return REFUSED
    destination = os.path.join(os.path.dirname(database), EXPORT_NAME)
    write_export(destination, "\n".join(table["lines"]))
    print(destination)
    return OK


def main(argv):
    parser = argparse.ArgumentParser(
        prog="board.py", description="Manipulate the per-clone SQLite board.")
    parser.add_argument("--file", help="read-only Markdown fixture (not the live SQLite board)")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("show", help="print board rows")
    p.add_argument("id", nargs="?", help="one row ID; default prints all rows")

    p = sub.add_parser("add", help="append a row")
    p.add_argument("--id", required=True)
    p.add_argument("--task", required=True)
    p.add_argument("--type", required=True)
    p.add_argument("--status", required=True)
    p.add_argument("--priority", required=True)
    p.add_argument("--risk", required=True)
    p.add_argument("--blocked-by")
    p.add_argument("--repos", help="comma separated repo ids from .opencode/repos.json")
    p.add_argument("--branch-worktree")
    p.add_argument("--note")
    p.add_argument("--fingerprint", help="kind|category|route|subject; a repeat is refused")

    p = sub.add_parser("add-column", help="insert a column into the table")
    p.add_argument("--name", required=True, help="the new column name")
    p.add_argument("--after", help="the column the new one follows")

    p = sub.add_parser("note", help="append evidence to an existing row")
    p.add_argument("id")
    p.add_argument("--value", required=True)
    p.add_argument("--escalate", action="store_true",
                   help="also move the row to Blocked")

    p = sub.add_parser("set-status", help="change only the status cell")
    p.add_argument("id")
    p.add_argument("status")

    p = sub.add_parser("set-field", help="change only one cell")
    p.add_argument("id")
    p.add_argument("--field", required=True, choices=sorted(FIELDS))
    p.add_argument("--value", required=True)

    p = sub.add_parser("remove", help="remove a row")
    p.add_argument("id")

    p = sub.add_parser("migrate-normalized", help="preview or apply the normalized-board migration")
    p.add_argument("--apply", action="store_true", help="create a consistent backup and migrate")

    plan = sub.add_parser("plan", help="accept and manage planned work")
    plan_sub = plan.add_subparsers(dest="plan_command", required=True)
    plan_sub.add_parser("accept", help="accept a JSON array from stdin atomically")
    plan_sub.add_parser("queue", help="list queued work in queue order")
    plan_sub.add_parser("history", help="list completed and cancelled work")
    for action, help_text in (("promote", "promote a queued item to Ready"),
                              ("complete", "complete an active item"),
                              ("cancel", "cancel a queued or active item")):
        action_parser = plan_sub.add_parser(action, help=help_text)
        action_parser.add_argument("id")

    sub.add_parser("lanes", help="count rows per status lane")
    sub.add_parser("export", help="write a Markdown snapshot to .factory-state")
    sub.add_parser("pre-merge-check", help="verify and back up the legacy board before its one-time merge")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return USAGE
    if args.file and args.command not in ("show", "lanes"):
        print("--file is read-only; use the default SQLite board for mutations", file=sys.stderr)
        return REFUSED
    if args.command == "pre-merge-check":
        return cmd_pre_merge_check(control_root(os.getcwd()))
    if args.command == "migrate-normalized":
        try:
            path = database_path(control_root(os.getcwd()))
            result = migrate_normalized(path, args.apply)
            print(json.dumps(result, sort_keys=True))
            return OK
        except (OSError, ValueError, sqlite3.Error) as exc:
            print("normalized migration refused: %s" % exc, file=sys.stderr)
            return REFUSED
    try:
        path = args.file if args.file else initialize_board(control_root(os.getcwd()))
    except (OSError, UnicodeError, ValueError, sqlite3.Error) as exc:
        print("cannot initialize board: %s" % exc, file=sys.stderr)
        return REFUSED

    if args.command == "export":
        return cmd_export(path)

    if args.command == "plan":
        return cmd_plan(args, path)

    if args.command == "add":
        if args.type not in TYPES:
            print("invalid --type %r: use one of %s" % (args.type, ", ".join(TYPES)), file=sys.stderr)
            return INVALID
        if args.status not in STATUSES:
            print("invalid --status %r: use one of %s" % (args.status, ", ".join(STATUSES)), file=sys.stderr)
            return INVALID
        if args.priority not in PRIORITIES:
            print("invalid --priority %r: use one of %s" % (args.priority, ", ".join(PRIORITIES)),
                  file=sys.stderr)
            return INVALID
        return cmd_add(args, path)
    if args.command == "add-column":
        return cmd_add_column(args, path)
    if args.command == "note":
        return cmd_note(args, path)
    if args.command == "set-status":
        if args.status not in STATUSES:
            print("invalid status %r: use one of %s" % (args.status, ", ".join(STATUSES)),
                  file=sys.stderr)
            return INVALID
        return cmd_set_status(args, path)
    if args.command == "set-field":
        return cmd_set_field(args, path)
    if args.command == "remove":
        return cmd_remove(args, path)
    if args.command == "lanes":
        return cmd_lanes(args, path)
    return cmd_show(args, path)


def write_export(destination, content):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(destination), prefix=".board-export.")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content if isinstance(content, bytes) else content.encode("utf-8"))
        os.replace(tmp, destination)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception as exc:
        print("board.py error: %s" % exc, file=sys.stderr)
        sys.exit(REFUSED)
