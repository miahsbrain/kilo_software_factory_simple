#!/usr/bin/env python3
"""ledger.py — the bounded QA/fix ledger for one board row.

One ignored file per row, artifacts/reviews/<task-id>-ledger.md, carries the state
between rounds: the round number, the findings filed in that round, the Fix
row IDs created, the Fix rows merged since, and the stop reason when it stops.

A row may go through at most 3 rounds. `next-round` refuses to open round 4;
unresolved blockers require a human decision, not an automatic extension.

Usage:
  ledger.py artifact-root [artifacts/path]
  ledger.py [--ledger-dir <directory>] status --task-id BOARD-005
  ledger.py next-round  --task-id BOARD-005
  ledger.py finding     --task-id BOARD-005 --fingerprint "kind|category|route|subject"
                         [--evidence <path>] [--fix-row BOARD-010]
  ledger.py merged      --task-id BOARD-005 --fix-row BOARD-010
  ledger.py stop        --task-id BOARD-005 --reason "..."
  ledger.py show        --task-id BOARD-005

Exit codes: 0 ok, 1 refused, 2 usage error.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

MAX_ROUNDS = 3
FIELDS = ("Findings", "Fix rows", "Fix rows merged", "Stop reason")
ROUND_RE = re.compile(r"^## Round (\d+)\s*$")


def ledger_path(ledger_dir, task_id):
    if not re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9._-]*", task_id):
        raise ValueError("task-id must be a safe path segment")
    return os.path.join(ledger_dir, "%s-ledger.md" % task_id)


def git(cwd, *args):
    result = subprocess.run(['git', *args], cwd=cwd, capture_output=True,
                            env={k: v for k, v in os.environ.items() if not k.startswith('GIT_')})
    if result.returncode:
        if args[0] == 'check-ignore' and result.returncode == 1:
            raise ValueError(f'{args[-1]} is not ignored in {cwd}')
        raise ValueError(f'git {args[0]} failed in {cwd}: {os.fsdecode(result.stderr).strip()}')
    return os.fsdecode(result.stdout)


def primary_checkout(cwd):
    top = Path(git(cwd, 'rev-parse', '--show-toplevel').removesuffix('\n'))
    entries = git(cwd, 'worktree', 'list', '--porcelain', '-z').split('\0\0')
    roots = [entry.split('\0', 1)[0].removeprefix('worktree ') for entry in entries if entry]
    if not roots or str(top) not in roots or (top / '.git').is_symlink():
        raise ValueError('cannot resolve primary checkout')
    root = Path(roots[0])
    if (not root.is_absolute() or root.resolve(strict=True) != root or (root / '.git').is_symlink() or
            git(root, 'rev-parse', '--show-toplevel').removesuffix('\n') != str(root) or
            git(cwd, 'rev-parse', '--path-format=absolute', '--git-common-dir') !=
            git(root, 'rev-parse', '--path-format=absolute', '--git-common-dir')):
        raise ValueError('primary Git identity mismatch')
    return root


def artifact_owner(cwd):
    primary = primary_checkout(cwd)
    # Primary ancestry also works for linked service worktrees outside the project.
    # Installed control tooling can identify an explicitly mapped external service.
    visited = set()
    for start in (primary, Path(cwd), Path(__file__).absolute().parents[4]):
        for candidate in (start, *start.parents):
            if candidate in visited:
                continue
            visited.add(candidate)
            board = candidate / 'docs/BOARD.md'
            mapping = candidate / '.claude/repos.json'
            if not (os.path.lexists(board) and os.path.lexists(mapping)):
                continue
            if board.resolve() != board or mapping.resolve() != mapping or not board.is_file() or not mapping.is_file():
                raise ValueError('control board and repo map must be regular files without symlinks')
            if primary_checkout(candidate) != candidate:
                continue  # A linked checkout or ordinary subdirectory is not an owner.
            repos = json.loads(mapping.read_text(encoding='utf-8'))
            if not isinstance(repos, dict) or repos.get('control') != '.':
                raise ValueError('invalid control repo map')
            for value in repos.values():
                if not isinstance(value, str) or not value or '..' in Path(value).parts:
                    raise ValueError('invalid mapped repository path')
            if primary in (candidate / value for value in repos.values()):
                return candidate
    raise ValueError('no primary control board and repo map mapping the caller')


def artifact_path(path='artifacts', cwd=None, *, reviews_only=False):
    owner = artifact_owner(cwd or os.getcwd())
    root = owner / 'artifacts'
    target = owner / path
    if not target.is_relative_to(root) or '..' in target.parts or '.git' in target.relative_to(owner).parts:
        raise ValueError('output must stay inside primary control artifacts/')
    if reviews_only and not target.is_relative_to(root / 'reviews'):
        raise ValueError('manual guide must be under artifacts/reviews/')
    if target.resolve() != target:
        raise ValueError('artifact output has a symlink ancestor or destination')
    if root.exists() and not root.is_dir():
        raise ValueError('artifacts/ must be a directory')
    directory = target
    while not directory.is_dir():
        directory = directory.parent
    if git(directory, 'rev-parse', '--show-toplevel').removesuffix('\n') != str(owner):
        raise ValueError('artifact belongs to a nested repository')
    if (git(owner, 'ls-files', '--cached', '--', 'artifacts') or
            git(owner, 'diff', '--cached', '--name-only', '--no-renames', '--', 'artifacts')):
        raise ValueError('artifacts/ contains tracked or staged paths')
    git(owner, 'check-ignore', '-q', '--', 'artifacts/')
    if git(owner, 'ls-files', '--others', '--exclude-standard', '--', 'artifacts'):
        raise ValueError('artifacts/ contains nonignored paths')
    if target != root:
        git(owner, 'check-ignore', '-q', '--', str(target.relative_to(owner)))
    return str(target)


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
    except FileNotFoundError:
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
        print("No round 4 or ledger reset. If round 3 has unresolved blocking findings, "
              "highlight remaining problems, severity, user impact, evidence and attempted fixes; "
              "record the stop reason with 'stop', request Blocked status from the orchestrator, "
              "and ask the user how to proceed (through the orchestrator when delegated). "
              "Offer a revised approach, defer/drop, or explicitly scoped follow-up. "
              "A successful round 3 does not imply blockers or require Blocked status.",
              file=sys.stderr)
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
    parser.add_argument("--ledger-dir",
                        help="directory inside primary control artifacts/, relative to that checkout; "
                             "default: artifacts/reviews")
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser('artifact-root', help='print the verified absolute primary control artifact path')
    p.add_argument('target', nargs='?', default='artifacts', help='optional path within primary artifacts/')

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
    handlers = {
        "status": cmd_status,
        "next-round": cmd_next_round,
        "finding": cmd_finding,
        "merged": cmd_merged,
        "stop": cmd_stop,
        "show": cmd_show,
    }
    try:
        if args.command == 'artifact-root':
            if args.ledger_dir is not None:
                raise ValueError('artifact-root does not accept --ledger-dir')
            print(artifact_path(args.target))
            return OK
        path = ledger_path(args.ledger_dir or 'artifacts/reviews', args.task_id)
        args.ledger_dir = os.path.dirname(artifact_path(path))
        return handlers[args.command](args)
    except (OSError, ValueError, RuntimeError) as error:
        print("refused: %s" % error, file=sys.stderr)
        return REFUSED


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
