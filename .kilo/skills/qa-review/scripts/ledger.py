#!/usr/bin/env python3
"""ledger.py — the bounded QA/fix ledger for one board row.

One short file per row, docs/reviews/<task-id>-ledger.md, carries the state
between rounds: the round number, the findings filed in that round, the Fix
row IDs created, the Fix rows merged since, and the stop reason when it stops.

A row may go through at most 3 rounds. `next-round` refuses to open round 4;
the row moves to Blocked instead.

Usage:
  ledger.py status      --task-id BOARD-005 [--ledger-dir docs/reviews]
  ledger.py next-round  --task-id BOARD-005
  ledger.py finding     --task-id BOARD-005 --fingerprint "kind|category|route|subject"
                         [--evidence <path>] [--fix-row BOARD-010]
  ledger.py merged      --task-id BOARD-005 --fix-row BOARD-010
  ledger.py stop        --task-id BOARD-005 --reason "..."
  ledger.py show        --task-id BOARD-005

Exit codes: 0 ok, 1 refused, 2 usage error.
"""
import argparse
import os
import re
import sys

MAX_ROUNDS = 3
FIELDS = ("Findings", "Fix rows", "Fix rows merged", "Stop reason")
ROUND_RE = re.compile(r"^## Round (\d+)\s*$")


def ledger_path(ledger_dir, task_id):
    return os.path.join(ledger_dir, "%s-ledger.md" % task_id)


def parse_ledger(text):
    """(header, [(number, {field: value})]). A round is a '## Round N' heading."""
    rounds = []
    header = []
    current = None
    for line in text.split("\n"):
        match = ROUND_RE.match(line)
        if match:
            current = {"number": int(match.group(1)), "fields": {}}
            rounds.append(current)
            continue
        if current is None:
            header.append(line)
            continue
        item = re.match(r"^- ([A-Za-z ]+): (.*)$", line)
        if item and item.group(1) in FIELDS:
            current["fields"][item.group(1)] = item.group(2).strip()
    return header, rounds


def render_ledger(header, rounds):
    lines = [line for line in header if line.strip()]
    for entry in rounds:
        lines.append("")
        lines.append("## Round %d" % entry["number"])
        for field in FIELDS:
            lines.append("- %s: %s" % (field, entry["fields"].get(field, "-")))
    return "\n".join(lines) + "\n"


def read_ledger(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return ""


def write_ledger(path, header, rounds):
    directory = os.path.dirname(os.path.abspath(path)) or "."
    if not os.path.isdir(directory):
        os.makedirs(directory)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(render_ledger(header, rounds))


def load(ledger_dir, task_id):
    path = ledger_path(ledger_dir, task_id)
    header, rounds = parse_ledger(read_ledger(path))
    if not any(line.strip() for line in header):
        header = default_header(task_id)
    return path, header, rounds


def default_header(task_id):
    return [
        "# Ledger — %s" % task_id,
        "",
        "Round cap: %d. The ledger is the only state carried between rounds." % MAX_ROUNDS,
        "",
    ]


def append_item(current, item):
    """A comma-separated field, or the item alone when the field is empty."""
    if current is None or current in ("", "-"):
        return item
    return current + ", " + item


def cmd_status(args):
    path, header, rounds = load(args.ledger_dir, args.task_id)
    used = len(rounds)
    last = rounds[-1] if rounds else None
    print("ledger: %s" % path)
    print("rounds used: %d of %d" % (used, MAX_ROUNDS))
    print("next round: %d" % (used + 1) if used < MAX_ROUNDS else "next round: none (cap reached)")
    if last:
        for field in FIELDS:
            value = last["fields"].get(field, "-")
            if value != "-":
                print("round %d %s: %s" % (last["number"], field.lower(), value))
    return OK


def cmd_next_round(args):
    path, header, rounds = load(args.ledger_dir, args.task_id)
    if len(rounds) >= MAX_ROUNDS:
        print("refused: the round cap of %d is reached for %s" % (MAX_ROUNDS, args.task_id),
              file=sys.stderr)
        print("move the row to Blocked with a summary of what was tried and the question "
              "the human has to answer", file=sys.stderr)
        return REFUSED
    number = len(rounds) + 1
    rounds.append({"number": number, "fields": {field: "-" for field in FIELDS}})
    write_ledger(path, header, rounds)
    print("round %d opened" % number)
    return OK


def cmd_finding(args):
    path, header, rounds = load(args.ledger_dir, args.task_id)
    if not rounds:
        print("refused: no round is open for %s; run next-round first" % args.task_id,
              file=sys.stderr)
        return REFUSED
    entry = rounds[-1]
    item = args.fingerprint
    if args.evidence:
        item += " — " + args.evidence
    entry["fields"]["Findings"] = append_item(entry["fields"].get("Findings"), item)
    if args.fix_row:
        entry["fields"]["Fix rows"] = append_item(entry["fields"].get("Fix rows"), args.fix_row)
    write_ledger(path, header, rounds)
    print("round %d: finding recorded" % entry["number"])
    return OK


def cmd_merged(args):
    path, header, rounds = load(args.ledger_dir, args.task_id)
    if not rounds:
        print("refused: no round is open for %s" % args.task_id, file=sys.stderr)
        return REFUSED
    entry = rounds[-1]
    entry["fields"]["Fix rows merged"] = append_item(
        entry["fields"].get("Fix rows merged"), args.fix_row)
    write_ledger(path, header, rounds)
    print("round %d: %s marked merged" % (entry["number"], args.fix_row))
    return OK


def cmd_stop(args):
    path, header, rounds = load(args.ledger_dir, args.task_id)
    if not rounds:
        print("refused: no round is open for %s" % args.task_id, file=sys.stderr)
        return REFUSED
    entry = rounds[-1]
    entry["fields"]["Stop reason"] = args.reason
    write_ledger(path, header, rounds)
    print("round %d: stop reason recorded" % entry["number"])
    return OK


def cmd_show(args):
    path = ledger_path(args.ledger_dir, args.task_id)
    text = read_ledger(path)
    if not text:
        print("no ledger for %s at %s" % (args.task_id, path), file=sys.stderr)
        return REFUSED
    sys.stdout.write(text)
    return OK


OK = 0
REFUSED = 1
USAGE = 2


def main(argv):
    parser = argparse.ArgumentParser(
        prog="ledger.py",
        description="Track the bounded QA/fix rounds of one board row.")
    parser.add_argument("--ledger-dir", default="docs/reviews",
                        help="directory that holds the ledger files (default: docs/reviews)")
    sub = parser.add_subparsers(dest="command")

    for name, help_text in (
            ("status", "print the round state of the ledger"),
            ("next-round", "open the next round; refused when the cap is reached"),
            ("show", "print the ledger file")):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--task-id", required=True)

    p = sub.add_parser("finding", help="record a finding and its Fix row in the open round")
    p.add_argument("--task-id", required=True)
    p.add_argument("--fingerprint", required=True)
    p.add_argument("--evidence")
    p.add_argument("--fix-row")

    p = sub.add_parser("merged", help="record a Fix row as merged in the open round")
    p.add_argument("--task-id", required=True)
    p.add_argument("--fix-row", required=True)

    p = sub.add_parser("stop", help="record the stop reason of the open round")
    p.add_argument("--task-id", required=True)
    p.add_argument("--reason", required=True)

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return USAGE
    handler = {
        "status": cmd_status,
        "next-round": cmd_next_round,
        "finding": cmd_finding,
        "merged": cmd_merged,
        "stop": cmd_stop,
        "show": cmd_show,
    }[args.command]
    return handler(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
