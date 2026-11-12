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


def read_table(path):
    """(lines, header_index, row_indexes) for the board table, or None when it cannot be parsed."""
    try:
        db = live_database(path)
        if db:
            initialize_board(os.path.dirname(os.path.dirname(os.path.abspath(path))))
            with connect(db) as connection:
                content, revision = connection.execute(
                    "SELECT markdown, revision FROM board WHERE id = 1").fetchone()
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


def write_atomic(path, lines):
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
            merged = merge_board_changes(baseline, proposed, latest)
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
    table, err = read_table(path)
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
    table, err = read_table(path)
    if table is None:
        print(err, file=sys.stderr)
        return REFUSED
    index = row_by_id(table, args.id)
    if index is None:
        print("no row with ID %s" % args.id, file=sys.stderr)
        return REFUSED
    lines = list(table["lines"])
    del lines[index]
    note_uncommitted(path)
    write_atomic(path, lines)
    print("removed %s" % args.id)
    return OK


def cmd_lanes(args, path):
    table, err = read_table(path)
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
    try:
        path = args.file if args.file else initialize_board(control_root(os.getcwd()))
    except (OSError, UnicodeError, ValueError, sqlite3.Error) as exc:
        print("cannot initialize board: %s" % exc, file=sys.stderr)
        return REFUSED

    if args.command == "export":
        table, error = read_table(path)
        if table is None:
            print(error, file=sys.stderr)
            return REFUSED
        destination = os.path.join(os.path.dirname(live_database(path)), EXPORT_NAME)
        write_export(destination, "\n".join(table["lines"]))
        print(destination)
        return OK

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
