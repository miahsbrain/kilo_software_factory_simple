#!/usr/bin/env python3
"""Deterministic git worktree lifecycle for this factory.

    worktree.py create --board BOARD-00X [--base main] [--slug <override>] [--repo <id>]
    worktree.py resume --board BOARD-00X
    worktree.py discard --board BOARD-00X [--apply] [--force] [--yes]
    worktree.py handoff --board BOARD-00X
    worktree.py list
    worktree.py verify <slug> [--base main]
    worktree.py cleanup <slug> [--apply]
    worktree.py cleanup --board BOARD-00X [--apply]

create reads the board row named by --board from docs/BOARD.md, derives the
branch type from its Type column and the slug from its task title, then makes
.opencode/worktrees/<slug> on branch <type>/<slug> and records the worktree on the
row. It never overwrites: an existing branch or directory is a refusal. When
the row already has a live worktree, create refuses and names the three ways
forward: resume, discard, or a new slug.

resume reuses the live worktree of a row and puts the row back in progress.
discard removes it, and refuses while it is dirty or holds commits that the
base does not have. Both write a recovery TSV like cleanup does.

discard --board puts the row back in Ready and clears its worktree cell once
the worktree is gone; cleanup --board puts the row in Merged and clears the
cell. A refusal changes nothing on the board, and the slug form of cleanup
touches nothing there.

discard --force relaxes that refusal in two steps: --force alone prints the
destruction plan and never acts, and --force --yes acts after writing a
recovery copy — the uncommitted changes as a patch, and the lost commit shas
in the recovery TSV, both under <git-common-dir>/cleanup-wt/.

handoff prints review commands for a row. Merge guidance requires Pending Merge,
a clean worktree and committed work ahead of base; failed checks refuse guidance.
It never changes anything.

--repo picks the repository the worktree is created in. The id comes from
.opencode/repos.json in the control repo; the default is "control", the control
repo itself. The board stays in the control repo; the worktree is created in
the target repo, under that repo's own .opencode/worktrees/.

verify reports branch, commits ahead of base, changed files and dirty state,
and exits 0 only when the tree is clean and the branch has at least one commit
ahead of base.

cleanup is a dry run by default. --apply removes the worktree and deletes the
branch, but refuses when the branch has commits that are not reachable from the
base or when the worktree is dirty. Unmerged work is never deleted. Every run
writes a recovery TSV to <git-common-dir>/cleanup-wt/<timestamp>.tsv.

cleanup takes the worktree either as a slug or as the board row that owns it:
cleanup --board BOARD-00X resolves the row's Branch/Worktree cell. Exactly one
of the two may be given.

Exit codes: 0 ok, 1 refusal, 2 usage error, 66 invalid input.
"""
import argparse
import datetime
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys

TYPE_MAP = {"Feature": "feat", "Fix": "fix", "Chore": "chore", "Docs": "docs",
            "Research": "chore"}
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
WORKTREES_DIR = os.path.join(".opencode", "worktrees")
MAX_SLUG_LEN = 48
STATUS_INDEX = 3
REPOS_REL = os.path.join(".opencode", "repos.json")
DEFAULT_REPOS = {"control": "."}

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


def git_raw(cwd, *args, timeout=60):
    """(code, stdout, stderr) with the output untouched, for content that must stay exact."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        r = subprocess.run(["git", "-C", cwd] + list(args), capture_output=True, text=True,
                           env=env, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, "", str(e)
    return r.returncode, r.stdout, r.stderr


def repo_root(cwd):
    """The main checkout's root, from it or from any linked worktree."""
    top = git_out(cwd, "rev-parse", "--show-toplevel")
    if not top:
        return None
    return main_checkout_root(cwd)


def main_checkout_root(cwd):
    """The main working tree of the repository, from it or from any linked worktree."""
    out = git_out(cwd, "worktree", "list", "--porcelain") or ""
    for line in out.splitlines():
        key, _, value = line.partition(" ")
        if key == "worktree" and value:
            return os.path.abspath(value)
    return script_root()


def control_root(cwd):
    """The control repo of the work: the repo that owns the board and the map.

    A work surface holds application code only, so running the harness from
    inside one must still find the project that governs it. The control repo
    is the nearest ancestor that holds a repo map, even before its board exists. Its main
    checkout is returned, because the board has one writer and that writer
    works in the main checkout.
    """
    path = os.path.abspath(cwd)
    found = None
    while True:
        if os.path.exists(os.path.join(path, REPOS_REL)):
            found = path
            break
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent
    if found is None:
        return main_checkout_root(cwd)
    out = git_out(found, "worktree", "list", "--porcelain") or ""
    for line in out.splitlines():
        key, _, value = line.partition(" ")
        if key == "worktree" and value:
            return os.path.abspath(value)
    return found


def script_root():
    """The repo root that holds this script, whatever the cwd is."""
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "..", "..", "..", ".."))


def load_repos(root):
    """(map, error). The map is {repo id: path relative to the control repo root}.

    The control repo's own copy wins; the tree that holds this script is the
    fallback, so a branch that adds the map works before it is merged.
    """
    candidates = [root]
    own = script_root()
    if own != root:
        candidates.append(own)
    for candidate in candidates:
        path = os.path.join(candidate, REPOS_REL)
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except OSError as e:
            return None, "cannot read %s: %s" % (path, e.strerror)
        except ValueError as e:
            return None, "cannot parse %s: %s" % (path, e)
        if not isinstance(data, dict) or not data:
            return None, "%s must hold an object of repo id -> path" % path
        repos = {}
        for key, value in data.items():
            if not isinstance(key, str) or not isinstance(value, str) or not value.strip():
                return None, "%s: entry %r must map a repo id to a path" % (path, key)
            repos[key.strip()] = value.strip()
        return repos, None
    return dict(DEFAULT_REPOS), None


def resolve_repo(root, repos, repo_id):
    """(absolute repo root, error). The map is the only way in."""
    if repo_id not in repos:
        return None, ("unknown repo id %r; known ids: %s" %
                      (repo_id, ", ".join(sorted(repos))))
    rel = repos[repo_id]
    target = os.path.abspath(os.path.join(root, rel))
    inside = target == root or target.startswith(root.rstrip(os.sep) + os.sep)
    if not os.path.isabs(rel) and not inside:
        return None, ("repo %r resolves to %s, outside the control repo %s; the map in %s "
                      "is the only way in" % (repo_id, target, root, REPOS_REL))
    return target, None


def is_git_repo(path):
    """True when the path is the top of its own git repository."""
    top = git_out(path, "rev-parse", "--show-toplevel")
    if not top:
        return False
    return os.path.realpath(top) == os.path.realpath(path)


def repo_of_path(path):
    """The main checkout root of the repository that owns this path, or None."""
    common = git_out(path, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if not common:
        return None
    common = os.path.abspath(common)
    return os.path.dirname(common) if os.path.basename(common) == ".git" else common


def default_base(target):
    """The branch a worktree in this repository should branch from.

    The factory prefers its OpenCode integration branch when present. Projects
    and application repositories retain main, origin/HEAD, then current branch.
    """
    factory = (os.path.exists(os.path.join(target, "templates", "project", "AGENTS.md"))
               and not os.path.exists(os.path.join(target, "DOMAIN.md")))
    if factory and git_out(target, "rev-parse", "-q", "--verify", "refs/heads/opencode"):
        return "opencode"
    if git_out(target, "rev-parse", "-q", "--verify", "refs/heads/main"):
        return "main"
    head = git_out(target, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if head:
        return head.split("/", 1)[1] if "/" in head else head
    current = git_out(target, "rev-parse", "--abbrev-ref", "HEAD")
    if current and current != "HEAD":
        return current
    return "main"


def resolve_base(target, requested):
    """(branch, error). An explicit request wins; otherwise the repo decides."""
    if requested:
        if not git_out(target, "rev-parse", "-q", "--verify", "refs/heads/" + requested):
            return None, ("base branch %s does not exist in %s" % (requested, target))
        return requested, None
    branch = default_base(target)
    if not git_out(target, "rev-parse", "-q", "--verify", "refs/heads/" + branch):
        return None, ("no base branch found in %s; name one with --base" % target)
    return branch, None


def parse_worktree_entries(value):
    """[(path, branch)] from a Branch/Worktree cell."""
    entries = []
    for part in (value or "").split(","):
        part = part.strip()
        if not part or part == "-":
            continue
        path, _, branch = part.partition("·")
        entries.append((path.strip(), branch.strip()))
    return entries


def branch_name(text):
    """The branch name from a cell fragment like 'branch feat/x'."""
    name = (text or "").strip()
    if name.startswith("branch "):
        name = name[len("branch "):].strip()
    return name


def row_worktrees(cell_text, root):
    """[(absolute path, branch)] of the worktrees a Branch/Worktree cell records."""
    entries = []
    for path, branch in parse_worktree_entries(cell_text):
        absolute = path if os.path.isabs(path) else os.path.join(root, path)
        entries.append((absolute, branch_name(branch)))
    return entries


def live_row_worktree(cell_text, root, repo_root):
    """(path, branch) of the row's live worktree inside a repository, or (None, None)."""
    base = os.path.realpath(os.path.join(repo_root, WORKTREES_DIR))
    for absolute, branch in row_worktrees(cell_text, root):
        if not os.path.isdir(absolute):
            continue
        if not os.path.realpath(absolute).startswith(base + os.sep):
            continue
        return absolute, branch
    return None, None


def row_of_worktree(board, root, table, path):
    """(row index, status) of the board row that records this worktree, or (None, None)."""
    index = board.field_index(table, "branch-worktree")
    if index is None:
        return None, None
    for i in table["rows"]:
        cells = board.cell_texts(table["lines"], i)
        if len(cells) <= index:
            continue
        for absolute, _ in row_worktrees(cells[index], root):
            if os.path.realpath(absolute) == os.path.realpath(path):
                return i, (cells[3] if len(cells) > 3 else "")
    return None, None


def load_board_module(root):
    """The sibling board.py, loaded by path so it works from anywhere."""
    path = os.path.join(root, ".opencode", "skills", "board", "scripts", "board.py")
    if not os.path.exists(path):
        print("board script not found: %s" % path, file=sys.stderr)
        return None
    spec = importlib.util.spec_from_file_location("board", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # The invoking script may live in the worktree being removed. Keep board
    # discovery bound to this process rather than importing that deleted path.
    module.control_root = control_root
    return module


def load_scope_module(root):
    """The sibling scope.py, loaded by path so it works from anywhere."""
    path = os.path.join(root, ".opencode", "skills", "git-worktree", "scripts", "scope.py")
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location("scope", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_env_module(root):
    """The sibling env.py, loaded by path so it works from anywhere."""
    path = os.path.join(root, ".opencode", "skills", "git-worktree", "scripts", "env.py")
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location("env", path)
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


def board_worktree(board, root, slug):
    """(path, branch) of the worktree the board row records for this slug, or (None, None)."""
    if board is None:
        return None, None
    board_file = os.path.join(root, "docs", "BOARD.md")
    if not os.path.exists(board_file):
        return None, None
    table, err = board.read_table(board_file)
    if table is None:
        return None, None
    index = board.field_index(table, "branch-worktree")
    if index is None:
        return None, None
    suffix = os.path.join(WORKTREES_DIR, slug)
    for i in table["rows"]:
        cells = board.cell_texts(table["lines"], i)
        if len(cells) <= index:
            continue
        for path, branch in parse_worktree_entries(cells[index]):
            if path.endswith(suffix):
                absolute = path if os.path.isabs(path) else os.path.join(root, path)
                if os.path.isdir(absolute):
                    return absolute, branch_name(branch)
    return None, None


def find_worktree_for_slug(board, root, slug, cwd):
    """(path, branch) of the worktree for the slug: from the board row first, then the cwd repo."""
    path, branch = board_worktree(board, root, slug)
    if path:
        return path, branch
    wt = find_worktree(cwd, slug)
    if wt:
        return wt["path"], wt["branch"]
    return None, None


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
    root = control_root(cwd)
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
    repos, err = load_repos(root)
    if repos is None:
        print(err, file=sys.stderr)
        return REFUSED
    repo_id = args.repo or "control"
    target, err = resolve_repo(root, repos, repo_id)
    if err:
        print(err, file=sys.stderr)
        return REFUSED
    if not is_git_repo(target):
        print("%s is not a git repository; the repo id %r cannot hold a worktree"
              % (target, repo_id), file=sys.stderr)
        return REFUSED
    branch_index = board.field_index(table, "branch-worktree")
    repos_index = board.field_index(table, "repos")
    if branch_index is None:
        print("the board has no Branch/Worktree column", file=sys.stderr)
        return REFUSED
    if repos_index is None and repo_id != "control":
        print("the board has no Repos column; add it with "
              "'board.py add-column --name Repos --after \"Blocked by\"'", file=sys.stderr)
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
    cell_text = cells[branch_index] if len(cells) > branch_index else ""
    confined = os.path.realpath(os.path.join(target, WORKTREES_DIR)) + os.sep
    for recorded_path, _ in row_worktrees(cell_text, root):
        if (os.path.isdir(recorded_path)
                and repo_of_path(recorded_path) == os.path.realpath(target)
                and not os.path.realpath(recorded_path).startswith(confined)):
            print("row %s records an existing worktree outside %s: %s; refusing a duplicate" %
                  (args.board, WORKTREES_DIR, recorded_path), file=sys.stderr)
            return REFUSED
    live_path, live_branch = live_row_worktree(cell_text, root, target)
    if live_path:
        print("row %s already has a live worktree: %s (branch %s)" %
              (args.board, live_path, live_branch), file=sys.stderr)
        print("pick one:", file=sys.stderr)
        print("  resume:  worktree.py resume --board %s" % args.board, file=sys.stderr)
        print("  discard: worktree.py discard --board %s --apply" % args.board, file=sys.stderr)
        return REFUSED
    existing = find_worktree(target, slug)
    if existing:
        base = os.path.realpath(os.path.join(target, WORKTREES_DIR)) + os.sep
        if not os.path.realpath(existing["path"]).startswith(base):
            existing = None
    if existing:
        other_path = existing["path"]
        other_branch = existing["branch"]
        owner_index, _ = row_of_worktree(board, root, table, other_path)
        owner = board.cell_texts(table["lines"], owner_index)[0] if owner_index is not None else None
        print("the slug directory %s is already used by another worktree (branch %s)" %
              (other_path, other_branch), file=sys.stderr)
        if owner:
            print("that worktree belongs to row %s" % owner, file=sys.stderr)
        else:
            print("no board row records that worktree", file=sys.stderr)
        print("pick one:", file=sys.stderr)
        print("  new slug: worktree.py create --board %s --slug <other-slug>" % args.board,
              file=sys.stderr)
        if owner:
            print("  discard that row's worktree: worktree.py discard --board %s --apply" % owner,
                  file=sys.stderr)
        return REFUSED
    if git_out(target, "rev-parse", "-q", "--verify", "refs/heads/" + branch):
        print("branch %s already exists in %s; pick another slug or type" %
              (branch, target), file=sys.stderr)
        print("if the row already has a worktree for it, resume it with "
              "'worktree.py resume --board %s'" % args.board, file=sys.stderr)
        return REFUSED
    path = worktree_path(target, slug)
    if os.path.exists(path):
        print("directory %s already exists; refusing to overwrite it" % path, file=sys.stderr)
        return REFUSED
    base, base_err = resolve_base(target, args.base)
    if base_err:
        print(base_err, file=sys.stderr)
        return REFUSED
    code, _, err = git(target, "worktree", "add", path, "-b", branch, base)
    if code != 0:
        print("git worktree add failed: %s" % (err.splitlines() or ["?"])[-1], file=sys.stderr)
        return REFUSED
    env_ready = provision_env(path, target)
    if not env_ready:
        print("refused: worktree created but env provisioning failed; worktree and branch remain "
              "for safe inspection. Do not create a second worktree.", file=sys.stderr)
    scope = load_scope_module(script_root())
    if scope is not None:
        content = scope.pointer_content(root, repo_id, path)
        if content:
            state, note = scope.write_pointer(path, content)
            if state == "kept":
                print("warning: %s has a hand-written AGENTS.md; left alone" % path,
                      file=sys.stderr)
            else:
                print("scope pointer: %s" % note)
        # The repository itself carries the pointer too, so a shell that sits in
        # the repository rather than in a worktree still finds the project.
        repo_content = scope.pointer_content(root, repo_id, target)
        if repo_content:
            repo_state, _ = scope.write_pointer(target, repo_content)
            if repo_state != "kept":
                print("scope pointer at the repository root: %s" % repo_state)
        scope.ensure_ignored(target)
    try:
        lines = list(table["lines"])
        rel_path = os.path.relpath(path, root).replace(os.sep, "/")
        entry = "%s · branch %s" % (rel_path, branch)
        existing = cells[branch_index] if len(cells) > branch_index else ""
        entries = parse_worktree_entries(existing)
        if not any(p == rel_path for p, _ in entries):
            entries.append((rel_path, branch))
        merged = ", ".join("%s · branch %s" % (p, branch_name(b)) for p, b in entries)
        lines[index] = board.replace_cell(lines[index], branch_index, merged)
        if repos_index is not None:
            ids = [i.strip() for i in (cells[repos_index] if len(cells) > repos_index else "").split(",")]
            ids = [i for i in ids if i and i != "-"]
            if repo_id not in ids:
                ids.append(repo_id)
            lines[index] = board.replace_cell(lines[index], repos_index, ",".join(ids))
        lines[index] = board.replace_cell(lines[index], STATUS_INDEX,
                                          "In Progress" if env_ready else "Blocked")
        board.write_atomic(board_file, lines)
    except Exception as exc:
        print("warning: worktree %s exists but row %s was not updated (%s)" %
              (path, args.board, exc), file=sys.stderr)
        return REFUSED
    if not env_ready:
        print("row %s is Blocked and records the partial worktree; fix env and resume" % args.board,
              file=sys.stderr)
        return REFUSED
    print("board:    %s" % args.board)
    print("board file: %s" % board_file)
    print("task:     %s" % task)
    print("repo:     %s (%s)" % (repo_id, target))
    print("branch:   %s" % branch)
    print("worktree: %s" % os.path.abspath(path))
    print("base:     %s" % base)
    return OK


def provision_env(path, target):
    """Copy the env files into a new worktree and report what was provisioned."""
    env = load_env_module(script_root())
    if env is None:
        print("env: not provisioned; the env script is missing", file=sys.stderr)
        return False
    lines, err = env.sync_into(path, target)
    if err:
        print("env: %s" % err, file=sys.stderr)
        return False
    for line in lines:
        print("env: %s" % line)
    return True


def commits_ahead(cwd, branch, base):
    """[sha] of the commits the base does not have."""
    if not branch:
        return []
    out = git_out(cwd, "log", "--format=%H", "%s..%s" % (base, branch)) or ""
    return [line.strip() for line in out.splitlines() if line.strip()]


def removal_state(path, branch, base):
    """(dirty lines, unmerged shas). The state a removal would destroy."""
    dirty = [line for line in (git_out(path, "status", "--short") or "").splitlines()
             if line.strip()]
    return dirty, commits_ahead(path, branch, base)


def refusal_reason(dirty, shas, branch, base):
    """Why the worktree may not be removed, or None when it may."""
    if dirty:
        return "worktree is dirty; uncommitted work would be lost"
    if not branch:
        return "worktree has a detached HEAD; no branch to delete"
    if shas:
        return "branch %s has %d commit(s) not reachable from %s" % (
            branch, len(shas), base)
    return None


def removal_refusal(path, branch, base):
    """Why the worktree may not be removed, or None when it may.

    The same checks for cleanup and for discard: a dirty tree and a branch with
    commits the base does not have both hold work that would be lost.
    """
    dirty, shas = removal_state(path, branch, base)
    return refusal_reason(dirty, shas, branch, base)


def recovery_patch(path, common, dirty, stamp):
    """(patch path, error). The uncommitted changes as a patch, or None when clean.

    Untracked files are added with intent-to-add, so `git diff HEAD` carries
    their content in the same patch.
    """
    if not dirty:
        return None, None
    if not common:
        return None, "cannot find the repository's common git directory"
    target = os.path.join(common, "cleanup-wt", stamp + ".patch")
    if not os.path.realpath(target).startswith(os.path.realpath(common) + os.sep):
        return None, "refused: the patch path %s is outside %s" % (target, common)
    _, untracked, _ = git_raw(path, "ls-files", "--others", "--exclude-standard")
    for name in [line.strip() for line in untracked.splitlines() if line.strip()]:
        git(path, "add", "-N", "--", name)
    code, out, err = git_raw(path, "diff", "HEAD")
    if code != 0:
        return None, "cannot write the recovery patch: %s" % (err.splitlines() or ["?"])[-1]
    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(out)
            if out and not out.endswith("\n"):
                fh.write("\n")
    except OSError as e:
        return None, "cannot write %s: %s" % (target, e.strerror)
    return target, None


def cmd_resume(args, cwd):
    root = control_root(cwd)
    board = load_board_module(script_root())
    if board is None:
        return REFUSED
    board_file = os.path.join(root, "docs", "BOARD.md")
    table, index = board_row(board, board_file, args.board)
    if table is None:
        return REFUSED
    cells = board.cell_texts(table["lines"], index)
    branch_index = board.field_index(table, "branch-worktree")
    cell_text = cells[branch_index] if branch_index is not None and len(cells) > branch_index else ""
    repos, err = load_repos(root)
    if repos is None:
        print(err, file=sys.stderr)
        return REFUSED
    repo_id = args.repo or "control"
    target, err = resolve_repo(root, repos, repo_id)
    if err:
        print(err, file=sys.stderr)
        return REFUSED
    path, branch = live_row_worktree(cell_text, root, target)
    if not path:
        print("row %s has no live worktree in %s; nothing to resume" % (args.board, target),
              file=sys.stderr)
        return REFUSED
    if not provision_env(path, target):
        print("refused: row unchanged; repair env provisioning and resume again", file=sys.stderr)
        return REFUSED
    try:
        lines = list(table["lines"])
        lines[index] = board.replace_cell(lines[index], STATUS_INDEX, "In Progress")
        board.write_atomic(board_file, lines)
    except Exception as exc:
        print("warning: row %s was not updated (%s)" % (args.board, exc), file=sys.stderr)
        return REFUSED
    print("board:    %s is In Progress" % args.board)
    print("worktree: %s" % path)
    print("branch:   %s" % (branch or "(detached)"))
    print("repo:     %s (%s)" % (repo_id, target))
    return OK


def cmd_discard(args, cwd):
    if args.yes and not args.force:
        print("--yes needs --force; --force alone only prints the destruction plan",
              file=sys.stderr)
        return USAGE
    root = control_root(cwd)
    board = load_board_module(script_root())
    if board is None:
        return REFUSED
    board_file = os.path.join(root, "docs", "BOARD.md")
    table, index = board_row(board, board_file, args.board)
    if table is None:
        return REFUSED
    cells = board.cell_texts(table["lines"], index)
    branch_index = board.field_index(table, "branch-worktree")
    cell_text = cells[branch_index] if branch_index is not None and len(cells) > branch_index else ""
    repos, err = load_repos(root)
    if repos is None:
        print(err, file=sys.stderr)
        return REFUSED
    repo_id = args.repo or "control"
    target, err = resolve_repo(root, repos, repo_id)
    if err:
        print(err, file=sys.stderr)
        return REFUSED
    path, branch = live_row_worktree(cell_text, root, target)
    if not path:
        print("row %s has no live worktree in %s; nothing to discard" % (args.board, target),
              file=sys.stderr)
        return REFUSED
    sha = git_out(path, "rev-parse", "HEAD") or ""
    repo = repo_of_path(path) or target
    common = common_dir(repo)
    base, base_err = resolve_base(repo, args.base)
    if base_err:
        print(base_err, file=sys.stderr)
        return REFUSED
    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    dirty, unmerged = removal_state(path, branch, base)
    reason = refusal_reason(dirty, unmerged, branch, base)
    forced = args.force and args.yes
    if args.force and not args.yes:
        print("worktree: %s" % path)
        print("branch:   %s" % (branch or "(detached)"))
        print("base:     %s" % base)
        print("commits the base does not have: %d" % len(unmerged))
        print("dirty files: %d" % len(dirty))
        print("what will be lost:")
        print("  the worktree %s" % path)
        print("  the branch %s" % (branch or "(detached)"))
        for line in dirty:
            print("  uncommitted change: %s" % line)
        for sha in unmerged:
            print("  commit %s" % sha)
        print("refused: --force needs the second confirmation")
        print("nothing was written and nothing was deleted")
        print("to destroy it: worktree.py discard --board %s --force --yes" % args.board)
        return REFUSED
    actions = []
    if reason is None or forced:
        actions = [("worktree", branch or "(detached)", sha, path, "remove-worktree",
                    "forced; the work is saved in the recovery files" if forced
                    else "merged into %s and clean" % base),
                   ("branch", branch, sha, path, "delete-branch",
                    "forced; the commits are listed in the recovery TSV" if forced
                    else "merged into %s" % base)]
    rows = [{"when": now, "kind": k, "name": n, "sha": s, "path": p,
             "action": (a if (args.apply or forced) else "would-" + a), "reason": r}
            for k, n, s, p, a, r in actions]
    for sha in unmerged:
        rows.append({"when": now, "kind": "commit", "name": branch or "(detached)", "sha": sha,
                     "path": path, "action": "restore-branch", "reason":
                     "not reachable from %s; restore with: git branch %s %s" % (base, branch, sha)})
    if reason is not None and not forced:
        rows.append({"when": now, "kind": "worktree", "name": branch or "(detached)", "sha": sha,
                     "path": path, "action": "keep", "reason": reason})
    tsv = recovery_tsv(common, rows) if common else None

    print("worktree: %s" % path)
    print("branch:   %s" % (branch or "(detached)"))
    if reason is not None and not forced:
        print("refused: %s" % reason)
        print("no work was deleted")
        if tsv:
            print("recovery TSV: %s" % tsv)
        return REFUSED
    print("plan:")
    for k, n, s, p, a, r in actions:
        print("  %s %s (%s) - %s" % (a, n, p, r))
    if forced:
        print("forced: %d unmerged commit(s) and %d dirty file(s) will be destroyed" %
              (len(unmerged), len(dirty)))
    if not args.apply and not forced:
        print("dry run; re-run with --apply to act")
        if tsv:
            print("recovery TSV: %s" % tsv)
        return OK

    patch = None
    if forced:
        stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        patch, err = recovery_patch(path, common, dirty, stamp)
        if err:
            print(err, file=sys.stderr)
            print("refused: the recovery copy could not be written; nothing was deleted")
            return REFUSED

    env = load_env_module(script_root())
    if env is not None:
        lines, err = env.clean_into(path, repo, True)
        if err:
            print("env: %s" % err, file=sys.stderr)
        else:
            for line in lines:
                print("env: %s" % line)
    remove_args = ("worktree", "remove", "--force", path) if forced else ("worktree", "remove", path)
    code, _, err = git(repo, *remove_args)
    if code != 0:
        print("worktree remove failed: %s" % (err.splitlines() or ["?"])[-1], file=sys.stderr)
        print("recovery TSV: %s" % tsv)
        return REFUSED
    print("removed worktree " + path)
    code, _, err = git(repo, "branch", "-D", branch)
    if code == 0:
        print("deleted branch " + branch)
    else:
        print("kept branch %s: %s" % (branch, (err.splitlines() or ["?"])[-1]))
    ok, message = clear_row_worktree(board, board_file, table, index, root, path, "Ready")
    if ok:
        print("board: %s is Ready and no longer records the worktree" % args.board)
    else:
        print("warning: row %s was not updated (%s)" % (args.board, message), file=sys.stderr)
    if forced:
        if patch:
            print("recovery patch: %s" % patch)
            print("restore the uncommitted changes with: git apply %s" % patch)
        else:
            print("recovery patch: none; the worktree was clean")
        for sha in unmerged:
            print("lost commit: %s" % sha)
        if unmerged:
            print("restore the branch with: git branch %s %s" % (branch, unmerged[0]))
    print("recovery TSV: %s" % tsv)
    return OK


def cmd_list(args, cwd):
    root = repo_root(cwd)
    if not root:
        print("not inside a git repository", file=sys.stderr)
        return REFUSED
    control = control_root(cwd)
    repos, err = load_repos(control)
    if repos is None:
        print(err, file=sys.stderr)
        return REFUSED
    board = load_board_module(script_root())
    table = None
    if board is not None:
        table, _ = board.read_table(os.path.join(control, "docs", "BOARD.md"))
    print("repo | slug | path | branch | head | kind | state")
    for repo_id in sorted(repos):
        target, err = resolve_repo(control, repos, repo_id)
        if err:
            print("%s | (unresolved) | %s" % (repo_id, err))
            continue
        if not is_git_repo(target):
            print("%s | (not a git repository) | %s" % (repo_id, target))
            continue
        wts = list_worktrees(target)
        main = os.path.realpath(wts[0]["path"]) if wts else os.path.realpath(target)
        base, _ = resolve_base(target, None)
        for wt in wts:
            path = os.path.abspath(wt["path"])
            kind = "main" if os.path.realpath(path) == main else "linked"
            state = worktree_state(board, control, table, path, wt["branch"], base, target)
            print("%s | %s | %s | %s | %s | %s | %s" % (repo_id, slug_of(path, target), path,
                                                       wt["branch"] or "(detached)", wt["head"],
                                                       kind, state))
    return OK


def branch_already_merged(repo, branch, base):
    """True when the base already holds the branch's commits.

    A branch that still sits at the base's own tip has nothing to merge yet, so
    it is not merged: only a branch the base has moved past counts.
    """
    if not branch or not base:
        return False
    tip = git_out(repo, "rev-parse", branch)
    base_tip = git_out(repo, "rev-parse", base)
    if not tip or not base_tip or tip == base_tip:
        return False
    return git(repo, "merge-base", "--is-ancestor", branch, base)[0] == 0


def worktree_state(board, control, table, path, branch, base, repo_root):
    """The state of a worktree: active, merged, stale or unknown."""
    if board is None or table is None:
        return "unknown"
    index, status = row_of_worktree(board, control, table, path)
    if index is None:
        return "unknown"
    if status in ("Merged", "Dropped"):
        return "stale"
    if branch_already_merged(repo_root, branch, base):
        return "merged"
    return "active"


def cmd_handoff(args, cwd):
    root = control_root(cwd)
    board = load_board_module(script_root())
    if board is None:
        return REFUSED
    board_file = os.path.join(root, "docs", "BOARD.md")
    table, index = board_row(board, board_file, args.board)
    if table is None:
        return REFUSED
    cells = board.cell_texts(table["lines"], index)
    branch_index = board.field_index(table, "branch-worktree")
    cell_text = cells[branch_index] if branch_index is not None and len(cells) > branch_index else ""
    repos, err = load_repos(root)
    if repos is None:
        print(err, file=sys.stderr)
        return REFUSED
    repo_id = args.repo or "control"
    target, err = resolve_repo(root, repos, repo_id)
    if err:
        print(err, file=sys.stderr)
        return REFUSED
    path, branch = live_row_worktree(cell_text, root, target)
    if not path:
        print("row %s has no live worktree in %s; nothing to hand off" % (args.board, target),
              file=sys.stderr)
        return REFUSED
    live_branch = git_out(path, "symbolic-ref", "--short", "HEAD")
    repo = repo_of_path(path)
    if not repo:
        print("cannot determine the worktree repository; merge guidance withheld", file=sys.stderr)
        return REFUSED
    recorded_branch = branch
    branch = branch or live_branch
    base, base_err = resolve_base(repo, args.base)
    if base_err:
        print(base_err, file=sys.stderr)
        return REFUSED
    slug = slug_of(path, target)

    print("board:    %s" % args.board)
    print("worktree: %s" % path)
    print("branch:   %s" % branch)
    print("base:     %s" % base)
    print("")
    print("diff:")
    print("  git -C %s diff %s" % (path, base))
    print("log:")
    print("  git -C %s log --oneline %s..HEAD" % (path, base))
    blockers = []
    status = cells[STATUS_INDEX] if len(cells) > STATUS_INDEX else ""
    if not recorded_branch or not live_branch or live_branch != branch:
        blockers.append("cannot confirm the live branch matches the board worktree")
    code, dirty, _ = git(path, "status", "--porcelain", "--untracked-files=all")
    if code != 0:
        blockers.append("git status failed; cleanliness is unknown")
    elif dirty:
        blockers.append("the worktree has staged, unstaged or untracked changes; commit task changes")
    code, ahead, _ = git(path, "rev-list", "--count", "%s..HEAD" % base)
    if code != 0 or not ahead.isdigit():
        blockers.append("cannot determine commits ahead of %s" % base)
    ancestor_code, _, _ = git(path, "merge-base", "--is-ancestor", "HEAD", base)
    if ancestor_code not in (0, 1):
        blockers.append("git ancestry check failed; merge state is unknown")
    tip = git_out(path, "rev-parse", "HEAD")
    base_tip = git_out(path, "rev-parse", "refs/heads/" + base)
    if not tip or not base_tip:
        blockers.append("cannot resolve worktree and base commits")
    merged = ancestor_code == 0 and tip and base_tip and tip != base_tip
    if status != "Pending Merge":
        blockers.append("board status is %s, not Pending Merge; finish verification and review"
                        % (status or "missing"))
    if not merged:
        if ahead == "0":
            blockers.append("no committed work ahead of %s" % base)
    if blockers:
        for blocker in blockers:
            print("NOT READY: %s" % blocker, file=sys.stderr)
        return REFUSED
    if merged:
        print("show:")
        print("  git -C %s show --stat %s..%s" % (path, base, branch))
        print("the branch is already merged into %s; there is nothing to merge" % base)
        print("human recovery (run from %s):" % shlex.quote(target))
    else:
        print("human-only finalize (run from %s after review):" % shlex.quote(target))
    print("  python3 %s finalize --board %s%s" % (
        shlex.quote(os.path.join(script_root(), ".opencode", "skills", "git-worktree",
                                 "scripts", "worktree.py")), shlex.quote(args.board),
        " --repo " + shlex.quote(repo_id) if args.repo else ""))
    return OK


def cmd_finalize(args, cwd):
    """Human-invoked integration and resumable teardown, never called by agent workflows."""
    control = control_root(cwd)
    board = load_board_module(script_root())
    if board is None:
        return REFUSED
    board_file = os.path.join(control, "docs", "BOARD.md")
    table, index = board_row(board, board_file, args.board)
    if table is None:
        return REFUSED
    cells = board.cell_texts(table["lines"], index)
    if cells[STATUS_INDEX] != "Pending Merge":
        print("refused: board is not Pending Merge; verification and review must pass",
              file=sys.stderr)
        return REFUSED
    repos, error = load_repos(control)
    if error:
        print(error, file=sys.stderr)
        return REFUSED
    repo_id = args.repo or "control"
    repo, error = resolve_repo(control, repos, repo_id)
    if error or not is_git_repo(repo):
        print(error or "refused: mapped repository missing", file=sys.stderr)
        return REFUSED
    if os.path.realpath(cwd) != os.path.realpath(repo):
        print("refused: finalize must run in the target repository's main checkout", file=sys.stderr)
        return REFUSED
    base, error = resolve_base(repo, None)
    if error or git_out(repo, "symbolic-ref", "--short", "HEAD") != base:
        print(error or "refused: main checkout is not on its configured base branch", file=sys.stderr)
        return REFUSED
    column = board.field_index(table, "branch-worktree")
    recorded = row_worktrees(cells[column] if column is not None else "", control)
    scoped = [(p, b) for p, b in recorded
              if os.path.realpath(p).startswith(os.path.realpath(os.path.join(repo, WORKTREES_DIR)) + os.sep)]
    if len(scoped) != 1:
        print("refused: expected exactly one recorded worktree in the selected repository",
              file=sys.stderr)
        return REFUSED
    path, branch = scoped[0]
    if not branch or branch == base or not git_out(repo, "check-ref-format", "--branch", branch):
        # check-ref-format prints the branch name on success.
        print("refused: invalid recorded branch", file=sys.stderr)
        return REFUSED
    common = common_dir(repo)
    journal = os.path.join(common, "cleanup-wt", "finalize-%s-%s.json" % (args.board, repo_id))
    existing = None
    if os.path.exists(journal):
        try:
            with open(journal, encoding="utf-8") as stream:
                existing = json.load(stream)
        except (OSError, ValueError) as exc:
            print("refused: cannot read recovery record: %s" % exc, file=sys.stderr)
            return REFUSED
        if (not isinstance(existing, dict) or existing.get("path") != path
                or existing.get("branch") != branch or existing.get("base") != base
                or not isinstance(existing.get("tip"), str)
                or not re.fullmatch(r"[0-9a-f]{40,64}", existing["tip"])
                or not isinstance(existing.get("base_tip"), str)
                or not re.fullmatch(r"[0-9a-f]{40,64}", existing["base_tip"])
                or git_out(repo, "rev-parse", "--verify", existing["tip"] + "^{commit}")
                != existing["tip"]):
            print("refused: recovery record does not match row or repository", file=sys.stderr)
            return REFUSED
    tip = git_out(repo, "rev-parse", "refs/heads/" + branch)
    if existing and tip and tip != existing["tip"]:
        print("refused: branch changed since recovery record", file=sys.stderr)
        return REFUSED
    tip = tip or (existing["tip"] if existing else None)
    if not tip:
        print("refused: missing branch and recovery record", file=sys.stderr)
        return REFUSED
    integrated = git(repo, "merge-base", "--is-ancestor", tip, base)[0] == 0
    base_tip = git_out(repo, "rev-parse", "refs/heads/" + base)
    if not integrated:
        if not os.path.isdir(path) or repo_of_path(path) != os.path.realpath(repo):
            print("refused: recorded worktree missing or in wrong repository", file=sys.stderr)
            return REFUSED
        if git_out(path, "symbolic-ref", "--short", "HEAD") != branch or git_out(path, "rev-parse", "HEAD") != tip:
            print("refused: live worktree branch or tip does not match the board", file=sys.stderr)
            return REFUSED
        ahead = git_out(repo, "rev-list", "--count", "%s..%s" % (base, branch))
        if not ahead or not ahead.isdigit() or int(ahead) < 1:
            print("refused: no committed work ahead of the base", file=sys.stderr)
            return REFUSED
    for location in (repo, path) if os.path.isdir(path) else (repo,):
        code, dirty, _ = git(location, "status", "--porcelain", "--untracked-files=all")
        if code != 0 or dirty:
            print("refused: main checkout or task worktree is dirty", file=sys.stderr)
            return REFUSED
    if not integrated:
        code, output, error = git(repo, "merge-tree", "--write-tree", "--name-only",
                                  "--no-messages", base, branch)
        if code != 0:
            paths = output.splitlines()[1:]
            _, detail, _ = git(repo, "merge-tree", "--write-tree", base, branch)
            messages = [(match.group(1), line) for line in detail.splitlines()
                        if (match := re.match(r"^CONFLICT \(([a-zA-Z /-]+)\):", line))]
            print("refused: merge conflict; retain the task worktree. Resolve there and re-review.",
                  file=sys.stderr)
            for conflict in paths:
                cause = next((category for category, line in messages
                              if line.endswith(" in " + conflict)), "competing edits (type unavailable)")
                print("conflict: %s — %s" % (conflict, cause),
                      file=sys.stderr)
            if not paths:
                print("preflight failed without path details; inspect Git locally", file=sys.stderr)
            return REFUSED
    if not confirm_finalize(args.board, base, branch, tip):
        return REFUSED
    live_tip = git_out(repo, "rev-parse", "refs/heads/" + branch)
    if (git_out(repo, "rev-parse", "refs/heads/" + base) != base_tip
            or (live_tip or (existing["tip"] if integrated and existing else None)) != tip
            or git_out(repo, "symbolic-ref", "--short", "HEAD") != base
            or git(repo, "status", "--porcelain", "--untracked-files=all")[0:2] != (0, "")):
        print("refused: base, branch or main checkout changed during confirmation", file=sys.stderr)
        return REFUSED
    current, current_index = board_row(board, board_file, args.board)
    if current is None:
        return REFUSED
    current_cells = board.cell_texts(current["lines"], current_index)
    if (current_cells[STATUS_INDEX] != "Pending Merge"
            or current_cells[column] != cells[column]):
        print("refused: board row changed during confirmation", file=sys.stderr)
        return REFUSED
    table, index = current, current_index
    print("limitation: QA, review, acceptance proofs and verification are certified by the "
          "Pending Merge lane; their evidence is not machine-readable here.")
    if not existing:
        os.makedirs(os.path.dirname(journal), exist_ok=True)
        try:
            with open(journal, "x", encoding="utf-8") as stream:
                json.dump({"path": path, "branch": branch, "tip": tip, "base": base,
                           "base_tip": base_tip}, stream)
                stream.flush()
                os.fsync(stream.fileno())
            directory = os.open(os.path.dirname(journal), os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except OSError as exc:
            print("refused: recovery record is not durable: %s" % exc, file=sys.stderr)
            return REFUSED
    if not integrated:
        before_merge = git_out(repo, "rev-parse", "HEAD")
        code, _, error = git(repo, "merge", "--no-ff", branch,
                              "-m", "merge: %s" % slug_of(path, repo))
        if code != 0:
            if (before_merge and git_out(repo, "rev-parse", "HEAD") == before_merge
                    and git_out(repo, "rev-parse", "-q", "--verify", "MERGE_HEAD")):
                abort_code, _, _ = git(repo, "merge", "--abort")
                if abort_code != 0:
                    print("merge abort failed; main checkout needs human inspection", file=sys.stderr)
                else:
                    print("merge initiated here was aborted; task branch and board retained", file=sys.stderr)
            print("merge failed; task branch and board retained (Git exit %d)" % code,
                  file=sys.stderr)
            return REFUSED
    if git(repo, "merge-base", "--is-ancestor", tip, base)[0] != 0:
        print("refused: integration ancestry could not be verified", file=sys.stderr)
        return REFUSED
    env = load_env_module(script_root())
    if os.path.isdir(path):
        if env is None:
            print("refused: env cleaner missing; retry finalize", file=sys.stderr)
            return REFUSED
        _, error = env.clean_into(path, repo, True)
        if error:
            print("refused: env cleanup failed: %s; retry finalize" % error, file=sys.stderr)
            return REFUSED
        code, _, error = git(repo, "worktree", "remove", path)
        if code != 0:
            print("refused: worktree removal failed: %s; retry finalize" % error, file=sys.stderr)
            return REFUSED
    if git_out(repo, "rev-parse", "-q", "--verify", "refs/heads/" + branch):
        code, _, error = git(repo, "branch", "-d", branch)
        if code != 0:
            print("refused: branch deletion failed: %s; retry finalize" % error, file=sys.stderr)
            return REFUSED
    remaining = [p for p, _ in recorded if os.path.realpath(p) != os.path.realpath(path)]
    ok, message = clear_row_worktree(board, board_file, table, index, control, path,
                                     None if remaining else "Merged")
    if not ok:
        print("refused: board update failed: %s; retry finalize" % message, file=sys.stderr)
        return REFUSED
    print("integrated into %s; cleaned %s; board %s" %
          (base, branch, "Pending Merge (other repos remain)" if remaining else "Merged"))
    print("recovery record: %s" % journal)
    return OK


def confirm_finalize(board_id, base, branch, tip):
    """Show the target and require an exact interactive yes from a real terminal."""
    try:
        if not sys.stdin.isatty() or not sys.stderr.isatty():
            print("refused: finalize requires a real interactive terminal", file=sys.stderr)
            return False
        sys.stderr.write("Human-only finalize. This is a local policy gate, not an OS security boundary.\n"
                         "Board: %s\nBase: %s\nBranch: %s\nTip: %s\n"
                         "Type exactly yes to confirm: " % (board_id, base, branch, tip))
        sys.stderr.flush()
        answer = sys.stdin.readline()
    except (OSError, UnicodeError, KeyboardInterrupt):
        try:
            print("refused: finalize confirmation interrupted or unavailable", file=sys.stderr)
        except (OSError, UnicodeError):
            pass
        return False
    if not answer.endswith("\n") or answer[:-1].removesuffix("\r") != "yes":
        print("refused: confirmation must be exactly yes", file=sys.stderr)
        return False
    return True


def cmd_verify(args, cwd):
    root = repo_root(cwd)
    if not root:
        print("not inside a git repository", file=sys.stderr)
        return REFUSED
    board = load_board_module(script_root())
    control = control_root(cwd)
    path, board_branch = find_worktree_for_slug(board, control, args.slug, cwd)
    if not path:
        print("no worktree with slug %s" % args.slug, file=sys.stderr)
        return REFUSED
    branch = board_branch or (git_out(path, "rev-parse", "--abbrev-ref", "HEAD") or "(detached)")
    repo = repo_of_path(path) or root
    base, base_err = resolve_base(repo, args.base)
    if base_err:
        print(base_err, file=sys.stderr)
        return REFUSED
    ahead = git_out(path, "log", "--oneline", "%s..HEAD" % base) or ""
    changed = git_out(path, "diff", "--stat", base) or ""
    dirty = git_out(path, "status", "--short") or ""

    print("worktree: %s" % os.path.abspath(path))
    print("branch:   %s" % branch)
    print("base:     %s" % base)
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
        print("NOT READY: no commit ahead of %s" % base)
        return REFUSED
    print("READY FOR MERGE: clean tree, %d commit(s) ahead of %s" % (len(ahead.splitlines()), base))
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


def clear_row_worktree(board, board_file, table, index, root, path, status=None):
    """(ok, message). Drops the worktree from the row's Branch/Worktree cell.

    With a status, the row's lane moves to it in the same write, so the cell
    and the lane never drift apart.
    """
    branch_index = board.field_index(table, "branch-worktree")
    if branch_index is None:
        return False, "the board has no Branch/Worktree column"
    cells = board.cell_texts(table["lines"], index)
    cell_text = cells[branch_index] if len(cells) > branch_index else ""
    try:
        lines = list(table["lines"])
        kept = [(p, b) for p, b in parse_worktree_entries(cell_text)
                if os.path.realpath(p if os.path.isabs(p) else os.path.join(root, p))
                != os.path.realpath(path)]
        merged = ", ".join("%s · branch %s" % (p, branch_name(b)) for p, b in kept)
        lines[index] = board.replace_cell(lines[index], branch_index, merged or "-")
        if status:
            lines[index] = board.replace_cell(lines[index], STATUS_INDEX, status)
        board.write_atomic(board_file, lines)
    except Exception as exc:
        return False, str(exc)
    return True, ""


def row_worktree_for_board(board, control, board_id):
    """(path, branch, table, index) of the row's live worktree in any mapped repo."""
    if board is None:
        return None, None, None, None
    board_file = os.path.join(control, "docs", "BOARD.md")
    table, index = board_row(board, board_file, board_id)
    if table is None:
        return None, None, None, None
    cells = board.cell_texts(table["lines"], index)
    branch_index = board.field_index(table, "branch-worktree")
    cell_text = cells[branch_index] if branch_index is not None and len(cells) > branch_index else ""
    repos, err = load_repos(control)
    if repos is None:
        return None, None, None, None
    for repo_id in sorted(repos):
        target, err = resolve_repo(control, repos, repo_id)
        if err or not is_git_repo(target):
            continue
        path, branch = live_row_worktree(cell_text, control, target)
        if path:
            return path, branch, table, index
    return None, None, None, None


def cmd_cleanup(args, cwd):
    if args.board and args.slug:
        print("name the worktree with a slug or with --board, not both", file=sys.stderr)
        return USAGE
    if not args.board and not args.slug:
        print("name the worktree: 'cleanup <slug>' or 'cleanup --board <BOARD-ID>'",
              file=sys.stderr)
        return USAGE
    root = repo_root(cwd)
    if not root:
        print("not inside a git repository", file=sys.stderr)
        return REFUSED
    board = load_board_module(script_root())
    control = control_root(cwd)
    table = None
    index = None
    board_file = None
    if args.board:
        path, board_branch, table, index = row_worktree_for_board(board, control, args.board)
        board_file = os.path.join(control, "docs", "BOARD.md")
        if not path:
            print("row %s has no live worktree; nothing to clean up" % args.board, file=sys.stderr)
            return REFUSED
    else:
        path, board_branch = find_worktree_for_slug(board, control, args.slug, cwd)
        if not path:
            print("no worktree with slug %s" % args.slug, file=sys.stderr)
            return REFUSED
    branch = board_branch or (git_out(path, "rev-parse", "--abbrev-ref", "HEAD") or "")
    sha = git_out(path, "rev-parse", "HEAD") or ""
    repo = repo_of_path(path) or root
    common = common_dir(repo)
    base, base_err = resolve_base(repo, args.base)
    if base_err:
        print(base_err, file=sys.stderr)
        return REFUSED
    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")

    reason = removal_refusal(path, branch, base)

    actions = []
    if reason is None:
        actions = [("worktree", branch or "(detached)", sha, path, "remove-worktree",
                    "merged into %s and clean" % base),
                   ("branch", branch, sha, path, "delete-branch",
                    "merged into %s" % base)]

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
    env = load_env_module(script_root())
    if env is not None:
        env_lines, env_err = env.clean_into(path, repo, True)
        if env_err:
            print("env: %s" % env_err, file=sys.stderr)
        else:
            for line in env_lines:
                print("env: %s" % line)
    code, _, err = git(repo, "worktree", "remove", path)
    if code != 0:
        print("worktree remove failed: %s" % (err.splitlines() or ["?"])[-1], file=sys.stderr)
        print("recovery TSV: %s" % tsv)
        return REFUSED
    done.append("removed worktree " + path)
    code, _, err = git(repo, "branch", "-D", branch)
    branch_deleted = code == 0
    if branch_deleted:
        done.append("deleted branch " + branch)
    else:
        done.append("kept branch %s: %s" % (branch, (err.splitlines() or ["?"])[-1]))
    for d in done:
        print(d)
    if table is not None:
        cell_index = board.field_index(table, "branch-worktree")
        cells = board.cell_texts(table["lines"], index)
        others = [p for p, _ in row_worktrees(cells[cell_index], control)
                  if os.path.realpath(p) != os.path.realpath(path)]
        lane = "Merged" if branch_deleted and not others else None
        ok, message = clear_row_worktree(board, board_file, table, index, control, path, lane)
        if ok:
            if lane:
                print("board: %s is Merged and no longer records the worktree" % args.board)
            else:
                print("board: %s no longer records the worktree; the lane is unchanged "
                      "because the branch was not deleted" % args.board)
        else:
            print("warning: row %s was not updated (%s)" % (args.board, message), file=sys.stderr)
    print("recovery TSV: %s" % tsv)
    return OK


def main(argv):
    parser = argparse.ArgumentParser(
        prog="worktree.py", description="Deterministic git worktree lifecycle.")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("create", help="create a worktree named from a board row")
    p.add_argument("--board", required=True, help="board row ID, e.g. BOARD-00X")
    p.add_argument("--base", help="base branch (default: the repository's own default branch)")
    p.add_argument("--slug", help="override the slug derived from the task title")
    p.add_argument("--repo", help="repo id from .opencode/repos.json (default: control)")

    p = sub.add_parser("resume", help="reuse the live worktree of a board row")
    p.add_argument("--board", required=True, help="board row ID, e.g. BOARD-00X")
    p.add_argument("--repo", help="repo id from .opencode/repos.json (default: control)")

    p = sub.add_parser("discard", help="remove the live worktree of a board row")
    p.add_argument("--board", required=True, help="board row ID, e.g. BOARD-00X")
    p.add_argument("--repo", help="repo id from .opencode/repos.json (default: control)")
    p.add_argument("--apply", action="store_true", help="act; without it this is a dry run")
    p.add_argument("--force", action="store_true",
                   help="allow destroying unmerged work; without --yes it only prints the plan")
    p.add_argument("--yes", action="store_true",
                   help="confirm the destruction; it needs --force")
    p.add_argument("--base", help="base branch (default: the repository's own default branch)")

    sub.add_parser("list", help="list worktrees")

    p = sub.add_parser("handoff", help="print the hand-off block for a board row")
    p.add_argument("--board", required=True, help="board row ID, e.g. BOARD-00X")
    p.add_argument("--repo", help="repo id from .opencode/repos.json (default: control)")
    p.add_argument("--base", help="base branch (default: the repository's own default branch)")

    p = sub.add_parser("finalize", help="human-only: integrate and clean a reviewed worktree")
    p.add_argument("--board", required=True, help="board row ID")
    p.add_argument("--repo", help="repo id from .opencode/repos.json (default: control)")

    p = sub.add_parser("verify", help="check whether a worktree is ready to merge")
    p.add_argument("slug")
    p.add_argument("--base", help="base branch (default: the repository's own default branch)")

    p = sub.add_parser("cleanup", help="remove a merged worktree and its branch")
    p.add_argument("slug", nargs="?")
    p.add_argument("--board", help="board row ID, e.g. BOARD-00X; an alternative to the slug")
    p.add_argument("--apply", action="store_true", help="act; without it this is a dry run")
    p.add_argument("--base", help="base branch (default: the repository's own default branch)")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return USAGE
    cwd = os.getcwd()
    if args.command == "create":
        return cmd_create(args, cwd)
    if args.command == "resume":
        return cmd_resume(args, cwd)
    if args.command == "discard":
        return cmd_discard(args, cwd)
    if args.command == "handoff":
        return cmd_handoff(args, cwd)
    if args.command == "finalize":
        return cmd_finalize(args, cwd)
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
