#!/usr/bin/env python3
"""Deterministic git worktree lifecycle for this factory.

    worktree.py create --board BOARD-00X [--base main] [--slug <override>] [--repo <id>]
    worktree.py resume --board BOARD-00X
    worktree.py discard --board BOARD-00X [--apply] [--force] [--yes]
    worktree.py handoff --board BOARD-00X
    worktree.py list
    worktree.py verify <slug> [--base main]
    worktree.py cleanup <slug> [--apply]
    worktree.py mode required|optional|status
    worktree.py handoff --board BOARD-00X
    worktree.py merge --board BOARD-00X [--target <branch>] [--apply]
    worktree.py discard --board BOARD-00X [--repo <id>] [--apply --discard]
    worktree.py cleanup --board BOARD-00X [--apply]

create reads the board row named by --board from docs/BOARD.md, derives the
branch type from its Type column and the slug from its task title, then makes
.kilo/worktrees/<slug> on branch <type>/<slug> and records the worktree on the
row. Existing workspaces can be shared with --reuse; Fix rows reuse their parent.
Otherwise an existing branch or directory is a refusal.
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

handoff prints the hand-off block for a row: the diff command first, then the
merge command. It prints commands and paths only; it never changes anything.

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

cleanup takes the worktree either as a slug or as the board row that owns it:
cleanup --board BOARD-00X resolves the row's Branch/Worktree cell. Exactly one
of the two may be given.

Exit codes: 0 ok, 1 refusal, 2 usage error, 66 invalid input.
"""
import argparse
import importlib.util
import json
import os
import re
import shlex
import shutil
import stat
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


def load_guard_policy(root):
    spec = importlib.util.spec_from_file_location("guard", os.path.join(
        script_root(), ".kilo", "skills", "git-worktree", "scripts", "guard.py"))
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    if not guard.is_control_repo(root):
        raise ValueError("workspace permissions require a control repository with a board and repo map")
    policy = guard.load_policy(confined(os.path.join(root, guard.POLICY_REL), root))
    if (not isinstance(policy, dict) or not policy.get("protected_branches") or
            not isinstance(policy.get("bash"), list) or not isinstance(policy.get("edit"), list) or
            not isinstance(policy.get("hidden_paths"), dict) or
            not any(rule.get("workspace_default") for rule in policy["edit"])):
        raise ValueError("control policy is missing required workspace/secret protections")
    return guard, policy


def cmd_mode(args, cwd):
    root = control_root(cwd)
    state = local_state(root)
    if args.value != "status":
        guard, policy = load_guard_policy(root)
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


def provision_local_files(primary, destination, include_navigation=False):
    """Copy untracked local config without replacing worktree files."""
    primary, destination = Path(primary), Path(destination)
    candidates = []
    for directory, dirnames, filenames in os.walk(primary, followlinks=False):
        relative_directory = Path(directory).relative_to(primary).as_posix()
        dirnames[:] = [name for name in dirnames if name != ".git" and
                       not (relative_directory == ".kilo" and name == "worktrees") and
                       not (Path(directory) / name).is_symlink()]
        for name in filenames:
            source = Path(directory) / name
            relative = source.relative_to(primary)
            is_env = name.startswith(".env") and name != ".env.example"
            is_navigation = (include_navigation and
                             relative.as_posix() == ".kilo/local/qa-navigation.json")
            if is_env or is_navigation:
                candidates.append((source, relative))

    for source, relative in candidates:
        if source.is_symlink() or not source.is_file():
            continue
        rel = relative.as_posix()
        if git_out(str(primary), "ls-files", "--", rel):
            continue
        destination_file = destination / relative
        if destination_file.exists() or destination_file.is_symlink():
            continue
        if any(part.is_symlink() for part in destination_file.parents
               if part != destination and os.path.commonpath([str(part), str(destination)]) == str(destination)):
            continue
        destination_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            source_fd = os.open(str(source), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) |
                                getattr(os, "O_NONBLOCK", 0))
        except FileNotFoundError:
            continue
        try:
            with os.fdopen(source_fd, "rb") as source_stream:
                source_stat = os.fstat(source_stream.fileno())
                if not stat.S_ISREG(source_stat.st_mode):
                    continue
                try:
                    destination_fd = os.open(
                        str(destination_file), os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                        stat.S_IMODE(source_stat.st_mode))
                except FileExistsError:
                    continue
                with os.fdopen(destination_fd, "wb") as destination_stream:
                    shutil.copyfileobj(source_stream, destination_stream)
                os.chmod(destination_file, stat.S_IMODE(source_stat.st_mode), follow_symlinks=False)
        except OSError:
            raise


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


def load_env_module(root):
    """The sibling env.py, loaded by path so it works from anywhere."""
    path = os.path.join(root, ".kilo", "skills", "git-worktree", "scripts", "env.py")
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
    branch = "%s/%s" % (branch_type, slug)
    cell_text = cells[branch_index] if len(cells) > branch_index else ""
    live_path, live_branch = live_row_worktree(cell_text, root, target)
    if live_path:
        print("row %s already has a live worktree: %s (branch %s)" %
              (args.board, live_path, live_branch), file=sys.stderr)
        print("pick one:", file=sys.stderr)
        print("  resume:  worktree.py resume --board %s" % args.board, file=sys.stderr)
        print("  discard: worktree.py discard --board %s --apply" % args.board, file=sys.stderr)
        print("  new slug: worktree.py create --board %s --slug <other-slug>" % args.board,
              file=sys.stderr)
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
    guard, policy = load_guard_policy(root)
    state = local_state(root)
    code, _, err = (0, "", "") if shared else git(target, "worktree", "add", path, "-b", branch, base)
    if code != 0:
        print("git worktree add failed: %s" % (err.splitlines() or ["?"])[-1], file=sys.stderr)
        return REFUSED
    if not shared:
        state["workspaces"][path] = {"base": base, "branch": branch, "outcome": "active", "boards": [args.board]}
    else:
        associated = state["workspaces"].setdefault(path, {"base": base, "branch": branch, "outcome": "active"})
        boards = associated.setdefault("boards", [reuse])
        if args.board not in boards:
            boards.append(args.board)
    local_state(root, state)
    if not shared:
        try:
            config = confined(os.path.join(path, "kilo.jsonc"), path)
            inherited = set()
            if os.path.commonpath([path, root]) == root:
                for parent in Path(path).parents:
                    if os.path.commonpath([str(parent), root]) != root:
                        break
                    ancestor = confined(os.path.join(parent, "kilo.jsonc"), root)
                    if os.path.exists(ancestor):
                        inherited.add(ancestor)
            local = os.path.exists(config)
            if not local and (repo_id == "control" or not inherited):
                raise ValueError("new checkout has no effective project configuration")
            candidates = inherited | ({config} if local else set())
            override = os.environ.get("KILO_CONFIG")
            if override and os.path.abspath(override) not in candidates:
                raise ValueError("KILO_CONFIG is outside the new checkout's effective configurations")
            for candidate in sorted(candidates):
                expected, message = guard.write_permission_map(candidate, policy, mode=state["mode"], preview=True)
                if expected is None:
                    raise ValueError(message)
                if candidate != config:
                    current, _ = guard.load_config(candidate)
                    if not guard.permission_maps_match(current.get("permission"), expected):
                        raise ValueError("inherited permission map disagrees with saved mode: %s" % candidate)
            if local:
                expected, message = guard.write_permission_map(config, policy, mode=state["mode"])
                if expected is None:
                    raise ValueError(message)
        except (ValueError, OSError) as exc:
            state["workspaces"][path]["error"] = "permission initialization failed: %s" % exc
            local_state(root, state)
            print("worktree %s and branch %s preserved; permission initialization failed: %s; "
                  "board unchanged, creation incomplete" % (path, branch, exc), file=sys.stderr)
            return REFUSED
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
    if not shared:
        try:
            provision_local_files(main_checkout_root(target), path, include_navigation=True)
        except OSError:
            state["workspaces"][path]["error"] = "local file provisioning failed"
            local_state(root, state)
            print("worktree %s and branch %s preserved; local file provisioning failed; "
                  "board unchanged, creation incomplete" % (path, branch), file=sys.stderr)
            return REFUSED
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


def provision_env(path, target):
    """Copy the env files into a new worktree and report what was provisioned."""
    env = load_env_module(script_root())
    if env is None:
        print("env: not provisioned; the env script is missing", file=sys.stderr)
        return
    lines, err = env.sync_into(path, target)
    if err:
        print("env: %s" % err, file=sys.stderr)
        return
    for line in lines:
        print("env: %s" % line)


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
    print("worktree: %s" % path)
    print("branch:   %s" % (branch or "(detached)"))
    print("repo:     %s (%s)" % (repo_id, target))
    try:
        lines = list(table["lines"])
        lines[index] = board.replace_cell(lines[index], STATUS_INDEX, "In Progress")
        board.write_atomic(board_file, lines)
    except Exception as exc:
        print("warning: row %s was not updated (%s)" % (args.board, exc), file=sys.stderr)
        return REFUSED
    print("board:    %s is In Progress" % args.board)
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
    if args.command not in ("handoff", "merge"):
        raise ValueError("cmd_lifecycle handles handoff and merge only")
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
        for verb in ("merge",):
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
    branch = branch or (git_out(path, "rev-parse", "--abbrev-ref", "HEAD") or "")
    repo = repo_of_path(path) or target
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
    if branch_already_merged(repo, branch, base):
        print("show:")
        print("  git -C %s show --stat %s..%s" % (path, base, branch))
        print("the branch is already merged into %s; there is nothing to merge" % base)
    else:
        print("merge (run by the human, in the main checkout):")
        print("  git merge --no-ff %s -m \"merge: %s\"" % (branch, slug))
    print("after the merge, remove the worktree and delete the branch:")
    print("  python3 .kilo/skills/git-worktree/scripts/worktree.py cleanup --board %s --apply"
          % args.board)
    print("or, by hand:")
    print("  git worktree remove %s" % path)
    print("  git branch -d %s" % branch)
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
        lane = "Merged" if branch_deleted else None
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

    p = sub.add_parser("mode", help="project-local workspace requirement; restart Kilo after changes")
    p.add_argument("value", choices=("required", "optional", "status"))

    p = sub.add_parser("create", help="create a worktree named from a board row")
    p.add_argument("--board", required=True, help="board row ID, e.g. BOARD-00X")
    p.add_argument("--base", help="base branch (default: the repository's own default branch)")
    p.add_argument("--slug", help="override the slug derived from the task title")
    p.add_argument("--repo", help="repo id from .kilo/repos.json (default: control)")
    p.add_argument("--reuse", help="reuse the workspace of another board row")

    p = sub.add_parser("resume", help="reuse the live worktree of a board row")
    p.add_argument("--board", required=True, help="board row ID, e.g. BOARD-00X")
    p.add_argument("--repo", help="repo id from .kilo/repos.json (default: control)")

    p = sub.add_parser("discard", help="remove the live worktree of a board row")
    p.add_argument("--board", required=True, help="board row ID, e.g. BOARD-00X")
    p.add_argument("--repo", help="repo id from .kilo/repos.json (default: control)")
    p.add_argument("--apply", action="store_true", help="act; without it this is a dry run")
    p.add_argument("--force", action="store_true",
                   help="allow destroying unmerged work; without --yes it only prints the plan")
    p.add_argument("--yes", action="store_true",
                   help="confirm the destruction; it needs --force")
    p.add_argument("--base", help="base branch (default: the repository's own default branch)")

    sub.add_parser("list", help="list worktrees")

    p = sub.add_parser("verify", help="check whether a worktree is ready to merge")
    p.add_argument("slug")
    p.add_argument("--base", help="base branch (default: the repository's own default branch)")
    p.add_argument("--repo", action="append", help="disambiguate repo ID")

    p = sub.add_parser("cleanup", help="remove a merged worktree and its branch")
    p.add_argument("slug", nargs="?")
    p.add_argument("--board", help="board row ID, e.g. BOARD-00X; an alternative to the slug")
    p.add_argument("--apply", action="store_true", help="act; without it this is a dry run")
    p.add_argument("--base", help="base branch (default: the repository's own default branch)")
    p.add_argument("--repo", action="append", help="disambiguate repo ID")

    for command in ("handoff", "merge"):
        p = sub.add_parser(command, help="human CLI workspace %s (preview by default)" % command)
        p.add_argument("--board", action="append", required=True, help="board ID; repeat for a batch")
        p.add_argument("--repo", action="append", help="select repo IDs; default all required repos")
        p.add_argument("--target", help="explicit target branch; otherwise each workspace's own base")
        if command == "merge":
            p.add_argument("--apply", action="store_true", help="human CLI only: execute previewed operations")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return USAGE
    cwd = os.getcwd()
    if args.command == "mode":
        return cmd_mode(args, cwd)
    if args.command in ("handoff", "merge"):
        return cmd_lifecycle(args, cwd)
    if args.command == "create":
        return cmd_create(args, cwd)
    if args.command == "resume":
        return cmd_resume(args, cwd)
    if args.command == "discard":
        return cmd_discard(args, cwd)
    if args.command == "handoff":
        return cmd_handoff(args, cwd)
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
