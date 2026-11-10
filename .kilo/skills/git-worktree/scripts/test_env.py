#!/usr/bin/env python3
"""Self-test for the env provisioning and the worktree reuse rules.

    python3 .kilo/skills/git-worktree/scripts/test_env.py

The test builds a throwaway git repository under a temp directory, copies the
scripts into it, and drives them the way an agent would. It never touches this
repository's board, worktrees or branches.

Exit codes: 0 ok, 1 a check failed.
"""
import os
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
        target = os.path.join(repo, ".kilo", "skills", group, "scripts")
        os.makedirs(target)
        for name in os.listdir(os.path.join(REPO_SCRIPTS, group, "scripts")):
            if name.endswith(".py"):
                shutil.copyfile(os.path.join(REPO_SCRIPTS, group, "scripts", name),
                                os.path.join(target, name))
    write(os.path.join(repo, ".kilo", "repos.json"), '{\n  "control": "."\n}\n')
    write(os.path.join(repo, "docs", "BOARD.md"), (
        "| ID | Task | Type | Status | Priority | Risk | Blocked by | Repos | "
        "Branch/Worktree | Notes |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
        "| BOARD-900 | Provision env files in the scratch repo | Feature | Ready | P2 | "
        "test | None. | control | - | test row |\n"))
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


def main():
    base = tempfile.mkdtemp(prefix="factory-env-test-")
    repo = make_repo(base)
    worktree_script = os.path.join(repo, ".kilo", "skills", "git-worktree", "scripts",
                                   "worktree.py")
    env_script = os.path.join(repo, ".kilo", "skills", "git-worktree", "scripts", "env.py")
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
    worktree = os.path.join(repo, ".kilo", "worktrees", slug)
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
    check(code != 0, "sync accepted a destination outside .kilo/worktrees/")

    code, out, err = call(worktree_script, "resume", "--board", "BOARD-900")
    check(code == 0, "resume failed: %s%s" % (out, err))
    check(os.path.isdir(worktree), "resume removed the worktree")
    with open(os.path.join(repo, "docs", "BOARD.md"), encoding="utf-8") as fh:
        check("In Progress" in fh.read(), "resume did not put the row back in progress")
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
    with open(os.path.join(repo, "docs", "BOARD.md"), encoding="utf-8") as fh:
        check(".kilo/worktrees/%s" % slug not in fh.read(),
              "discard did not clear the row's worktree cell")

    code, out, err = call(worktree_script, "list")
    check(code == 0, "list failed: %s%s" % (out, err))
    check("state" in out, "list has no state column")

    joined = "".join(outputs)
    check(MARKER not in joined, "the secret value appeared in the script output")

    shutil.rmtree(base, ignore_errors=True)
    if FAILURES:
        print("%d check(s) failed" % len(FAILURES))
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
