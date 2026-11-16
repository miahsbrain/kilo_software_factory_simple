#!/usr/bin/env python3
"""Deterministic git worktree lifecycle for this factory.

    worktree.py create --board BOARD-00X [--base main] [--slug <override>] [--repo <id>]
    worktree.py list
    worktree.py verify <slug> [--base main]
    worktree.py cleanup <slug> [--apply]
    worktree.py mode required|optional|status
    worktree.py handoff --board BOARD-00X
    worktree.py merge --board BOARD-00X [--target <branch>] [--apply]
    worktree.py discard --board BOARD-00X [--repo <id>] [--apply --discard]

create reads the board row named by --board from docs/BOARD.md, derives the
branch type from its Type column and the slug from its task title, then makes
.kilo/worktrees/<slug> on branch <type>/<slug> and records the worktree on the
row. Existing workspaces can be shared with --reuse; Fix rows reuse their parent.
Otherwise an existing branch or directory is a refusal.

--repo picks the repository the worktree is created in. The id comes from
.kilo/repos.json in the control repo; the default is "control", the control
repo itself. The board stays in the control repo; the worktree is created in
the target repo, under that repo's own .kilo/worktrees/.

verify reports branch, commits ahead of base, changed files and dirty state,
and exits 0 only when the tree is clean and the branch has at least one commit
ahead of base.

cleanup, merge and discard preview by default. cleanup --apply requires clean,
merged work. Human-run discard --apply --discard explicitly permits removal of
selected dirty or unmerged workspaces and their feature branches. Protected
branches, main checkouts, locks and paths outside mapped workspace roots are refused.
Merge preflights every selected repository; progress and errors are recorded in
the control repository's common Git directory at kilo-workspace.json.

Exit codes: 0 ok, 1 refusal, 2 usage error, 66 invalid input.
"""
import argparse
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

TYPE_MAP = {"Feature": "feat", "Fix": "fix", "Chore": "chore", "Docs": "docs",
            "Research": "chore"}
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
WORKTREES_DIR = os.path.join(".kilo", "worktrees")
MAX_SLUG_LEN = 48
STATUS_INDEX = 3
REPOS_REL = os.path.join(".kilo", "repos.json")
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


def checked_git(cwd, *args):
    code, out, err = git(cwd, *args)
    if code:
        raise ValueError("git %s failed (exit %s): %s" % (" ".join(args), code, err))
    return out


def confined(path, root):
    path, root = os.path.abspath(path), os.path.abspath(root)
    if os.path.commonpath([path, root]) != root:
        raise ValueError("path escapes permitted root: %s" % path)
    for part in [Path(path)] + list(Path(path).parents):
        if part.is_symlink():
            raise ValueError("symlink path refused: %s" % path)
    return path


def local_state(root, value=None):
    common = checked_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    path = confined(os.path.join(common, "kilo-workspace.json"), common)
    if value is None:
        if not os.path.exists(path):
            return {"mode": "required", "workspaces": {}}
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        if data.get("mode") not in ("required", "optional") or not isinstance(data.get("workspaces"), dict):
            raise ValueError("invalid local workspace state")
        return data
    fd, temporary = tempfile.mkstemp(dir=common, prefix=".workspace-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(value, fh, indent=2)
            fh.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def workspace_mode(cwd):
    return local_state(control_root(cwd))["mode"]


def cmd_mode(args, cwd):
    root = control_root(cwd)
    state = local_state(root)
    if args.value != "status":
        spec = importlib.util.spec_from_file_location("guard", os.path.join(
            script_root(), ".kilo", "skills", "git-worktree", "scripts", "guard.py"))
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        if not guard.is_control_repo(root):
            raise ValueError("mode requires a control repository with a board and repo map")
        policy = guard.load_policy(confined(os.path.join(root, guard.POLICY_REL), root))
        if (not isinstance(policy, dict) or not policy.get("protected_branches") or
                not isinstance(policy.get("bash"), list) or not isinstance(policy.get("edit"), list) or
                not isinstance(policy.get("hidden_paths"), dict) or
                not any(rule.get("workspace_default") for rule in policy["edit"])):
            raise ValueError("control policy is missing required workspace/secret protections")
        repos, error = load_repos(root)
        if error or repos.get("control") != ".":
            raise ValueError(error or "repo map must register control as '.'")
        configs, checkouts = set(), set()
        for repo_id in repos:
            target, error = resolve_repo(root, repos, repo_id)
            if error or not is_git_repo(target):
                raise ValueError(error or "mapped repository is missing: %s" % repo_id)
            for entry in list_worktrees(target):
                tree = confined(entry["path"], target)
                if not os.path.isdir(tree) or entry.get("prunable"):
                    raise ValueError("mapped checkout is missing or prunable: %s" % tree)
                checkouts.add(tree)
                config = confined(os.path.join(tree, "kilo.jsonc"), tree)
                if os.path.exists(config) or repo_id == "control":
                    configs.add(config)
                if repo_id != "control":
                    inherited = os.path.exists(config)
                    if os.path.commonpath([tree, root]) == root:
                        for parent in Path(tree).parents:
                            if os.path.commonpath([str(parent), root]) != root:
                                break
                            ancestor_config = confined(os.path.join(parent, "kilo.jsonc"), root)
                            if os.path.exists(ancestor_config):
                                configs.add(ancestor_config)
                                inherited = True
                    if not inherited:
                        raise ValueError("mapped checkout has no effective project config: %s" % tree)
        if checked_git(cwd, "rev-parse", "--show-toplevel") not in checkouts:
            raise ValueError("caller is not a mapped project checkout")
        override = os.environ.get("KILO_CONFIG")
        if override and os.path.abspath(override) not in configs:
            raise ValueError("KILO_CONFIG is outside the project's effective configurations")
        originals = {}
        for config in sorted(configs):
            expected, message = guard.write_permission_map(config, policy, mode=args.value, preview=True)
            if expected is None:
                raise ValueError(message)
            with open(config, "rb") as fh:
                originals[config] = fh.read()
        try:
            for config in originals:
                expected, message = guard.write_permission_map(config, policy, mode=args.value)
                if expected is None:
                    raise ValueError(message)
            state["mode"] = args.value
            local_state(root, state)
        except (ValueError, OSError):
            for config, content in originals.items():
                with open(config, "wb") as fh:
                    fh.write(content)
            raise
    print("workspace mode: %s (project-local)" % state["mode"])
    print("Restart Kilo after changing mode to reload the generated edit permission map.")
    return OK


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
    out = checked_git(cwd, "worktree", "list", "--porcelain")
    for line in out.splitlines():
        key, _, value = line.partition(" ")
        if key == "worktree" and value:
            return os.path.abspath(value)
    raise ValueError("cannot resolve main checkout")


def control_root(cwd):
    """The control repo of the work: the repo that owns the board and the map.

    A work surface holds application code only, so running the harness from
    inside one must still find the project that governs it. The control repo
    is the nearest ancestor that holds a repo map and a board. Its main
    checkout is returned, because the board has one writer and that writer
    works in the main checkout.
    """
    path = os.path.abspath(cwd)
    found = None
    while True:
        if (os.path.exists(os.path.join(path, REPOS_REL))
                and os.path.exists(os.path.join(path, "docs", "BOARD.md"))):
            found = path
            break
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent
    if found is None:
        return main_checkout_root(cwd)
    out = checked_git(found, "worktree", "list", "--porcelain")
    for line in out.splitlines():
        key, _, value = line.partition(" ")
        if key == "worktree" and value:
            return os.path.abspath(value)
    raise ValueError("cannot resolve control checkout")


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
    try:
        confined(target, target if os.path.isabs(rel) else root)
    except ValueError as exc:
        return None, str(exc)
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

    ``main`` wins whenever it exists, so the control repo keeps its documented
    base. A repository that does not have ``main`` names its own default branch
    through ``origin/HEAD``; the checked-out branch is the last resort.
    """
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


def load_scope_module(root):
    """The sibling scope.py, loaded by path so it works from anywhere."""
    path = os.path.join(root, ".kilo", "skills", "git-worktree", "scripts", "scope.py")
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location("scope", path)
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
    out = checked_git(cwd, "worktree", "list", "--porcelain")
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
            elif key in ("locked", "prunable"):
                wt[key] = True
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
    confined(board_file, root)
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
    reuse = getattr(args, "reuse", None)
    if row_type == "Fix" and not reuse:
        dependency = board.field_index(table, "blocked-by")
        parents = re.findall(r"BOARD-\d+", cells[dependency]) if dependency is not None else []
        if len(parents) != 1:
            raise ValueError("Fix rows reuse a shared workspace; select its board ID with --reuse")
        reuse = parents[0]
    shared = None
    if reuse:
        shared = lifecycle_selection(root, board, [reuse], [repo_id])[0]
        validate_workspace(shared, root)
    slug = os.path.basename(shared["path"]) if shared else args.slug or derived
    if not SLUG_RE.match(slug):
        print("invalid slug %r: use kebab-case, e.g. user-login" % slug, file=sys.stderr)
        return INVALID
    if args.slug and args.slug != derived:
        print("derived slug: %s" % derived)
        print("used slug:    %s" % slug)
    branch = shared["branch"] if shared else "%s/%s" % (branch_type, slug)
    if not shared and git_out(target, "rev-parse", "-q", "--verify", "refs/heads/" + branch):
        print("branch %s already exists in %s; pick another slug or type"
              % (branch, target), file=sys.stderr)
        return REFUSED
    path = confined(worktree_path(target, slug), os.path.join(target, WORKTREES_DIR))
    if not shared and os.path.exists(path):
        print("directory %s already exists; refusing to overwrite it" % path, file=sys.stderr)
        return REFUSED
    base, base_err = resolve_base(target, args.base)
    if base_err:
        print(base_err, file=sys.stderr)
        return REFUSED
    if shared:
        saved_base = local_state(root)["workspaces"].get(path, {}).get("base", base)
        if args.base and args.base != saved_base:
            raise ValueError("reused workspace keeps its original base: %s" % saved_base)
        base = saved_base
    code, _, err = (0, "", "") if shared else git(target, "worktree", "add", path, "-b", branch, base)
    if code != 0:
        print("git worktree add failed: %s" % (err.splitlines() or ["?"])[-1], file=sys.stderr)
        return REFUSED
    state = local_state(root)
    if not shared:
        state["workspaces"][path] = {"base": base, "branch": branch, "outcome": "active", "boards": [args.board]}
    else:
        associated = state["workspaces"].setdefault(path, {"base": base, "branch": branch, "outcome": "active"})
        boards = associated.setdefault("boards", [reuse])
        if args.board not in boards:
            boards.append(args.board)
    local_state(root, state)
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
        lines[index] = board.replace_cell(lines[index], STATUS_INDEX, "In Progress")
        board.write_atomic(board_file, lines)
    except Exception as exc:
        print("warning: worktree %s exists but row %s was not updated (%s)" %
              (path, args.board, exc), file=sys.stderr)
        return REFUSED
    print("board:    %s" % args.board)
    print("board file: %s" % board_file)
    print("task:     %s" % task)
    print("repo:     %s (%s)" % (repo_id, target))
    print("branch:   %s" % branch)
    print("worktree: %s" % os.path.abspath(path))
    print("base:     %s" % base)
    return OK


def lifecycle_selection(root, board, ids=None, repo_ids=None, slug=None):
    repos, error = load_repos(root)
    if error:
        raise ValueError(error)
    targets = {}
    for repo_id, rel in repos.items():
        target, error = resolve_repo(root, repos, repo_id)
        if error:
            raise ValueError(error)
        targets[repo_id] = target
    if repo_ids and any(repo_id not in repos for repo_id in repo_ids):
        raise ValueError("unknown repo ID")
    table, error = board.read_table(confined(os.path.join(root, "docs", "BOARD.md"), root))
    if table is None:
        raise ValueError(error)
    column = board.field_index(table, "branch-worktree")
    repo_column = board.field_index(table, "repos")
    if column is None or repo_column is None:
        raise ValueError("board requires Branch/Worktree and Repos columns")
    selected, found = {}, set()
    for index in table["rows"]:
        cells = board.cell_texts(table["lines"], index)
        if ids and cells[0] not in ids:
            continue
        if not ids and cells[STATUS_INDEX] in ("Merged", "Dropped"):
            continue
        found.add(cells[0])
        represented = set()
        for path, branch in parse_worktree_entries(cells[column]):
            absolute = os.path.abspath(os.path.join(root, path))
            matches = [key for key, target in targets.items()
                       if os.path.dirname(absolute) == os.path.join(target, WORKTREES_DIR)]
            if len(matches) != 1:
                raise ValueError("workspace is outside mapped .kilo/worktrees or ambiguous: %s" % path)
            repo_id = matches[0]
            represented.add(repo_id)
            if repo_ids and repo_id not in repo_ids:
                continue
            if slug and os.path.basename(absolute) != slug:
                continue
            confined(absolute, os.path.join(targets[repo_id], WORKTREES_DIR))
            item = {"repo_id": repo_id, "repo": targets[repo_id], "path": absolute,
                    "branch": branch_name(branch), "boards": [cells[0]]}
            if absolute in selected and selected[absolute]["branch"] != item["branch"]:
                raise ValueError("board has inconsistent branch references")
            if absolute in selected:
                selected[absolute]["boards"].append(cells[0])
            else:
                selected[absolute] = item
        required = {value.strip() for value in cells[repo_column].split(",") if value.strip() not in ("", "-")}
        if ids and not required.issubset(represented):
            raise ValueError("board %s has required repos without workspace entries" % cells[0])
    if ids and found != set(ids):
        raise ValueError("unknown board ID: %s" % ", ".join(sorted(set(ids) - found)))
    if not selected:
        raise ValueError("no selected board workspace")
    if repo_ids and not set(repo_ids).issubset({item["repo_id"] for item in selected.values()}):
        raise ValueError("selected repo has no workspace on these board rows")
    if slug and not repo_ids and len(selected) > 1:
        raise ValueError("ambiguous slug; select --repo")
    return list(selected.values())


def validate_workspace(item, root, allow_removed=False):
    path, repo, branch = item["path"], item["repo"], item["branch"]
    confined(repo, repo)
    confined(path, os.path.join(repo, WORKTREES_DIR))
    if not is_git_repo(repo):
        raise ValueError("mapped path is not a repository: %s" % repo)
    with open(os.path.join(script_root(), ".kilo", "policies", "git-policy.json"), encoding="utf-8") as fh:
        protected = set(json.load(fh)["protected_branches"])
    code, default, err = git(repo, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    if code not in (0, 1):
        raise ValueError("cannot resolve repository default: %s" % err)
    if default:
        protected.add(default.split("/", 1)[-1])
    if not branch or branch in protected:
        raise ValueError("protected or detached branch cannot be removed: %s" % branch)
    checked_git(repo, "check-ref-format", "refs/heads/" + branch)
    worktrees = list_worktrees(repo)
    matches = [entry for entry in worktrees if os.path.abspath(entry["path"]) == path]
    if allow_removed and not matches and not os.path.lexists(path):
        return None
    if len(matches) != 1 or path == os.path.abspath(worktrees[0]["path"]):
        raise ValueError("not a linked workspace: %s" % path)
    entry = matches[0]
    if entry["branch"] != branch or entry.get("locked") or entry.get("prunable"):
        raise ValueError("workspace branch mismatch, locked or prunable: %s" % path)
    if checked_git(path, "rev-parse", "--show-toplevel") != path:
        raise ValueError("workspace repository mismatch")
    return entry


def require_clean(path, control):
    excluded = [":(exclude)docs/BOARD.md"] if path == control else []
    dirty = checked_git(path, "status", "--porcelain=v1", "--untracked-files=all", "--", ".", *excluded)
    if dirty:
        raise ValueError("dirty checkout refused: %s\n%s" % (path, dirty))


def related_rows(board, root, identities):
    table, error = board.read_table(confined(os.path.join(root, "docs", "BOARD.md"), root))
    if table is None:
        raise ValueError(error)
    column = board.field_index(table, "branch-worktree")
    rows = []
    for index in table["rows"]:
        cells = board.cell_texts(table["lines"], index)
        entries = parse_worktree_entries(cells[column])
        if cells[STATUS_INDEX] in ("Merged", "Dropped"):
            continue
        if any((os.path.abspath(os.path.join(root, path)), branch_name(branch)) in identities
               for path, branch in entries):
            rows.append((index, cells, entries))
    return table, rows


def update_lifecycle_board(board, root, state, paths):
    identities = {(path, state["workspaces"][path].get("branch")) for path in paths
                  if path in state["workspaces"]}
    table, rows = related_rows(board, root, identities)
    lines = list(table["lines"])
    for index, cells, entries in rows:
        outcomes = []
        for path, branch in entries:
            record = state["workspaces"].get(os.path.abspath(os.path.join(root, path)), {})
            same = record.get("branch") == branch_name(branch) and cells[0] in record.get("boards", [cells[0]])
            outcomes.append(record.get("outcome") if same else None)
        status = ("Merged" if all(value == "merged" for value in outcomes) else
                  "Dropped" if all(value == "discarded" for value in outcomes) else None)
        if status:
            lines[index] = board.replace_cell(lines[index], STATUS_INDEX, status)
    board.write_atomic(os.path.join(root, "docs", "BOARD.md"), lines)


def require_committed_merge(item, control, pending=None):
    target = item["target"]
    if checked_git(target, "symbolic-ref", "--short", "HEAD") != item["base"]:
        raise ValueError("target branch changed after preflight")
    code, _out, error = git(target, "rev-parse", "--quiet", "--verify", "MERGE_HEAD")
    if code == 0:
        raise ValueError("target has an unfinished merge; human must commit it before cleanup")
    if code != 1:
        raise ValueError("cannot establish target merge state: %s" % error)
    require_clean(target, control)
    checked_git(item["repo"], "merge-base", "--is-ancestor", item["sha"], "refs/heads/" + item["base"])
    if pending:
        parents = checked_git(target, "show", "-s", "--format=%P", "HEAD").split()
        if parents != [pending.get("target_sha"), pending.get("sha")]:
            raise ValueError("pending merge was not completed with the saved source and target parents")


def cmd_lifecycle(args, cwd):
    root = control_root(cwd)
    board = load_board_module(script_root())
    if board is None:
        raise ValueError("board parser missing")
    items = lifecycle_selection(root, board, getattr(args, "board", None), args.repo,
                                getattr(args, "slug", None))
    state = local_state(root)
    command = args.command
    script = os.path.join(script_root(), ".kilo", "skills", "git-worktree", "scripts", "worktree.py")
    apply = getattr(args, "apply", False)
    discard = command == "discard"
    if discard and apply and not args.discard:
        raise ValueError("discard requires both --apply and --discard")
    if command != "handoff":
        require_clean(root, root)
    table, rows = related_rows(board, root, {(item["path"], item["branch"]) for item in items})
    if command == "merge":
        for index, cells, _entries in rows:
            if cells[STATUS_INDEX] not in ("Pending Merge", "Merged"):
                raise ValueError("board %s is not review-ready (Pending Merge required)" % cells[0])
            dependency = board.field_index(table, "blocked-by")
            if dependency is not None:
                for other_index in table["rows"]:
                    other = board.cell_texts(table["lines"], other_index)
                    if cells[0] in re.findall(r"BOARD-\d+", other[dependency]) and other[2] == "Fix":
                        other_paths = {os.path.abspath(os.path.join(root, path)) for path, _ in
                                       parse_worktree_entries(other[board.field_index(table, "branch-worktree")])}
                        selected_paths = {item["path"] for item in items}
                        if (other[STATUS_INDEX] not in ("Merged", "Dropped") and
                                (other[STATUS_INDEX] != "Pending Merge" or not other_paths or
                                 not other_paths.issubset(selected_paths))):
                            raise ValueError("open fix row blocks merge: %s" % other[0])
    plans = []
    for item in items:
        record = state["workspaces"].get(item["path"], {})
        if record and (record.get("branch") != item["branch"] or
                       (record.get("boards") and not set(item["boards"]).issubset(record["boards"]))):
            raise ValueError("workspace incarnation does not match selected board entries")
        if record.get("outcome") in ("merged", "discarded"):
            if os.path.lexists(item["path"]):
                raise ValueError("completed workspace path has been recreated; refusing stale state")
            print("%s: already %s" % (item["path"], record["outcome"]))
            continue
        resuming = record.get("outcome") in ("merged-pending-cleanup", "discarded-pending-cleanup")
        pending_merge = command == "merge" and record.get("outcome") == "pending" and record.get("operation") == "merge"
        if resuming and command != "handoff" and record.get("operation") != command:
            raise ValueError("unfinished cleanup must resume its original operation")
        entry = validate_workspace(item, root, allow_removed=resuming)
        base, error = resolve_base(item["repo"], getattr(args, "target", None) or record.get("base"))
        if error:
            raise ValueError(error)
        if base == item["branch"]:
            raise ValueError("source and target are identical")
        item["base"] = base
        item["sha"] = checked_git(item["repo"], "rev-parse", "refs/heads/" + item["branch"])
        item["resuming"] = resuming
        item["removed"] = entry is None
        if resuming and item["sha"] != record.get("sha"):
            raise ValueError("branch changed since interrupted cleanup")
        if (resuming or pending_merge) and (record.get("branch") != item["branch"] or base != record.get("base")
                                           or item["sha"] != record.get("sha")):
            raise ValueError("saved operation source or target identity changed")
        if command == "handoff":
            print(shlex.join(["git", "-C", item["repo"], "diff", base + "..." + item["branch"]]))
            print(shlex.join(["git", "-C", item["repo"], "diff", "--stat", base + "..." + item["branch"]]))
            print("workspace: %s" % item["path"])
            continue
        if not discard and not item["removed"]:
            require_clean(item["path"], root)
        if command == "merge":
            targets = [entry for entry in list_worktrees(item["repo"]) if entry["branch"] == base]
            if len(targets) != 1:
                raise ValueError("target branch must be checked out exactly once: %s" % base)
            target = confined(targets[0]["path"], item["repo"])
            if targets[0].get("locked") or targets[0].get("prunable"):
                raise ValueError("target checkout is locked or prunable")
            require_clean(target, root)
            item["target"] = target
            item["target_sha"] = checked_git(target, "rev-parse", "HEAD")
            ahead = checked_git(item["repo"], "rev-list", base + ".." + item["branch"])
            if pending_merge:
                if target != record.get("target"):
                    raise ValueError("pending merge target checkout changed")
                if not ahead:
                    require_committed_merge(item, root, pending=record)
                    item["resuming"] = resuming = True
                elif item["target_sha"] != record.get("target_sha"):
                    raise ValueError("pending merge target changed without completing the saved merge")
            if resuming:
                require_committed_merge(item, root)
                item["target_sha"] = record.get("target_sha", item["target_sha"])
            if resuming and ahead:
                raise ValueError("previously merged source is no longer reachable from target")
            if not resuming and not ahead:
                raise ValueError("source has no commits ahead of target")
        elif not discard:
            if checked_git(item["repo"], "rev-list", base + ".." + item["branch"]):
                raise ValueError("unmerged branch refused; use explicit discard instead")
        plans.append(item)
        print("%s: %s %s (%s) -> %s" % ("apply" if apply else "preview", command,
              item["repo_id"], item["branch"], base))
    if command == "handoff":
        for verb in ("merge", "discard"):
            invocation = ["python3", script, verb]
            for board_id in args.board:
                invocation.extend(["--board", board_id])
            for repo_id in args.repo or []:
                invocation.extend(["--repo", repo_id])
            if args.target:
                invocation.extend(["--target", args.target])
            print(shlex.join(invocation))
            print(shlex.join(invocation + ["--apply"] + (["--discard"] if verb == "discard" else [])))
        return OK
    if not apply:
        print("dry run; human CLI only: add --apply" + (" --discard" if discard else ""))
        return OK
    target_heads = {item["target"]: (checked_git(item["target"], "rev-parse", "HEAD")
                                    if item["resuming"] else item["target_sha"])
                    for item in plans if command == "merge"}
    for item in plans:
        record = dict(state["workspaces"].get(item["path"], {}))
        record.update({"base": item["base"], "branch": item["branch"], "sha": item["sha"],
                       "outcome": "pending", "operation": command})
        if command == "merge":
            record.update({"target": item["target"], "target_sha": item["target_sha"]})
        state["workspaces"][item["path"]] = record
        local_state(root, state)
        try:
            validate_workspace(item, root, allow_removed=item["resuming"])
            if checked_git(item["repo"], "rev-parse", "refs/heads/" + item["branch"]) != item["sha"]:
                raise ValueError("source branch changed after preflight")
            if not discard and not item["removed"]:
                require_clean(item["path"], root)
            if command == "merge" and not item["resuming"]:
                require_clean(item["target"], root)
                if checked_git(item["target"], "symbolic-ref", "--short", "HEAD") != item["base"]:
                    raise ValueError("target branch changed after preflight")
                current_target = checked_git(item["target"], "rev-parse", "HEAD")
                if current_target != target_heads[item["target"]]:
                    raise ValueError("target commit changed after preflight")
                record["target_sha"] = current_target
                local_state(root, state)
                checked_git(item["target"], "-c", "merge.autoStash=false", "merge", "--no-ff", "--no-edit", "--commit", item["sha"])
            if command == "merge":
                require_committed_merge(item, root)
                target_heads[item["target"]] = checked_git(item["target"], "rev-parse", "HEAD")
            record["outcome"] = "discarded-pending-cleanup" if discard else "merged-pending-cleanup"
            local_state(root, state)
            if not item["removed"]:
                remove_args = ["worktree", "remove"] + (["--force"] if discard else []) + [item["path"]]
                checked_git(item["repo"], *remove_args)
            if checked_git(item["repo"], "rev-parse", "refs/heads/" + item["branch"]) != item["sha"]:
                raise ValueError("source branch changed during cleanup; branch preserved")
            if command == "merge":
                require_committed_merge(item, root)
            checked_git(item["repo"], "branch", "-D", item["branch"])
            record["outcome"] = "discarded" if discard else "merged"
            record.pop("error", None)
            local_state(root, state)
            update_lifecycle_board(board, root, state, {item["path"]})
        except (ValueError, OSError) as exc:
            record["error"] = str(exc)
            local_state(root, state)
            print("halted; partial state recorded in local workspace state: %s" % exc, file=sys.stderr)
            return REFUSED
    update_lifecycle_board(board, root, state, {item["path"] for item in items})
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
    print("repo | slug | path | branch | head | kind")
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
        for wt in wts:
            path = os.path.abspath(wt["path"])
            kind = "main" if os.path.realpath(path) == main else "linked"
            print("%s | %s | %s | %s | %s | %s" % (repo_id, slug_of(path, target), path,
                                                  wt["branch"] or "(detached)", wt["head"], kind))
    return OK


def cmd_verify(args, cwd):
    root = repo_root(cwd)
    if not root:
        print("not inside a git repository", file=sys.stderr)
        return REFUSED
    board = load_board_module(script_root())
    control = control_root(cwd)
    item = lifecycle_selection(control, board, repo_ids=args.repo, slug=args.slug)[0]
    validate_workspace(item, control)
    path, board_branch = item["path"], item["branch"]
    if not path:
        print("no worktree with slug %s" % args.slug, file=sys.stderr)
        return REFUSED
    branch = board_branch or (git_out(path, "rev-parse", "--abbrev-ref", "HEAD") or "(detached)")
    repo = repo_of_path(path) or root
    record = local_state(control)["workspaces"].get(path, {})
    saved_base = record.get("base") if record.get("branch") == branch else None
    base, base_err = resolve_base(repo, args.base or saved_base)
    if base_err:
        print(base_err, file=sys.stderr)
        return REFUSED
    ahead = checked_git(path, "log", "--oneline", "%s..HEAD" % base)
    changed = checked_git(path, "diff", "--stat", base)
    dirty = checked_git(path, "status", "--short")

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


def cmd_cleanup(args, cwd):
    args.target = args.base
    return cmd_lifecycle(args, cwd)


def main(argv):
    parser = argparse.ArgumentParser(
        prog="worktree.py", description="Deterministic git worktree lifecycle.")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("mode", help="project-local workspace requirement; restart Kilo after changes")
    p.add_argument("value", choices=("required", "optional", "status"))

    p = sub.add_parser("create", help="create a worktree named from a board row")
    p.add_argument("--board", required=True, help="board row ID, e.g. BOARD-00X")
    p.add_argument("--base", help="base branch (default: the repository's own default branch)")
    p.add_argument("--slug", help="override the slug derived from the task title")
    p.add_argument("--repo", help="repo id from .kilo/repos.json (default: control)")
    p.add_argument("--reuse", help="reuse the workspace of another board row")

    sub.add_parser("list", help="list worktrees")

    p = sub.add_parser("verify", help="check whether a worktree is ready to merge")
    p.add_argument("slug")
    p.add_argument("--base", help="base branch (default: the repository's own default branch)")
    p.add_argument("--repo", action="append", help="disambiguate repo ID")

    p = sub.add_parser("cleanup", help="remove a merged worktree and its branch")
    p.add_argument("slug")
    p.add_argument("--apply", action="store_true", help="act; without it this is a dry run")
    p.add_argument("--base", help="base branch (default: the repository's own default branch)")
    p.add_argument("--repo", action="append", help="disambiguate repo ID")

    for command in ("handoff", "merge", "discard"):
        p = sub.add_parser(command, help="human CLI workspace %s (preview by default)" % command)
        p.add_argument("--board", action="append", required=True, help="board ID; repeat for a batch")
        p.add_argument("--repo", action="append", help="select repo IDs; default all required repos")
        p.add_argument("--target", help="explicit target branch; otherwise each workspace's own base")
        if command != "handoff":
            p.add_argument("--apply", action="store_true", help="human CLI only: execute previewed operations")
        if command == "discard":
            p.add_argument("--discard", action="store_true", help="explicit consent to lose dirty/unmerged work")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return USAGE
    cwd = os.getcwd()
    if args.command == "mode":
        return cmd_mode(args, cwd)
    if args.command in ("handoff", "merge", "discard"):
        return cmd_lifecycle(args, cwd)
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
