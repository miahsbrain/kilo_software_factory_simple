#!/usr/bin/env python3
"""Provision the local env files into a worktree.

    env.py sync --board BOARD-00X [--repo <id>]
    env.py sync --worktree <path>
    env.py status --board BOARD-00X [--repo <id>]
    env.py clean --board BOARD-00X [--repo <id>] [--apply]

sync copies .env and .env.local from the repository's main checkout into a
worktree under .opencode/worktrees/. Nothing else travels. The contents are never
printed: the script reports the file name and the byte count, never a value.

The copies are listed in the repository's .git/info/exclude, so they can never
be committed. The agent's own read policy on env files stays denied: the app
reads the file, the agent runs the app.

A destination that does not resolve under <repo>/.opencode/worktrees/ is refused.
clean removes the copies from the worktree and nothing else, and is a dry run
without --apply.

Exit codes: 0 ok, 1 refusal, 2 usage error, 66 invalid input.
"""
import argparse
import errno
import importlib.util
import os
import stat
import sys
import tempfile

ENV_NAMES = (".env", ".env.local")
WORKTREES_DIR = os.path.join(".opencode", "worktrees")
EXCLUDE_MARKER = "# env files provisioned into worktrees by the factory; never committed"

OK = 0
REFUSED = 1
USAGE = 2
INVALID = 66

_MODULE = None


def worktree_module():
    """The sibling worktree.py, loaded by path so it works from anywhere."""
    global _MODULE
    if _MODULE is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "worktree.py")
        spec = importlib.util.spec_from_file_location("worktree", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _MODULE = module
    return _MODULE


def inside_worktrees(path, repo_root):
    """True when the path resolves under <repo_root>/.opencode/worktrees/."""
    base = os.path.realpath(os.path.join(repo_root, WORKTREES_DIR))
    real = os.path.realpath(path)
    return (real.startswith(base + os.sep) and
            os.path.abspath(path).startswith(os.path.abspath(os.path.join(repo_root, WORKTREES_DIR)) + os.sep) and
            os.path.isdir(path) and not os.path.islink(path))


def read_text(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def resolve_target(board_id, repo_id, cwd):
    """(info, error). info holds the worktree path, its branch and the repo root."""
    wt = worktree_module()
    control = wt.control_root(cwd)
    board = wt.load_board_module(wt.script_root())
    if board is None:
        return None, "the board script is missing"
    board_file = os.path.join(control, "docs", "BOARD.md")
    table, err = board.read_table(board_file)
    if table is None:
        return None, err
    index = board.row_by_id(table, board_id)
    if index is None:
        return None, "no row with ID %s on the board" % board_id
    repos, err = wt.load_repos(control)
    if repos is None:
        return None, err
    repo_id = repo_id or "control"
    repo_root, err = wt.resolve_repo(control, repos, repo_id)
    if err:
        return None, err
    cells = board.cell_texts(table["lines"], index)
    column = board.field_index(table, "branch-worktree")
    cell_text = cells[column] if column is not None and len(cells) > column else ""
    path, branch = recorded_worktree(cell_text, control, repo_root)
    if not path:
        return None, "row %s has no live worktree in %s" % (board_id, repo_root)
    return {"path": path, "branch": branch, "repo": repo_root}, None


def recorded_worktree(cell_text, control, repo_root):
    """(path, branch) of the row's live worktree inside the repository, or (None, None)."""
    wt = worktree_module()
    for absolute, branch in wt.row_worktrees(cell_text, control):
        if not os.path.isdir(absolute):
            continue
        if not inside_worktrees(absolute, repo_root):
            continue
        return absolute, branch
    return None, None


def source_root(repo_root):
    """The repository's main checkout, the only place the env files are read from."""
    return worktree_module().main_checkout_root(repo_root)


def exclude_path(repo_root):
    """The repository's local exclude file, the one shared by every worktree."""
    common = worktree_module().common_dir(repo_root)
    if not common:
        return None
    return os.path.join(common, "info", "exclude")


def ensure_excluded(repo_root):
    """(path, error). The env files are listed under a marker comment."""
    path = exclude_path(repo_root)
    if not path:
        return None, "cannot find the repository's common git directory"
    existing = read_text(path)
    if existing is None:
        existing = ""
    lines = [line.strip() for line in existing.splitlines()]
    missing = [name for name in ENV_NAMES if name not in lines]
    if not missing:
        return path, None
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            if existing and not existing.endswith("\n"):
                fh.write("\n")
            if EXCLUDE_MARKER not in existing:
                fh.write("\n%s\n" % EXCLUDE_MARKER)
            for name in missing:
                fh.write("%s\n" % name)
    except OSError as e:
        return None, "cannot update %s: %s" % (path, e.strerror)
    return path, None


def write_file(dst, data):
    """Publish a 0600 copy atomically; never follow or replace a planted link."""
    fd, temp = tempfile.mkstemp(prefix=".factory-env-", dir=os.path.dirname(dst))
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        if os.path.lexists(dst) and not stat.S_ISREG(os.lstat(dst).st_mode):
            raise OSError(errno.EINVAL, "unsafe existing destination")
        os.replace(temp, dst)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def sync_into(worktree_path, repo_root):
    """(lines, error). Copies the env files into the worktree and excludes them."""
    if not inside_worktrees(worktree_path, repo_root):
        return None, ("refused: %s is not under %s" %
                      (worktree_path, os.path.join(repo_root, WORKTREES_DIR)))
    source = source_root(repo_root)
    if os.path.realpath(source) != os.path.realpath(repo_root):
        return None, "refused: env source is not the repository main checkout"
    sources = {}
    for name in ENV_NAMES:
        src = os.path.join(source, name)
        dst = os.path.join(worktree_path, name)
        if os.path.lexists(src):
            if not stat.S_ISREG(os.lstat(src).st_mode):
                return None, "refused: %s source is not a regular file" % name
            sources[name] = src
        if os.path.lexists(dst) and not stat.S_ISREG(os.lstat(dst).st_mode):
            return None, "refused: %s destination is not a regular file" % name
        code, _, _ = worktree_module().git(repo_root, "ls-files", "--error-unmatch", "--", name)
        if code == 0:
            return None, "refused: %s is tracked; cannot provision or overwrite" % name
    path, err = ensure_excluded(repo_root)
    if err:
        return None, err
    lines = []
    for name in ENV_NAMES:
        dst = os.path.join(worktree_path, name)
        if name not in sources:
            lines.append("%s: no file in the main checkout" % name)
            continue
        try:
            fd = os.open(sources[name], os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            with os.fdopen(fd, "rb") as fh:
                data = fh.read()
            write_file(dst, data)
        except OSError as e:
            return None, "cannot copy %s: %s" % (name, e.strerror or "I/O failure")
        lines.append("%s: copied (%d bytes)" % (name, os.path.getsize(dst)))
    lines.append("excluded in %s" % path)
    return lines, None


def status_into(worktree_path, repo_root):
    """(lines, error). Per file: whether the source and the copy exist."""
    source = source_root(repo_root)
    lines = []
    for name in ENV_NAMES:
        src = os.path.join(source, name)
        dst = os.path.join(worktree_path, name)
        lines.append("%s | main checkout: %s | worktree: %s" %
                     (name,
                      "present" if os.path.isfile(src) else "absent",
                      "present" if os.path.isfile(dst) else "absent"))
    return lines, None


def clean_into(worktree_path, repo_root, apply):
    """(lines, error). Removes the copies from the worktree and nothing else."""
    if not inside_worktrees(worktree_path, repo_root):
        return None, ("refused: %s is not under %s" %
                      (worktree_path, os.path.join(repo_root, WORKTREES_DIR)))
    lines = []
    for name in ENV_NAMES:
        dst = os.path.join(worktree_path, name)
        if not os.path.exists(dst):
            lines.append("%s: nothing to remove" % name)
            continue
        if not apply:
            lines.append("%s: would remove" % name)
            continue
        try:
            os.unlink(dst)
        except OSError as e:
            return None, "cannot remove %s: %s" % (dst, e.strerror)
        lines.append("%s: removed" % name)
    return lines, None


def cmd_sync(args, cwd):
    if args.worktree:
        path = os.path.abspath(args.worktree)
        wt = worktree_module()
        repo_root = wt.repo_of_path(path)
        if not repo_root:
            print("refused: %s is not inside a git repository" % path, file=sys.stderr)
            return REFUSED
    else:
        info, err = resolve_target(args.board, args.repo, cwd)
        if err:
            print(err, file=sys.stderr)
            return REFUSED
        path, repo_root = info["path"], info["repo"]
    lines, err = sync_into(path, repo_root)
    if err:
        print(err, file=sys.stderr)
        return REFUSED
    print("worktree: %s" % path)
    for line in lines:
        print("env: %s" % line)
    return OK


def cmd_status(args, cwd):
    info, err = resolve_target(args.board, args.repo, cwd)
    if err:
        print(err, file=sys.stderr)
        return REFUSED
    lines, err = status_into(info["path"], info["repo"])
    if err:
        print(err, file=sys.stderr)
        return REFUSED
    print("worktree: %s" % info["path"])
    for line in lines:
        print(line)
    return OK


def cmd_clean(args, cwd):
    info, err = resolve_target(args.board, args.repo, cwd)
    if err:
        print(err, file=sys.stderr)
        return REFUSED
    lines, err = clean_into(info["path"], info["repo"], args.apply)
    if err:
        print(err, file=sys.stderr)
        return REFUSED
    print("worktree: %s" % info["path"])
    for line in lines:
        print("env: %s" % line)
    if not args.apply:
        print("dry run; re-run with --apply to act")
    return OK


def main(argv):
    parser = argparse.ArgumentParser(
        prog="env.py", description="Provision the local env files into a worktree.")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("sync", help="copy the env files into a worktree")
    p.add_argument("--board", help="board row ID, e.g. BOARD-00X")
    p.add_argument("--worktree", help="path of the worktree")
    p.add_argument("--repo", help="repo id from .opencode/repos.json (default: control)")

    p = sub.add_parser("status", help="report whether the env files are present")
    p.add_argument("--board", required=True, help="board row ID, e.g. BOARD-00X")
    p.add_argument("--repo", help="repo id from .opencode/repos.json (default: control)")

    p = sub.add_parser("clean", help="remove the env copies from a worktree")
    p.add_argument("--board", required=True, help="board row ID, e.g. BOARD-00X")
    p.add_argument("--repo", help="repo id from .opencode/repos.json (default: control)")
    p.add_argument("--apply", action="store_true", help="act; without it this is a dry run")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return USAGE
    if args.command == "sync" and not args.board and not args.worktree:
        print("sync needs --board or --worktree", file=sys.stderr)
        return USAGE
    cwd = os.getcwd()
    if args.command == "sync":
        return cmd_sync(args, cwd)
    if args.command == "status":
        return cmd_status(args, cwd)
    if args.command == "clean":
        return cmd_clean(args, cwd)
    parser.print_help()
    return USAGE


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception as exc:
        print("env.py error: %s" % exc, file=sys.stderr)
        sys.exit(REFUSED)
