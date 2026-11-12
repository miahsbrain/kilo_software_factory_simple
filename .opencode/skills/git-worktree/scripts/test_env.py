#!/usr/bin/env python3
"""Self-test for the env provisioning and the worktree reuse rules.

    python3 .opencode/skills/git-worktree/scripts/test_env.py

The test builds a throwaway git repository under a temp directory, copies the
scripts into it, and drives them the way an agent would. It never touches this
repository's board, worktrees or branches.

Exit codes: 0 ok, 1 a check failed.
"""
import os
import importlib.util
import json
import shutil
import stat
import subprocess
import sys
import tempfile

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
REPO_SCRIPTS = os.path.abspath(os.path.join(SCRIPTS, "..", ".."))
MARKER = "FACTORY-TEST-SECRET-MARKER"

FAILURES = []


def check(condition, message):
    if not condition:
        FAILURES.append(message)
        print("FAIL: %s" % message)
    return condition


def run(repo, *args):
    """Run a script in the scratch repository; returns (code, stdout, stderr)."""
    proc = subprocess.run([sys.executable] + list(args), cwd=repo,
                          capture_output=True, text=True, timeout=120)
    return proc.returncode, proc.stdout, proc.stderr


def git(repo, *args):
    proc = subprocess.run(["git", "-C", repo] + list(args), capture_output=True,
                          text=True, timeout=60)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def write(path, content):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def make_repo(base):
    """A scratch control repo with the scripts, a board and one row."""
    repo = os.path.join(base, "repo")
    os.makedirs(os.path.join(repo, "docs"))
    for group in ("git-worktree", "board"):
        target = os.path.join(repo, ".opencode", "skills", group, "scripts")
        os.makedirs(target)
        for name in os.listdir(os.path.join(REPO_SCRIPTS, group, "scripts")):
            if name.endswith(".py"):
                shutil.copyfile(os.path.join(REPO_SCRIPTS, group, "scripts", name),
                                os.path.join(target, name))
    write(os.path.join(repo, ".opencode", "repos.json"), '{\n  "control": "."\n}\n')
    write(os.path.join(repo, "docs", "BOARD.md"), (
        "| ID | Task | Type | Status | Priority | Risk | Blocked by | Repos | "
        "Branch/Worktree | Notes |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
        "| BOARD-900 | Provision env files in the scratch repo | Feature | Ready | P2 | "
        "test | None. | control | - | test row |\n"
        "| BOARD-901 | Provision env files in the scratch repo | Feature | Ready | P2 | "
        "test | None. | control | - | a second row with the same title |\n"
        "| BOARD-902 | Force a dirty worktree away | Feature | Ready | P2 | "
        "test | None. | control | - | forced discard of a dirty worktree |\n"
        "| BOARD-903 | Force an unmerged branch away | Feature | Ready | P2 | "
        "test | None. | control | - | forced discard of an unmerged branch |\n"
        "| BOARD-904 | Hand off a worktree | Feature | Ready | P2 | "
        "test | None. | control | - | the hand-off block |\n"
        "| BOARD-905 | Clean up a worktree by board row | Feature | Ready | P2 | "
        "test | None. | control | - | the teardown named by the row |\n"
        "| BOARD-906 | Clean up a worktree by slug | Feature | Ready | P2 | "
        "test | None. | control | - | the teardown named by a slug |\n"
        "| BOARD-907 | Set the lane after a merged cleanup | Feature | Ready | P2 | "
        "test | None. | control | - | cleanup --board on a merged worktree |\n"
        "| BOARD-908 | Refuse a cleanup that holds unmerged work | Feature | Ready | P2 | "
        "test | None. | control | - | the refused cleanup |\n"
        "| BOARD-909 | Set the lane after a discard | Feature | Ready | P2 | "
        "test | None. | control | - | discard --board on a clean worktree |\n"
        "| BOARD-910 | Refuse a discard of a dirty worktree | Feature | Ready | P2 | "
        "test | None. | control | - | the refused discard |\n"))
    write(os.path.join(repo, "README.md"), "scratch\n")
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Test")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "initial")
    return repo


def env_names(repo):
    """The two env file names this factory provisions."""
    return [".env", ".env.local"]


def row_cells(repo, board_id):
    """The cells of one board row, as a list of strings."""
    path = os.path.join(repo, "docs", "BOARD.md")
    script = os.path.join(repo, ".opencode", "skills", "board", "scripts", "board.py")
    spec = importlib.util.spec_from_file_location("scratch_board", script)
    board = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(board)
    table, error = board.read_table(path)
    index = board.row_by_id(table, board_id) if table is not None else None
    return board.cell_texts(table["lines"], index) if index is not None else []


def row_state(repo, board_id):
    """(status, branch/worktree cell) of one board row."""
    cells = row_cells(repo, board_id)
    if len(cells) < 9:
        return None, None
    return cells[3], cells[8]


def main():
    base = tempfile.mkdtemp(prefix="factory-env-test-")
    repo = make_repo(base)
    worktree_script = os.path.join(repo, ".opencode", "skills", "git-worktree", "scripts",
                                   "worktree.py")
    env_script = os.path.join(repo, ".opencode", "skills", "git-worktree", "scripts", "env.py")
    outputs = []

    def call(script, *args):
        code, out, err = run(repo, script, *args)
        outputs.append(out)
        outputs.append(err)
        return code, out, err

    source = os.path.join(repo, ".env")
    write(source, "TOKEN=%s\n" % MARKER)
    local = os.path.join(repo, ".env.local")
    write(local, "LOCAL=%s\n" % MARKER)

    code, out, err = call(worktree_script, "create", "--board", "BOARD-900")
    check(code == 0, "create failed: %s%s" % (out, err))
    slug = "provision-env-files-in-the-scratch-repo"
    worktree = os.path.join(repo, ".opencode", "worktrees", slug)
    check(os.path.isdir(worktree), "the worktree was not created at %s" % worktree)

    for name in env_names(repo):
        copied = os.path.join(worktree, name)
        check(os.path.isfile(copied), "%s was not provisioned into the worktree" % name)
        if not os.path.isfile(copied):
            continue
        mode = stat.S_IMODE(os.stat(copied).st_mode)
        check(mode == 0o600, "%s has mode %o, expected 600" % (name, mode))
        with open(copied, encoding="utf-8") as fh:
            content = fh.read()
        with open(os.path.join(repo, name), encoding="utf-8") as fh:
            check(content == fh.read(), "%s is not byte-identical to the source" % name)

    _, common, _ = git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")
    exclude = os.path.join(common, "info", "exclude")
    check(os.path.isfile(exclude), "the repository has no info/exclude file")
    if os.path.isfile(exclude):
        with open(exclude, encoding="utf-8") as fh:
            excluded = fh.read()
        for name in env_names(repo):
            check(name in excluded, "%s is not listed in info/exclude" % name)

    code, out, err = call(worktree_script, "create", "--board", "BOARD-900")
    check(code != 0, "create did not refuse for a row that already has a live worktree")
    check("resume" in out + err, "the refusal does not name the resume option")
    check("discard" in out + err, "the refusal does not name the discard option")

    code, out, err = call(worktree_script, "create", "--board", "BOARD-901")
    check(code != 0, "create did not refuse for a row whose slug directory is taken")
    check("BOARD-900" in out + err, "the refusal does not name the row that owns the worktree")
    check("resume" not in out + err,
          "the refusal offers a resume for a row that has no worktree")
    check("--slug" in out + err, "the refusal does not offer a new slug")

    code, out, err = call(env_script, "status", "--board", "BOARD-900")
    check(code == 0, "status failed: %s%s" % (out, err))
    for name in env_names(repo):
        check(name in out, "status does not report %s" % name)

    code, out, err = call(env_script, "clean", "--board", "BOARD-900")
    check(code == 0, "the clean dry run failed: %s%s" % (out, err))
    check(os.path.isfile(os.path.join(worktree, ".env")),
          "the clean dry run removed the env copy")
    code, out, err = call(env_script, "clean", "--board", "BOARD-900", "--apply")
    check(code == 0, "clean --apply failed: %s%s" % (out, err))
    for name in env_names(repo):
        check(not os.path.exists(os.path.join(worktree, name)),
              "clean --apply left %s in the worktree" % name)

    outside = os.path.join(repo, "not-a-worktree")
    os.makedirs(outside, exist_ok=True)
    code, out, err = call(env_script, "sync", "--worktree", outside)
    check(code != 0, "sync accepted a destination outside .opencode/worktrees/")

    link_target = os.path.join(base, "link-target.txt")
    write(link_target, "untouched\n")
    planted = os.path.join(worktree, ".env")
    if os.path.exists(planted) or os.path.islink(planted):
        os.unlink(planted)
    os.symlink(link_target, planted)
    code, out, err = call(env_script, "sync", "--worktree", worktree)
    check(code != 0, "sync accepted a planted symlink: %s%s" % (out, err))
    with open(link_target, encoding="utf-8") as fh:
        check(fh.read() == "untouched\n", "the copy was written through the symlink")
    check(os.path.islink(planted), "the planted symlink was changed")
    os.unlink(planted)

    code, out, err = call(worktree_script, "resume", "--board", "BOARD-900")
    check(code == 0, "resume failed: %s%s" % (out, err))
    check(os.path.isdir(worktree), "resume removed the worktree")
    check(row_state(repo, "BOARD-900")[0] == "In Progress",
          "resume did not put the row back in progress")
    for name in env_names(repo):
        check(os.path.isfile(os.path.join(worktree, name)),
              "resume did not re-provision %s" % name)

    marker_file = os.path.join(worktree, "dirty.txt")
    write(marker_file, "uncommitted\n")
    code, out, err = call(worktree_script, "discard", "--board", "BOARD-900", "--apply")
    check(code != 0, "discard accepted a dirty worktree")
    check(os.path.isdir(worktree), "the refused discard removed the worktree")
    os.unlink(marker_file)

    code, out, err = call(worktree_script, "discard", "--board", "BOARD-900")
    check(code == 0, "the discard dry run failed: %s%s" % (out, err))
    check(os.path.isdir(worktree), "the discard dry run removed the worktree")
    code, out, err = call(worktree_script, "discard", "--board", "BOARD-900", "--apply")
    check(code == 0, "discard --apply failed: %s%s" % (out, err))
    check(not os.path.exists(worktree), "discard --apply left the worktree behind")
    _, branches, _ = git(repo, "branch", "--list")
    check(slug not in branches, "discard --apply left the branch behind")
    check(row_state(repo, "BOARD-900")[1] in ("-", ""),
          "discard did not clear the row's worktree cell")

    code, out, err = call(worktree_script, "list")
    check(code == 0, "list failed: %s%s" % (out, err))
    check("state" in out, "list has no state column")

    force_dirty(repo, worktree_script, base, call, check)

    handoff(repo, worktree_script, call, check)

    cleanup_merged(repo, worktree_script, call, check)

    cleanup_by_board(repo, worktree_script, call, check)

    lanes(repo, worktree_script, call, check)

    joined = "".join(outputs)
    check(MARKER not in joined, "the secret value appeared in the script output")

    for name in ("worktree", "guard"):
        spec = importlib.util.spec_from_file_location(name, os.path.join(SCRIPTS, name + ".py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if name == "worktree":
            wt = module
        else:
            guard = module
    git(repo, "branch", "opencode")
    check(wt.default_base(repo) == "main", "app base changed merely because opencode exists")
    os.makedirs(os.path.join(repo, "templates", "project"))
    write(os.path.join(repo, "templates", "project", "AGENTS.md"), "factory fixture\n")
    check(wt.default_base(repo) == "opencode", "factory does not prefer opencode")
    check("opencode" in guard.protected_branch_names(repo), "opencode is not protected")
    policy_path = os.path.join(SCRIPTS, "..", "..", "..", "policies", "git-policy.json")
    with open(policy_path, encoding="utf-8") as fh:
        policy = json.load(fh)
    expected = guard.generated_permission(policy)
    check(isinstance(expected, list), "native permissions are not an ordered array")
    check(all(set(rule) == {"action", "resource", "effect"} for rule in expected),
          "native permission fields are incorrect")
    check(not any(rule["action"] in ("bash", "grep", "glob", "list") for rule in expected),
          "legacy tools or misleading search-path denies were generated")
    check(guard.bash_verdict(policy, "git push origin opencode")[0] == "deny",
          "shell policy no longer denies push")
    config_path = os.path.join(base, "opencode.jsonc")
    write(config_path, '{"default_agent":"architect","custom":{"keep":true}}\n')
    guard.write_permission_map(config_path, policy)
    config, error = guard.load_config(config_path)
    check(error is None and config.get("permissions") == expected,
          "native permission write did not preserve rule ordering")
    check(config.get("custom") == {"keep": True} and config.get("default_agent") == "architect",
          "permission regeneration discarded unrelated config")
    root_config = os.path.join(SCRIPTS, "..", "..", "..", "..", "opencode.jsonc")
    native, error = guard.load_config(root_config)
    check(error is None and native.get("permissions") == expected,
          "tracked native configuration drifted from the policy")
    ctx = guard.repo_context(repo)
    legacy = os.path.join(repo, ".kilo", "worktrees", "bootstrap")
    check(guard.check_worktree("git worktree add %s -b feat/bootstrap main" % legacy,
                               repo, ctx, {}) is not None,
          "legacy bootstrap root weakened steady-state confinement")

    shutil.rmtree(base, ignore_errors=True)
    if FAILURES:
        print("%d check(s) failed" % len(FAILURES))
        return 1
    print("all checks passed")
    return 0


def handoff(repo, worktree_script, call, check):
    """Review first; merge guidance only for committed, finished work."""
    code, out, err = call(worktree_script, "handoff", "--board", "BOARD-901")
    check(code != 0, "handoff did not refuse for a row with no worktree")
    check("no live worktree" in out + err, "the refusal does not say what is missing")

    code, out, err = call(worktree_script, "create", "--board", "BOARD-904")
    check(code == 0, "create failed for BOARD-904: %s%s" % (out, err))
    slug = "hand-off-a-worktree"
    worktree = os.path.join(repo, ".opencode", "worktrees", slug)
    check(os.path.isdir(worktree), "the BOARD-904 worktree was not created")

    code, out, err = call(worktree_script, "handoff", "--board", "BOARD-904")
    check(code == 1, "unfinished handoff did not refuse merge guidance")
    check("git merge --no-ff" not in out, "unfinished handoff offered a merge")
    check("cleanup --board" not in out, "unfinished handoff offered teardown")
    write(os.path.join(worktree, "kept.txt"), "committed on the branch\n")
    git(worktree, "add", "kept.txt")
    git(worktree, "commit", "-m", "a commit on the branch")
    board_script = os.path.join(repo, ".opencode", "skills", "board", "scripts", "board.py")
    code, out, err = call(board_script, "set-status", "BOARD-904", "Pending Merge")
    check(code == 0, "could not mark finished scratch work Pending Merge")

    code, out, err = call(worktree_script, "handoff", "--board", "BOARD-904")
    check(code == 0, "handoff failed: %s%s" % (out, err))
    check(worktree in out, "the block does not name the worktree path")
    check("feat/hand-off-a-worktree" in out, "the block does not name the branch")
    diff_at = out.find("diff %s" % "main")
    merge_at = out.find("finalize --board BOARD-904")
    check(diff_at != -1, "the block has no diff command")
    check(merge_at != -1, "the block has no merge command")
    check(diff_at < merge_at, "the merge command comes before the diff command")
    check("log --oneline main..HEAD" in out, "the block has no log command")
    check("git merge --no-ff" not in out, "the block names a raw merge")

    git(repo, "merge", "--no-ff", "feat/hand-off-a-worktree", "-m", "merge: hand-off-a-worktree")

    code, out, err = call(worktree_script, "handoff", "--board", "BOARD-904")
    check(code == 0, "handoff failed after the merge: %s%s" % (out, err))
    check("git merge --no-ff" not in out, "the block offers a merge command for a merged branch")
    check("show --stat main..feat/hand-off-a-worktree" in out,
          "the block has no show --stat line for a merged branch")
    check("diff main" in out, "the block has no diff command for a merged branch")


def cleanup_merged(repo, worktree_script, call, check):
    """cleanup --board on a merged, clean worktree: the worktree, the branch and the cell go."""
    slug = "hand-off-a-worktree"
    worktree = os.path.join(repo, ".opencode", "worktrees", slug)
    check(os.path.isdir(worktree), "the BOARD-904 worktree is gone before the cleanup")

    code, out, err = call(worktree_script, "cleanup", "--board", "BOARD-904", "--apply")
    check(code == 0, "cleanup --board failed: %s%s" % (out, err))
    check(not os.path.exists(worktree), "cleanup --board left the worktree behind")
    _, branches, _ = git(repo, "branch", "--list")
    check(slug not in branches, "cleanup --board left the branch behind")
    check(row_state(repo, "BOARD-904")[1] in ("-", ""),
          "cleanup --board did not clear the row's worktree cell")


def cleanup_by_board(repo, worktree_script, call, check):
    """cleanup --board on an unmerged branch: the refusal, and nothing destroyed."""
    code, out, err = call(worktree_script, "create", "--board", "BOARD-905")
    check(code == 0, "create failed for BOARD-905: %s%s" % (out, err))
    slug = "clean-up-a-worktree-by-board-row"
    worktree = os.path.join(repo, ".opencode", "worktrees", slug)
    check(os.path.isdir(worktree), "the BOARD-905 worktree was not created")

    code, out, err = call(worktree_script, "cleanup", slug, "--board", "BOARD-905")
    check(code == 2, "cleanup with a slug and --board did not exit 2")

    code, out, err = call(worktree_script, "cleanup")
    check(code == 2, "cleanup with neither a slug nor --board did not exit 2")

    write(os.path.join(worktree, "unmerged.txt"), "a commit the base does not have\n")
    git(worktree, "add", "-A")
    git(worktree, "commit", "-m", "a commit the base does not have")

    code, out, err = call(worktree_script, "cleanup", "--board", "BOARD-905", "--apply")
    check(code != 0, "cleanup --board accepted a branch with an unmerged commit: %s%s" % (out, err))
    check(os.path.isdir(worktree), "the refused cleanup removed the worktree")
    _, branches, _ = git(repo, "branch", "--list")
    check(slug in branches, "the refused cleanup deleted the branch")


def set_status(repo, board_id, status):
    """Put a board row in a lane, through the board script."""
    board_script = os.path.join(repo, ".opencode", "skills", "board", "scripts", "board.py")
    code, out, err = run(repo, board_script, "set-status", board_id, status)
    if code != 0:
        print("set-status failed for %s: %s%s" % (board_id, out, err))


def lanes(repo, worktree_script, call, check):
    """The lane a teardown sets on the row it tears down."""
    cleanup_sets_merged(repo, worktree_script, call, check)
    cleanup_refusal_keeps_lane(repo, worktree_script, call, check)
    discard_sets_ready(repo, worktree_script, call, check)
    discard_refusal_keeps_lane(repo, worktree_script, call, check)
    cleanup_by_slug_keeps_lane(repo, worktree_script, call, check)


def cleanup_sets_merged(repo, worktree_script, call, check):
    """cleanup --board on a merged, clean worktree: the row reads Merged."""
    code, out, err = call(worktree_script, "create", "--board", "BOARD-907")
    check(code == 0, "create failed for BOARD-907: %s%s" % (out, err))
    slug = "set-the-lane-after-a-merged-cleanup"
    worktree = os.path.join(repo, ".opencode", "worktrees", slug)
    check(os.path.isdir(worktree), "the BOARD-907 worktree was not created")
    write(os.path.join(worktree, "merged.txt"), "merged into main\n")
    git(worktree, "add", "-A")
    git(worktree, "commit", "-m", "a commit that gets merged")
    git(repo, "merge", "--no-ff", "feat/%s" % slug, "-m", "merge: %s" % slug)
    set_status(repo, "BOARD-907", "Pending Merge")

    before_status, before_cell = row_state(repo, "BOARD-907")
    check(before_status == "Pending Merge",
          "BOARD-907 is not in Pending Merge before the cleanup, found %r" % before_status)
    check(slug in (before_cell or ""), "BOARD-907 does not record the worktree before the cleanup")

    code, out, err = call(worktree_script, "cleanup", "--board", "BOARD-907", "--apply")
    check(code == 0, "cleanup --board failed for BOARD-907: %s%s" % (out, err))
    check(not os.path.exists(worktree), "cleanup --board left the worktree behind")
    _, branches, _ = git(repo, "branch", "--list")
    check(slug not in branches, "cleanup --board left the branch behind")
    status, cell = row_state(repo, "BOARD-907")
    check(status == "Merged", "cleanup --board left the row at %r, expected Merged" % status)
    check(cell in ("-", ""), "cleanup --board left the worktree cell at %r" % cell)


def cleanup_refusal_keeps_lane(repo, worktree_script, call, check):
    """cleanup --board on an unmerged branch: the refusal leaves the row alone."""
    code, out, err = call(worktree_script, "create", "--board", "BOARD-908")
    check(code == 0, "create failed for BOARD-908: %s%s" % (out, err))
    slug = "refuse-a-cleanup-that-holds-unmerged-work"
    worktree = os.path.join(repo, ".opencode", "worktrees", slug)
    check(os.path.isdir(worktree), "the BOARD-908 worktree was not created")
    write(os.path.join(worktree, "unmerged.txt"), "a commit the base does not have\n")
    git(worktree, "add", "-A")
    git(worktree, "commit", "-m", "a commit the base does not have")
    set_status(repo, "BOARD-908", "In Progress")

    before_status, before_cell = row_state(repo, "BOARD-908")

    code, out, err = call(worktree_script, "cleanup", "--board", "BOARD-908", "--apply")
    check(code != 0, "cleanup --board accepted a branch with an unmerged commit: %s%s" % (out, err))
    check(os.path.isdir(worktree), "the refused cleanup removed the worktree")
    _, branches, _ = git(repo, "branch", "--list")
    check(slug in branches, "the refused cleanup deleted the branch")
    status, cell = row_state(repo, "BOARD-908")
    check(status == before_status,
          "the refused cleanup moved the row from %r to %r" % (before_status, status))
    check(cell == before_cell, "the refused cleanup changed the worktree cell")


def discard_sets_ready(repo, worktree_script, call, check):
    """discard --board on a clean, merged worktree: the row reads Ready."""
    code, out, err = call(worktree_script, "create", "--board", "BOARD-909")
    check(code == 0, "create failed for BOARD-909: %s%s" % (out, err))
    slug = "set-the-lane-after-a-discard"
    worktree = os.path.join(repo, ".opencode", "worktrees", slug)
    check(os.path.isdir(worktree), "the BOARD-909 worktree was not created")
    write(os.path.join(worktree, "merged.txt"), "merged into main\n")
    git(worktree, "add", "-A")
    git(worktree, "commit", "-m", "a commit that gets merged")
    git(repo, "merge", "--no-ff", "feat/%s" % slug, "-m", "merge: %s" % slug)
    set_status(repo, "BOARD-909", "In Progress")

    code, out, err = call(worktree_script, "discard", "--board", "BOARD-909", "--apply")
    check(code == 0, "discard --apply failed for BOARD-909: %s%s" % (out, err))
    check(not os.path.exists(worktree), "discard --apply left the worktree behind")
    status, cell = row_state(repo, "BOARD-909")
    check(status == "Ready", "discard --apply left the row at %r, expected Ready" % status)
    check(cell in ("-", ""), "discard --apply left the worktree cell at %r" % cell)


def discard_refusal_keeps_lane(repo, worktree_script, call, check):
    """discard --board on a dirty worktree: the refusal leaves the row alone."""
    code, out, err = call(worktree_script, "create", "--board", "BOARD-910")
    check(code == 0, "create failed for BOARD-910: %s%s" % (out, err))
    slug = "refuse-a-discard-of-a-dirty-worktree"
    worktree = os.path.join(repo, ".opencode", "worktrees", slug)
    check(os.path.isdir(worktree), "the BOARD-910 worktree was not created")
    write(os.path.join(worktree, "dirty.txt"), "uncommitted work\n")

    before_status, before_cell = row_state(repo, "BOARD-910")

    code, out, err = call(worktree_script, "discard", "--board", "BOARD-910", "--apply")
    check(code != 0, "discard --apply accepted a dirty worktree: %s%s" % (out, err))
    check(os.path.isdir(worktree), "the refused discard removed the worktree")
    status, cell = row_state(repo, "BOARD-910")
    check(status == before_status,
          "the refused discard moved the row from %r to %r" % (before_status, status))
    check(cell == before_cell, "the refused discard changed the worktree cell")


def cleanup_by_slug_keeps_lane(repo, worktree_script, call, check):
    """cleanup by slug: it cannot know the row, so it touches nothing on the board."""
    code, out, err = call(worktree_script, "create", "--board", "BOARD-906")
    check(code == 0, "create failed for BOARD-906: %s%s" % (out, err))
    slug = "clean-up-a-worktree-by-slug"
    worktree = os.path.join(repo, ".opencode", "worktrees", slug)
    check(os.path.isdir(worktree), "the BOARD-906 worktree was not created")
    write(os.path.join(worktree, "merged.txt"), "merged into main\n")
    git(worktree, "add", "-A")
    git(worktree, "commit", "-m", "a commit that gets merged")
    git(repo, "merge", "--no-ff", "feat/%s" % slug, "-m", "merge: %s" % slug)

    before_status, before_cell = row_state(repo, "BOARD-906")

    code, out, err = call(worktree_script, "cleanup", slug, "--apply")
    check(code == 0, "cleanup by slug failed: %s%s" % (out, err))
    check(not os.path.exists(worktree), "cleanup by slug left the worktree behind")
    status, cell = row_state(repo, "BOARD-906")
    check(status == before_status,
          "cleanup by slug moved the row from %r to %r" % (before_status, status))
    check(cell == before_cell, "cleanup by slug changed the worktree cell")


def force_dirty(repo, worktree_script, base, call, check):
    """The forced discard of a dirty worktree: the plan, then the act."""
    code, out, err = call(worktree_script, "create", "--board", "BOARD-902")
    check(code == 0, "create failed for BOARD-902: %s%s" % (out, err))
    slug = "force-a-dirty-worktree-away"
    worktree = os.path.join(repo, ".opencode", "worktrees", slug)
    check(os.path.isdir(worktree), "the BOARD-902 worktree was not created")
    dirty_file = os.path.join(worktree, "uncommitted.txt")
    write(dirty_file, "work that will be destroyed\n")

    code, out, err = call(worktree_script, "discard", "--board", "BOARD-902", "--apply")
    check(code != 0, "discard --apply accepted a dirty worktree without --force")

    code, out, err = call(worktree_script, "discard", "--board", "BOARD-902", "--force")
    check(code != 0, "--force alone did not refuse")
    plan = out + err
    check(worktree in plan, "the plan does not name the worktree path")
    check("feat/force-a-dirty-worktree-away" in plan, "the plan does not name the branch")
    check("dirty files: 1" in plan, "the plan does not report the dirty file count")
    check("--force --yes" in plan, "the plan does not name the command that acts")
    check(os.path.isdir(worktree), "--force alone removed the worktree")
    _, branches, _ = git(repo, "branch", "--list")
    check(slug in branches, "--force alone deleted the branch")

    code, out, err = call(worktree_script, "discard", "--board", "BOARD-902",
                           "--force", "--yes")
    check(code == 0, "--force --yes failed: %s%s" % (out, err))
    check(not os.path.exists(worktree), "--force --yes left the worktree behind")
    _, branches, _ = git(repo, "branch", "--list")
    check(slug not in branches, "--force --yes left the branch behind")

    _, common, _ = git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")
    patches = [name for name in os.listdir(os.path.join(common, "cleanup-wt"))
               if name.endswith(".patch")]
    check(len(patches) == 1, "expected one recovery patch, found %d" % len(patches))
    if patches:
        patch_path = os.path.join(common, "cleanup-wt", patches[0])
        check(patch_path in out, "the output does not print the patch path")
        with open(patch_path, encoding="utf-8") as fh:
            patch = fh.read()
        check("work that will be destroyed" in patch,
              "the recovery patch does not hold the uncommitted content")

    force_unmerged(repo, worktree_script, call, check)


def force_unmerged(repo, worktree_script, call, check):
    """The forced discard of a branch with a commit the base does not have."""
    code, out, err = call(worktree_script, "create", "--board", "BOARD-903")
    check(code == 0, "create failed for BOARD-903: %s%s" % (out, err))
    slug = "force-an-unmerged-branch-away"
    worktree = os.path.join(repo, ".opencode", "worktrees", slug)
    check(os.path.isdir(worktree), "the BOARD-903 worktree was not created")
    write(os.path.join(worktree, "kept.txt"), "committed on the branch\n")
    git(worktree, "add", "-A")
    git(worktree, "commit", "-m", "a commit the base does not have")
    _, commit_sha, _ = git(worktree, "rev-parse", "HEAD")

    code, out, err = call(worktree_script, "discard", "--board", "BOARD-903", "--apply")
    check(code != 0, "discard --apply accepted a branch with an unmerged commit")

    code, out, err = call(worktree_script, "discard", "--board", "BOARD-903", "--force", "--yes")
    check(code == 0, "--force --yes failed: %s%s" % (out, err))
    check(commit_sha in out, "the output does not print the commit sha")
    check(not os.path.exists(worktree), "--force --yes left the worktree behind")
    _, branches, _ = git(repo, "branch", "--list")
    check(slug not in branches, "--force --yes left the branch behind")

    _, common, _ = git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")
    tsvs = [name for name in os.listdir(os.path.join(common, "cleanup-wt"))
            if name.endswith(".tsv")]
    check(bool(tsvs), "no recovery TSV was written")
    found = False
    for name in tsvs:
        with open(os.path.join(common, "cleanup-wt", name), encoding="utf-8") as fh:
            if commit_sha in fh.read():
                found = True
    check(found, "the recovery TSV does not hold the commit sha")


if __name__ == "__main__":
    sys.exit(main())
