#!/usr/bin/env python3
"""Deterministic git worktree lifecycle for this factory.

    worktree.py create --board BOARD-00X [--base main] [--slug <override>]
    worktree.py list
    worktree.py verify <slug> [--base main]
    worktree.py cleanup <slug> [--apply]

create reads the board row named by --board from docs/BOARD.md, derives the
branch type from its Type column and the slug from its task title, then makes
.kilo/worktrees/<slug> on branch <type>/<slug> and records the worktree on the
row. It never overwrites: an existing branch or directory is a refusal.

verify reports branch, commits ahead of base, changed files and dirty state,
and exits 0 only when the tree is clean and the branch has at least one commit
ahead of base.

cleanup is a dry run by default. --apply removes the worktree and deletes the
branch, but refuses when the branch has commits that are not reachable from the
base or when the worktree is dirty. Unmerged work is never deleted. Every run
writes a recovery TSV to <git-common-dir>/cleanup-wt/<timestamp>.tsv.

Exit codes: 0 ok, 1 refusal, 2 usage error, 66 invalid input.
"""
import argparse
import datetime
import importlib.util
import os
import re
import subprocess
import sys

TYPE_MAP = {"Feature": "feat", "Fix": "fix", "Chore": "chore", "Docs": "docs",
            "Research": "chore"}
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
WORKTREES_DIR = os.path.join(".kilo", "worktrees")
MAX_SLUG_LEN = 48
STATUS_INDEX = 3
BRANCH_INDEX = 7

OK = 0
REFUSED = 1
USAGE = 2
INVALID = 66


def git(cwd, *args, timeout=60):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        r = subprocess.run(["git", "-C", cwd] + list(args), capture_output=True, text=True,
                           env=env, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, "", str(e)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def git_out(cwd, *args):
    code, out, _ = git(cwd, *args)
    return out if code == 0 else None


def repo_root(cwd):
    """The main checkout's root, from it or from any linked worktree."""
    top = git_out(cwd, "rev-parse", "--show-toplevel")
    if not top:
        return None
    marker = os.sep + WORKTREES_DIR.replace(os.sep, os.sep) + os.sep
    at = top.find(marker)
    return top if at == -1 else top[:at]


def main_checkout_root(cwd):
    """The main working tree of the repository, from it or from any linked worktree."""
    out = git_out(cwd, "worktree", "list", "--porcelain") or ""
    for line in out.splitlines():
        key, _, value = line.partition(" ")
        if key == "worktree" and value:
            return os.path.abspath(value)
    return script_root()


def script_root():
    """The repo root that holds this script, whatever the cwd is."""
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "..", "..", "..", ".."))


def load_board_module(root):
    """The sibling board.py, loaded by path so it works from anywhere."""
    path = os.path.join(root, ".kilo", "skills", "board", "scripts", "board.py")
    if not os.path.exists(path):
        print("board script not found: %s" % path, file=sys.stderr)
        return None
    spec = importlib.util.spec_from_file_location("board", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TRAILING_STOPWORDS = {
    "with", "and", "or", "but", "for", "from", "to", "of", "in", "on", "at", "by", "as",
    "that", "which", "the", "a", "an", "is", "are", "was", "were", "be", "been", "it", "its",
    "this", "these", "those", "then", "into", "over", "via", "per",
}


def drop_trailing_stopwords(slug):
    """The slug without the connective words it ends on, never below one word."""
    words = slug.split("-")
    while len(words) > 1 and words[-1] in TRAILING_STOPWORDS:
        words.pop()
    return "-".join(words)


def slugify(title):
    """The kebab-case slug of a board task title."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if len(slug) > MAX_SLUG_LEN:
        slug = drop_trailing_stopwords("-".join(slug.split("-")[:6]))
    return slug


def common_dir(cwd):
    out = git_out(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if not out:
        out = git_out(cwd, "rev-parse", "--git-common-dir")
    return os.path.abspath(out) if out else None


def list_worktrees(cwd):
    out = git_out(cwd, "worktree", "list", "--porcelain") or ""
    wts = []
    for block in out.split("\n\n"):
        wt = {"path": "", "head": "", "branch": None, "bare": False}
        for line in block.splitlines():
            key, _, val = line.partition(" ")
            if key == "worktree":
                wt["path"] = val
            elif key == "HEAD":
                wt["head"] = val
            elif key == "branch":
                wt["branch"] = val[len("refs/heads/"):] if val.startswith("refs/heads/") else val
            elif key == "bare":
                wt["bare"] = True
        if wt["path"]:
            wts.append(wt)
    return wts


def slug_of(path, root):
    marker = os.sep + WORKTREES_DIR + os.sep
    at = path.find(marker)
    if at == -1:
        return os.path.basename(path)
    rest = path[at + len(marker):]
    return rest.split(os.sep)[0]


def worktree_path(root, slug):
    return os.path.join(root, WORKTREES_DIR, slug)


def find_worktree(cwd, slug):
    for wt in list_worktrees(cwd):
        if slug_of(wt["path"], None) == slug:
            return wt
    return None


def board_row(board, path, board_id):
    table, err = board.read_table(path)
    if table is None:
        print(err, file=sys.stderr)
        return None, None
    index = board.row_by_id(table, board_id)
    if index is None:
        print("no row with ID %s on the board; add it first with "
              "'board.py add --id %s --task \"...\"' (rule: every task gets a board row "
              "before its worktree exists)" % (board_id, board_id), file=sys.stderr)
        return None, None
    return table, index


def cmd_create(args, cwd):
    root = main_checkout_root(cwd)
    git_root = cwd
    board = load_board_module(script_root())
    if board is None:
        return REFUSED
    board_file = os.path.join(root, "docs", "BOARD.md")
    table, index = board_row(board, board_file, args.board)
    if table is None:
        return REFUSED
    cells = board.cell_texts(table["lines"], index)
    if len(cells) < 3:
        print("row %s is malformed: %d cells" % (args.board, len(cells)), file=sys.stderr)
        return REFUSED
    task, row_type = cells[1], cells[2]
    branch_type = TYPE_MAP.get(row_type)
    if branch_type is None:
        print("row %s has Type %r; allowed types are %s" %
              (args.board, row_type,
               ", ".join("%s -> %s" % (k, v) for k, v in TYPE_MAP.items())),
              file=sys.stderr)
        return INVALID
    derived = slugify(task)
    if not derived:
        print("row %s has an empty task title; the task title needs a real name" % args.board,
              file=sys.stderr)
        return INVALID
    slug = args.slug or derived
    if not SLUG_RE.match(slug):
        print("invalid slug %r: use kebab-case, e.g. user-login" % slug, file=sys.stderr)
        return INVALID
    if args.slug and args.slug != derived:
        print("derived slug: %s" % derived)
        print("used slug:    %s" % slug)
    branch = "%s/%s" % (branch_type, slug)
    if git_out(git_root, "rev-parse", "-q", "--verify", "refs/heads/" + branch):
        print("branch %s already exists; pick another slug or type" % branch, file=sys.stderr)
        return REFUSED
    path = worktree_path(root, slug)
    if os.path.exists(path):
        print("directory %s already exists; refusing to overwrite it" % path, file=sys.stderr)
        return REFUSED
    if not git_out(git_root, "rev-parse", "-q", "--verify", "refs/heads/" + args.base):
        print("base branch %s does not exist" % args.base, file=sys.stderr)
        return REFUSED
    code, _, err = git(git_root, "worktree", "add", path, "-b", branch, args.base)
    if code != 0:
        print("git worktree add failed: %s" % (err.splitlines() or ["?"])[-1], file=sys.stderr)
        return REFUSED
    try:
        lines = list(table["lines"])
        lines[index] = board.replace_cell(lines[index], BRANCH_INDEX,
                                          "%s · branch %s" % (os.path.join(WORKTREES_DIR, slug),
                                                              branch))
        lines[index] = board.replace_cell(lines[index], STATUS_INDEX, "In Progress")
        board.write_atomic(board_file, lines)
    except Exception as exc:
        print("warning: worktree %s exists but row %s was not updated (%s)" %
              (path, args.board, exc), file=sys.stderr)
        return REFUSED
    print("board:    %s" % args.board)
    print("board file: %s" % board_file)
    print("task:     %s" % task)
    print("branch:   %s" % branch)
    print("worktree: %s" % os.path.abspath(path))
    print("base:     %s" % args.base)
    return OK


def cmd_list(args, cwd):
    root = repo_root(cwd)
    if not root:
        print("not inside a git repository", file=sys.stderr)
        return REFUSED
    wts = list_worktrees(cwd)
    main = os.path.realpath(wts[0]["path"]) if wts else os.path.realpath(root)
    for wt in wts:
        path = os.path.abspath(wt["path"])
        kind = "main" if os.path.realpath(path) == main else "linked"
        print("%s | %s | %s | %s | %s" % (slug_of(path, root), path,
                                         wt["branch"] or "(detached)", wt["head"], kind))
    return OK


def cmd_verify(args, cwd):
    root = repo_root(cwd)
    if not root:
        print("not inside a git repository", file=sys.stderr)
        return REFUSED
    wt = find_worktree(cwd, args.slug)
    if not wt:
        print("no worktree with slug %s" % args.slug, file=sys.stderr)
        return REFUSED
    path = wt["path"]
    branch = wt["branch"] or "(detached)"
    ahead = git_out(path, "log", "--oneline", "%s..HEAD" % args.base) or ""
    changed = git_out(path, "diff", "--stat", args.base) or ""
    dirty = git_out(path, "status", "--short") or ""

    print("worktree: %s" % os.path.abspath(path))
    print("branch:   %s" % branch)
    print("base:     %s" % args.base)
    print("commits ahead of base:")
    print(ahead if ahead else "  (none)")
    print("changed files:")
    print(changed if changed else "  (none)")
    print("dirty state:")
    print(dirty if dirty else "  (clean)")

    if dirty:
        print("NOT READY: the worktree has uncommitted changes")
        return REFUSED
    if not ahead:
        print("NOT READY: no commit ahead of %s" % args.base)
        return REFUSED
    print("READY FOR MERGE: clean tree, %d commit(s) ahead of %s" % (len(ahead.splitlines()), args.base))
    return OK


def recovery_tsv(common, rows):
    stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    path = os.path.join(common, "cleanup-wt", stamp + ".tsv")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write("when\tkind\tname\tsha\tpath\taction\treason\n")
        for r in rows:
            fh.write("\t".join(str(r[k]) for k in
                                ("when", "kind", "name", "sha", "path", "action", "reason")) + "\n")
    return path


def cmd_cleanup(args, cwd):
    root = repo_root(cwd)
    if not root:
        print("not inside a git repository", file=sys.stderr)
        return REFUSED
    wt = find_worktree(cwd, args.slug)
    if not wt:
        print("no worktree with slug %s" % args.slug, file=sys.stderr)
        return REFUSED
    path = wt["path"]
    branch = wt["branch"]
    sha = wt["head"]
    common = common_dir(cwd)
    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")

    dirty = git_out(path, "status", "--short") or ""
    unmerged = git_out(path, "log", "--oneline", "%s..%s" % (args.base, branch)) if branch else None
    reason = None
    if dirty:
        reason = "worktree is dirty; uncommitted work would be lost"
    elif not branch:
        reason = "worktree has a detached HEAD; no branch to delete"
    elif unmerged:
        reason = "branch %s has %d commit(s) not reachable from %s" % (
            branch, len(unmerged.splitlines()), args.base)

    actions = []
    if reason is None:
        actions = [("worktree", branch or "(detached)", sha, path, "remove-worktree",
                    "merged into %s and clean" % args.base),
                   ("branch", branch, sha, path, "delete-branch",
                    "merged into %s" % args.base)]

    rows = [{"when": now, "kind": k, "name": n, "sha": s, "path": p,
             "action": (a if args.apply else "would-" + a), "reason": r}
            for k, n, s, p, a, r in actions]
    if reason is not None:
        rows.append({"when": now, "kind": "worktree", "name": branch or "(detached)", "sha": sha,
                     "path": path, "action": "keep", "reason": reason})
    tsv = recovery_tsv(common, rows) if common else None

    print("worktree: %s" % os.path.abspath(path))
    print("branch:   %s" % (branch or "(detached)"))
    if reason is not None:
        print("refused: %s" % reason)
        print("no work was deleted")
        if tsv:
            print("recovery TSV: %s" % tsv)
        return REFUSED

    print("plan:")
    for k, n, s, p, a, r in actions:
        print("  %s %s (%s) - %s" % (a, n, p, r))

    if not args.apply:
        print("dry run; re-run with --apply to act")
        if tsv:
            print("recovery TSV: %s" % tsv)
        return OK

    done = []
    code, _, err = git(root, "worktree", "remove", path)
    if code != 0:
        print("worktree remove failed: %s" % (err.splitlines() or ["?"])[-1], file=sys.stderr)
        print("recovery TSV: %s" % tsv)
        return REFUSED
    done.append("removed worktree " + path)
    code, _, err = git(root, "branch", "-D", branch)
    if code == 0:
        done.append("deleted branch " + branch)
    else:
        done.append("kept branch %s: %s" % (branch, (err.splitlines() or ["?"])[-1]))
    for d in done:
        print(d)
    print("recovery TSV: %s" % tsv)
    return OK


def main(argv):
    parser = argparse.ArgumentParser(
        prog="worktree.py", description="Deterministic git worktree lifecycle.")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("create", help="create a worktree named from a board row")
    p.add_argument("--board", required=True, help="board row ID, e.g. BOARD-00X")
    p.add_argument("--base", default="main", help="base branch (default: main)")
    p.add_argument("--slug", help="override the slug derived from the task title")

    sub.add_parser("list", help="list worktrees")

    p = sub.add_parser("verify", help="check whether a worktree is ready to merge")
    p.add_argument("slug")
    p.add_argument("--base", default="main", help="base branch (default: main)")

    p = sub.add_parser("cleanup", help="remove a merged worktree and its branch")
    p.add_argument("slug")
    p.add_argument("--apply", action="store_true", help="act; without it this is a dry run")
    p.add_argument("--base", default="main", help="base branch (default: main)")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return USAGE
    cwd = os.getcwd()
    if args.command == "create":
        return cmd_create(args, cwd)
    if args.command == "list":
        return cmd_list(args, cwd)
    if args.command == "verify":
        return cmd_verify(args, cwd)
    if args.command == "cleanup":
        return cmd_cleanup(args, cwd)
    parser.print_help()
    return USAGE


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception as exc:
        print("worktree.py error: %s" % exc, file=sys.stderr)
        sys.exit(REFUSED)
