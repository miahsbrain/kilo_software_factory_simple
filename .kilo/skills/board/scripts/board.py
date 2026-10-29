#!/usr/bin/env python3
"""Deterministic manipulation of the markdown board at docs/BOARD.md.

    board.py show [ID]
    board.py add --id BOARD-00X --task "..." --type Feature --status Backlog
                 --priority P1 --risk "🟢 low — one line" [--blocked-by "..."]
                 [--branch-worktree "..."] [--note "..."] [--fingerprint "kind|category|route|subject"]
    board.py note <ID> --value "..." [--escalate]
    board.py set-status <ID> "<new status>"
    board.py set-field <ID> --field risk|priority|blocked-by|branch-worktree|notes --value "..."
    board.py remove <ID>
    board.py lanes

The table is located by its header row and separator row. Rows are split on
`|`, so an escaped or unescaped pipe inside a cell breaks the parse; the script
refuses to touch the file when the table cannot be parsed. Only the named cell
changes: every other cell keeps its bytes. The file is written atomically
(temp file in the same directory, then os.replace).

A Fix row may carry a fingerprint — kind|category|route|subject — so the same
complaint about the same thing is recognised when it is filed again. A row with
a fingerprint that is already open is refused; the repeat is appended to the
existing row with `board.py note`.

Exit codes: 0 ok, 1 refusal, 2 usage error, 66 invalid input.
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

BOARD_PATH = os.path.join("docs", "BOARD.md")
TYPES = ["Feature", "Fix", "Chore", "Docs", "Research"]
STATUSES = ["Backlog", "Ready", "In Progress", "In Review", "Pending Merge",
            "Merged", "Blocked", "Dropped"]
PRIORITIES = ["P1", "P2", "P3", "P4"]
FIELDS = {"risk": 5, "priority": 4, "blocked-by": 6, "branch-worktree": 7, "notes": 8}
COLUMNS = ["ID", "Task", "Type", "Status", "Priority", "Risk", "Blocked by",
           "Branch/Worktree", "Notes"]
OPEN_STATUSES = ("Backlog", "Ready", "In Progress", "In Review", "Pending Merge", "Blocked")
FINGERPRINT_PREFIX = "fp="

OK = 0
REFUSED = 1
USAGE = 2
INVALID = 66


def board_path(explicit):
    return explicit or os.path.join(os.getcwd(), BOARD_PATH)


def read_table(path):
    """(lines, header_index, row_indexes) for the board table, or None when it cannot be parsed."""
    try:
        with open(path) as fh:
            lines = fh.read().split("\n")
    except OSError as e:
        return None, "cannot read %s: %s" % (path, e.strerror)

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
    for i in range(header + 2, len(lines)):
        if not lines[i].lstrip().startswith("|"):
            break
        cells = split_row(lines[i])
        if cells and cells[0].strip():
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
    if index >= len(parts):
        return line
    raw = parts[index]
    left = raw[:len(raw) - len(raw.lstrip())]
    right = raw[len(raw.rstrip()):]
    parts[index] = left + value.replace("|", "\\|") + right
    return lead + ("|" if leading_pipe else "") + "|".join(parts) + ("|" if trailing_pipe else "")


def write_atomic(path, lines):
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


def note_uncommitted(path):
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


def row_fingerprint(cells):
    """The fingerprint carried by a row's Notes cell, or an empty string."""
    notes = cells[8] if len(cells) > 8 else ""
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
    for i in table["rows"]:
        cells = cell_texts(table["lines"], i)
        if len(cells) < 4:
            continue
        if cells[3] not in OPEN_STATUSES:
            continue
        if row_fingerprint(cells) == fingerprint:
            return cells[0], cells[3]
    return None, None


def cmd_show(args, path):
    table, err = read_table(path)
    if table is None:
        print(err, file=sys.stderr)
        return REFUSED
    wanted = args.id
    found = False
    for i in table["rows"]:
        cells = cell_texts(table["lines"], i)
        if len(cells) < len(COLUMNS):
            print("skipping malformed row %d: %d cells" % (i + 1, len(cells)), file=sys.stderr)
            continue
        if wanted and cells[0] != wanted:
            continue
        found = True
        print(" | ".join(cells[:8]))
    if wanted and not found:
        print("no row with ID %s" % wanted, file=sys.stderr)
        return REFUSED
    return OK


def escalate_repeat(table, existing_id, fingerprint):
    """A repeat finding: the existing row carries it and is escalated to Blocked."""
    index = row_by_id(table, existing_id)
    if index is None:
        return
    cells = cell_texts(table["lines"], index)
    notes = cells[8] if len(cells) > 8 else ""
    merged = notes + " · repeat finding: fingerprint " + fingerprint
    table["lines"][index] = replace_cell(table["lines"][index], FIELDS["notes"], merged)
    table["lines"][index] = replace_cell(table["lines"][index], 3, "Blocked")


def cmd_add(args, path):
    named_values = [("--id", args.id), ("--task", args.task), ("--risk", args.risk),
                    ("--blocked-by", args.blocked_by), ("--branch-worktree", args.branch_worktree),
                    ("--note", args.note)]
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
    values = [args.id, args.task, args.type, args.status, args.priority, args.risk,
              args.blocked_by or "- None.", args.branch_worktree or "-",
              fingerprint_notes(fingerprint, args.note)]
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
    notes = cells[8] if len(cells) > 8 else ""
    if notes in ("", "-"):
        merged = args.value
    else:
        merged = notes + " · " + args.value
    lines = list(table["lines"])
    lines[index] = replace_cell(lines[index], FIELDS["notes"], merged)
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
    lines = list(table["lines"])
    lines[index] = replace_cell(lines[index], FIELDS[args.field], args.value)
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
        prog="board.py", description="Manipulate the markdown board at docs/BOARD.md.")
    parser.add_argument("--file", help="board file (default: docs/BOARD.md in the current directory)")
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
    p.add_argument("--branch-worktree")
    p.add_argument("--note")
    p.add_argument("--fingerprint", help="kind|category|route|subject; a repeat is refused")

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

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return USAGE
    path = board_path(args.file)

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


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception as exc:
        print("board.py error: %s" % exc, file=sys.stderr)
        sys.exit(REFUSED)
