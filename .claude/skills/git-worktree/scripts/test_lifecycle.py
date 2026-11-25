import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parent
SOURCE = SCRIPTS.parents[3]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


WORKTREE = module("lifecycle_test_worktree", SCRIPTS / "worktree.py")
ENV = module("lifecycle_test_env", SCRIPTS / "env.py")
GUARD = module("lifecycle_test_guard", SCRIPTS / "guard.py")


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="lifecycle-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "control"
        self.root.mkdir()
        for relative in (".claude/skills/git-worktree/scripts/worktree.py",
                         ".claude/skills/git-worktree/scripts/env.py",
                         ".claude/skills/git-worktree/scripts/guard.py",
                         ".claude/skills/git-worktree/scripts/scope.py",
                         ".claude/skills/board/scripts/board.py",
                         ".claude/policies/git-policy.json"):
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / relative, destination)
        # Generated, not copied: the developer's own settings file is ignored local tooling.
        self.policy = GUARD.load_policy(str(self.root / GUARD.POLICY_REL))
        self.settings_path = self.root / GUARD.CONFIG_REL
        settings, error = GUARD.write_settings(str(self.settings_path), self.policy, create_missing=True)
        self.assertIsNotNone(settings, error)
        (self.root / "docs").mkdir()
        (self.root / ".claude/repos.json").write_text('{"control": "."}\n')
        (self.root / ".gitignore").write_text(
            ".claude/worktrees/\n.claude/local/qa-navigation.json\n.env*\n!.env.example\n"
            "__pycache__/\napps/\n")
        self.board = module("test_board", self.root / ".claude/skills/board/scripts/board.py")
        self.rows = []
        self.add_row("BOARD-001", "Shared lifecycle")
        self.initialize(self.root)
        self.script = self.root / ".claude/skills/git-worktree/scripts/worktree.py"
        self.guard = self.root / ".claude/skills/git-worktree/scripts/guard.py"

    def git(self, root, *args, check=True):
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        env.update(GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1")
        result = subprocess.run(["git", "-C", str(root), "-c", "user.name=Lifecycle Test",
                                 "-c", "user.email=lifecycle@example.invalid", "-c",
                                 "core.hooksPath=/dev/null", *args], text=True,
                                capture_output=True, env=env, timeout=30)
        if check:
            self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def initialize(self, root):
        self.git(root, "init", "-b", "main")
        self.git(root, "config", "user.name", "Lifecycle Test")
        self.git(root, "config", "user.email", "lifecycle@example.invalid")
        self.git(root, "config", "core.hooksPath", "/dev/null")
        self.git(root, "config", "commit.gpgSign", "false")
        (root / "data.txt").write_text("initial\n")
        self.commit(root)

    def commit(self, root):
        self.git(root, "add", ".")
        self.git(root, "commit", "-m", "test fixture")

    def add_row(self, board_id, task, kind="Feature", blocked="None.", repos="control"):
        self.rows.append([board_id, task, kind, "Ready", "P2", "low", blocked, repos, "-", "test"])
        self.write_board()

    def write_board(self):
        text = "| " + " | ".join(self.board.COLUMNS) + " |\n"
        text += "| " + " | ".join(["---"] * len(self.board.COLUMNS)) + " |\n"
        text += "".join("| " + " | ".join(row) + " |\n" for row in self.rows)
        (self.root / "docs/BOARD.md").write_text(text)

    def set_status(self, board_id, status):
        path = self.root / "docs/BOARD.md"
        table, error = self.board.read_table(path)
        self.assertIsNone(error)
        index = self.board.row_by_id(table, board_id)
        lines = table["lines"]
        lines[index] = self.board.replace_cell(lines[index], 3, status)
        self.board.write_atomic(path, lines)

    def status(self, board_id="BOARD-001"):
        table, error = self.board.read_table(self.root / "docs/BOARD.md")
        self.assertIsNone(error)
        index = self.board.row_by_id(table, board_id)
        return self.board.cell_texts(table["lines"], index)[3]

    def cli(self, *args, success=True, cwd=None, guard=False):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", GIT_CONFIG_GLOBAL="/dev/null",
                   GIT_CONFIG_NOSYSTEM="1")
        result = subprocess.run([sys.executable, str(self.guard if guard else self.script), *args],
                                cwd=cwd or self.root, text=True, capture_output=True, env=env, timeout=30)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def settings_match(self, checkout):
        config, _ = GUARD.load_config(str(checkout / GUARD.CONFIG_REL))
        return GUARD.settings_match(config, self.policy)

    def hook(self, tool, tool_input, cwd=None, raw=None):
        """The decision the guard hook prints for one PreToolUse event, or None for allow."""
        cwd = cwd or self.root
        event = raw if raw is not None else json.dumps(
            {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input, "cwd": str(cwd)})
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", GIT_CONFIG_GLOBAL="/dev/null",
                   GIT_CONFIG_NOSYSTEM="1")
        result = subprocess.run([sys.executable, str(self.guard), "hook"], cwd=cwd, input=event,
                                text=True, capture_output=True, env=env, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        if not result.stdout.strip():
            return None
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertTrue(output["permissionDecisionReason"])
        return output["permissionDecision"]

    def create(self, board_id="BOARD-001", repo="control", change=True):
        self.cli("create", "--board", board_id, "--repo", repo)
        root = self.root if repo == "control" else self.root / "apps" / repo
        path = root / ".claude/worktrees/shared-lifecycle"
        if change:
            (path / "data.txt").write_text("feature\n")
            self.commit(path)
        return path

    def add_repo(self, name):
        path = self.root / "apps" / name
        path.mkdir(parents=True)
        (path / ".gitignore").write_text(".claude/worktrees/\n")
        self.initialize(path)
        mapping = json.loads((self.root / ".claude/repos.json").read_text())
        mapping[name] = "apps/" + name
        (self.root / ".claude/repos.json").write_text(json.dumps(mapping))
        self.commit(self.root)
        return path

    def test_create_from_legacy_title_does_not_rename_task_or_override_slug(self):
        legacy = '\U0001f680 [feat] inhouz_agentic_ms: add kus deployment manifests'
        self.add_row('BOARD-002', legacy)
        self.add_row('BOARD-003', legacy)
        self.cli('create', '--board', 'BOARD-002')
        self.cli('create', '--board', 'BOARD-003', '--new', '--slug', 'add-custom')
        self.cli('resume', '--board', 'BOARD-003')
        for board_id, slug in [('BOARD-002', 'added-kus-deployment-manifests'), ('BOARD-003', 'add-custom')]:
            path = self.root / '.claude/worktrees' / slug
            self.assertEqual(self.git(path, 'branch', '--show-current').stdout.strip(), 'feat/' + slug)
            self.assertIn(f'| {board_id} | {legacy} |', (self.root / 'docs/BOARD.md').read_text())

    def test_mode_is_local_persistent_and_leaves_settings_unchanged(self):
        self.assertIn("required", self.cli("mode", "status").stdout)
        settings = self.settings_path.read_bytes()
        self.git(self.root, "checkout", "-b", "feat/current")
        self.cli("check-git", "--", "git commit -m test", guard=True, success=False)
        self.assertEqual(self.hook("Edit", {"file_path": str(self.root / "data.txt")}), "ask")
        output = self.cli("mode", "optional").stdout
        self.assertIn("no restart is needed", output)
        self.assertNotIn("Restart", output)
        self.cli("check-git", "--", "git commit -m test", guard=True)
        self.assertIsNone(self.hook("Edit", {"file_path": str(self.root / "data.txt")}))
        self.assertEqual(self.hook("Edit", {"file_path": str(self.root / "docs/BOARD.md")}), "deny")
        self.assertEqual(self.hook("Edit", {"file_path": str(self.root / ".env")}), "deny")
        self.assertEqual(self.hook("Edit", {"file_path": str(self.root / "CLAUDE.md")}), "ask")
        self.assertEqual(self.settings_path.read_bytes(), settings)
        self.cli("check-policy", guard=True)
        self.git(self.root, "checkout", "main")
        self.cli("check-git", "--", "git commit -m test", guard=True, success=False)
        self.cli("mode", "required")
        self.assertEqual(self.settings_path.read_bytes(), settings)
        self.assertEqual(self.hook("Edit", {"file_path": str(self.root / "data.txt")}), "ask")
        other = Path(self.temporary.name) / "other"
        other.mkdir()
        self.initialize(other)
        self.assertEqual(WORKTREE.local_state(str(other))["mode"], "required")

    def test_skip_worktree_mode_matrix_never_changes_assignment(self):
        for number, kind in enumerate(("Fix", "Chore", "Docs", "Research"), start=2):
            self.add_row("BOARD-%03d" % number, kind + " task", kind)
        self.git(self.root, "switch", "-c", "maintenance/local")
        for mode in ("required", "optional", "adaptive"):
            self.cli("mode", mode)
            board_path = self.root / "docs/BOARD.md"
            state_path = self.root / ".git/claude-workspace.json"
            paths = (board_path, state_path, self.settings_path)
            before = [path.read_bytes() for path in paths]
            for number in range(1, 6):
                eligible = mode != "required" and number in (2, 3, 4)
                with self.subTest(mode=mode, number=number):
                    response = self.cli("create", "--board", "BOARD-%03d" % number,
                                        "--skip-worktree", success=eligible)
                    if eligible:
                        self.assertIn("no workspace created or recorded", response.stdout)
                    else:
                        self.assertIn("cannot skip", response.stderr)
            self.assertEqual(before, [path.read_bytes() for path in paths])
            self.assertFalse((self.root / ".claude/worktrees").exists())
            self.assertEqual(self.git(self.root, "branch", "--show-current").stdout.strip(), "maintenance/local")

    def test_adaptive_skip_refuses_unsafe_targets_and_conflicting_options(self):
        api = self.add_repo("api")
        self.add_row("BOARD-002", "Small adjustment", "Docs", repos="api")
        self.cli("mode", "adaptive")
        args = ("create", "--board", "BOARD-002", "--skip-worktree")
        self.assertIn("does not assign", self.cli(*args, success=False).stderr)
        args += ("--repo", "api")
        self.assertIn("primary checkout", self.cli(*args, success=False).stderr)
        self.assertIn("protected branch", self.cli(*args, cwd=api, success=False).stderr)
        self.git(api, "checkout", "--detach")
        self.assertIn("detached HEAD", self.cli(*args, cwd=api, success=False).stderr)
        self.git(api, "switch", "-c", "docs/local")
        self.cli(*args, cwd=api)
        for options in (("--reuse", "BOARD-001"), ("--new",), ("--base", "main"), ("--slug", "other")):
            self.assertIn("cannot be combined", self.cli(*args, *options, cwd=api, success=False).stderr)
        self.cli("create", "--board", "BOARD-002", "--repo", "api")
        self.write_board()  # Simulate a lost board link, not a lost Git assignment.
        self.assertIn("resume", self.cli(*args, cwd=api, success=False).stderr)

    def test_adaptive_unscoped_commit_needs_managed_worktree(self):
        self.cli("mode", "adaptive")
        self.git(self.root, "switch", "-c", "docs/local")
        args = ("check-git", "--", "git commit -m test")
        self.assertIn("no board-row context", self.cli(*args, guard=True, success=False).stdout)
        path = self.create(change=False)
        self.cli(*args, guard=True, cwd=path)
        lookalike = self.root / "elsewhere/.claude/worktrees/lookalike"
        self.git(self.root, "worktree", "add", "-b", "docs/lookalike", str(lookalike))
        self.cli(*args, guard=True, cwd=lookalike, success=False)

    def test_skip_refuses_blocked_row_closed_row_and_stale_or_missing_settings(self):
        self.add_row("BOARD-002", "Maintenance", "Fix", blocked="BOARD-001")
        self.git(self.root, "switch", "-c", "fix/current")
        self.cli("mode", "adaptive")
        args = ("create", "--board", "BOARD-002", "--skip-worktree")
        self.assertIn("dependency", self.cli(*args, success=False).stderr)
        self.rows[-1][6] = "- None."
        self.write_board()
        self.set_status("BOARD-002", "Merged")
        self.assertIn("Ready or In Progress", self.cli(*args, success=False).stderr)
        self.set_status("BOARD-002", "In Progress")
        original = self.settings_path.read_bytes()
        config = json.loads(original)
        config["hooks"]["PreToolUse"] = []
        self.settings_path.write_text(json.dumps(config))
        self.assertIn("out of sync", self.cli(*args, success=False).stderr)
        self.assertEqual(config, json.loads(self.settings_path.read_text()))
        self.settings_path.write_text("{malformed")
        self.assertIn("out of sync", self.cli(*args, success=False).stderr)
        self.assertEqual(self.settings_path.read_text(), "{malformed")
        self.settings_path.unlink()
        self.assertIn("settings missing", self.cli(*args, success=False).stderr)
        self.assertFalse(self.settings_path.exists())
        self.settings_path.write_bytes(original)
        self.assertIn("no workspace created or recorded", self.cli(*args).stdout)

    def test_guard_resolves_git_C_and_denies_missing_context(self):
        path = self.create(change=False)
        self.cli("check-git", "--", "git commit -m test", cwd=path, guard=True)
        self.cli("check-git", "--", "git -C %s commit -m test" % self.root,
                 cwd=path, guard=True, success=False)
        self.cli("mode", "optional", cwd=path)
        for arguments in ("-C%s" % self.root, "-C ../../..", "-C../ -C ../..",
                          "-C .. -C../..", '-C "" -C../../..'):
            with self.subTest(arguments=arguments):
                result = self.cli("check-git", "--", "git %s commit -m test" % arguments,
                                  cwd=path, guard=True, success=False)
                self.assertIn("blocked:", result.stdout)
        for arguments in ("-C", "-c", "--config-env", "--git-dir=.git", "--work-tree ."):
            with self.subTest(arguments=arguments):
                self.cli("check-git", "--", "git " + arguments, cwd=path, guard=True, success=False)
        # A bare repo stops Git discovery even when TMPDIR is inside another checkout.
        bare = Path(self.temporary.name) / "no-working-tree.git"
        self.git(self.root, "init", "--bare", str(bare))
        result = self.cli("check-git", "--", "git commit -m test", cwd=bare,
                          guard=True, success=False)
        self.assertIn("not inside a git repository; refusing operation", result.stderr)
        result = self.cli("check-git", "--", "git -C %s commit -m test" % shlex.quote(str(bare)),
                          cwd=path, guard=True, success=False)
        self.assertIn("cannot establish git repository context", result.stderr)

    def test_nested_primary_is_not_a_managed_link(self):
        checkout = self.create(change=False)
        nested = checkout / "separate"
        nested.mkdir()
        self.initialize(nested)
        self.git(nested, "switch", "-c", "fix/local")
        self.assertTrue(GUARD.repo_context(str(checkout))["linked"])
        self.assertFalse(GUARD.repo_context(str(nested))["linked"])
        self.cli("check-git", "--", "git commit -m test", cwd=nested, guard=True, success=False)

    def test_guard_rejects_directory_chains_without_executing_commits(self):
        path = self.create(change=False)
        before = self.git(self.root, "rev-parse", "HEAD").stdout
        direct = "git -C . commit -m example"
        commands = (
            "cd %s && %s" % (self.root, direct),
            "cd %s; %s" % (self.root, direct),
            "pushd %s && %s" % (self.root, direct),
            "popd; " + direct,
            "(cd %s && %s)" % (self.root, direct),
            "{ cd %s; %s; }" % (self.root, direct),
            "builtin cd %s && %s" % (self.root, direct),
            "command -- cd %s && %s" % (self.root, direct),
            "bash -c 'cd %s && %s'" % (self.root, direct),
            "env --chdir=%s %s" % (self.root, direct),
            "sudo -D %s %s" % (self.root, direct),
            "git status && cd %s; %s" % (self.root, direct),
            'echo "$(cd %s && %s)"' % (self.root, direct),
        )
        for command in commands:
            with self.subTest(command=command):
                result = self.cli("check-git", "--", command, cwd=path, guard=True, success=False)
                self.assertIn("manual review" if "$(" in command else "directory-changing shell chain",
                              result.stderr)
        for command in ("git commit -m cd", "git -C . commit -m example",
                        "git -C. commit -m example", 'git -C.. -C shared-lifecycle -C "" commit -m example',
                        "pwd && git -C. commit -m example"):
            self.cli("check-git", "--", command, cwd=path, guard=True)
        self.assertEqual(self.git(self.root, "rev-parse", "HEAD").stdout, before)

    def test_create_gives_worktree_matching_settings_in_every_mode(self):
        base = self.git(self.root, "show", "main:" + GUARD.CONFIG_REL).stdout
        main_config = self.settings_path.read_bytes()
        for number, mode in enumerate(("required", "optional", "adaptive"), start=2):
            with self.subTest(mode=mode):
                self.cli("mode", mode)
                board_id = "BOARD-%03d" % number
                self.add_row(board_id, "Settings " + mode)
                self.cli("create", "--board", board_id, "--new")
                path = self.root / ".claude/worktrees" / ("settings-" + mode)
                self.assertTrue(self.settings_match(path))
                self.assertEqual((path / GUARD.CONFIG_REL).read_bytes(), main_config)
                self.assertEqual(self.settings_path.read_bytes(), main_config)
                self.assertEqual(self.git(self.root, "show", "main:" + GUARD.CONFIG_REL).stdout, base)

    def test_create_writes_settings_when_primary_settings_are_untracked(self):
        self.git(self.root, "rm", "--cached", "--quiet", GUARD.CONFIG_REL)
        with (self.root / ".gitignore").open("a") as ignore_file:
            ignore_file.write(".claude/settings.json\n")
        self.commit(self.root)
        main_config = self.settings_path.read_bytes()
        path = self.create(change=False)
        self.assertTrue(self.settings_match(path))
        self.git(path, "check-ignore", GUARD.CONFIG_REL)
        self.assertEqual(self.settings_path.read_bytes(), main_config)
        self.assertEqual(self.git(path, "status", "--porcelain").stdout, "")

    def test_create_copies_local_environment_and_navigation_without_exposing_values(self):
        secret_value = "do-not-print-this-secret"
        (self.root / ".env.local").write_text(secret_value)
        (self.root / ".env.example").write_text("example")
        (self.root / "nested").mkdir()
        (self.root / "nested/.env.production").write_text("nested-secret")
        os.chmod(self.root / "nested/.env.production", 0o640)
        (self.root / ".claude/local").mkdir(parents=True)
        navigation = self.root / ".claude/local/qa-navigation.json"
        navigation.write_text('{"approved":true,"steps":[]}')
        result = self.cli("create", "--board", "BOARD-001")
        path = self.root / ".claude/worktrees/shared-lifecycle"
        self.assertTrue((path / ".env.local").read_text() == secret_value)
        self.assertTrue((path / "nested/.env.production").read_text() == "nested-secret")
        self.assertEqual((path / "nested/.env.production").stat().st_mode & 0o777, 0o640)
        self.assertFalse((path / ".env.example").exists())
        self.assertEqual((path / ".claude/local/qa-navigation.json").read_bytes(), navigation.read_bytes())
        self.assertNotIn(secret_value, result.stdout + result.stderr)

    def test_env_status_reports_the_same_eligible_recursive_sources(self):
        (self.root / ".env").write_text("root-secret")
        (self.root / ".env.tracked").write_text("tracked")
        self.git(self.root, "add", "-f", ".env.tracked")
        self.git(self.root, "commit", "-m", "track env fixture")
        (self.root / ".env.local").write_text("local-secret")
        (self.root / "nested").mkdir()
        (self.root / "nested/.env.production").write_text("nested-secret")
        (self.root / ".env.example").write_text("example")
        (self.root / ".env.link").symlink_to(self.root / ".env.local")
        self.cli("create", "--board", "BOARD-001")
        path = self.root / ".claude/worktrees/shared-lifecycle"

        lines, error = ENV.status_into(str(path), str(self.root))
        self.assertIsNone(error)
        output = "\n".join(lines)
        self.assertIn(".env | main checkout: present | worktree: present", output)
        self.assertIn(".env.local | main checkout: present | worktree: present", output)
        self.assertIn("nested/.env.production | main checkout: present | worktree: present", output)
        self.assertNotIn(".env.example", output)
        self.assertNotIn(".env.tracked", output)
        self.assertNotIn(".env.link", output)
        self.assertNotIn("root-secret", output)
        self.assertNotIn("nested-secret", output)

    def test_local_file_provisioning_skips_tracked_unignored_symlink_and_existing_destination(self):
        (self.root / ".env.tracked").write_text("tracked")
        self.git(self.root, "add", "-f", ".env.tracked")
        self.git(self.root, "commit", "-m", "track env fixture")
        with (self.root / ".gitignore").open("a") as ignore_file:
            ignore_file.write("!public/.env.open\n")
        (self.root / "public").mkdir()
        (self.root / "public/.env.open").write_text("not ignored")
        source = self.root / ".env.local"
        source.write_text("source")
        target = self.root / WORKTREE.WORKTREES_DIR / "copy"
        self.git(self.root, "worktree", "add", str(target), "-b", "feat/copy", "main")
        (target / ".env.tracked").unlink()
        (target / ".env.local").write_text("keep")
        (self.root / ".env.link").symlink_to(source)
        WORKTREE.provision_local_files(self.root, target)
        self.assertEqual((target / ".env.local").read_text(), "keep")
        self.assertFalse((target / ".env.tracked").exists())
        self.assertEqual((target / "public/.env.open").read_text(), "not ignored")
        self.assertFalse((target / ".env.link").exists())

    def test_create_regenerates_stale_base_settings_without_modifying_base(self):
        config = json.loads(self.settings_path.read_text())
        config["permissions"]["deny"].reverse()
        config["model"] = "fixture-model"
        self.settings_path.write_text(json.dumps(config))
        self.commit(self.root)
        self.cli("check-policy", guard=True, success=False)
        base = self.git(self.root, "show", "main:" + GUARD.CONFIG_REL).stdout
        main_config = self.settings_path.read_bytes()
        path = self.create(change=False)
        regenerated = json.loads((path / GUARD.CONFIG_REL).read_text())
        self.assertTrue(GUARD.settings_match(regenerated, self.policy))
        self.assertEqual(regenerated["model"], "fixture-model")
        self.assertEqual(self.settings_path.read_bytes(), main_config)
        self.assertEqual(self.git(self.root, "show", "main:" + GUARD.CONFIG_REL).stdout, base)

    def test_create_app_writes_own_settings_without_app_instructions_or_harness_copy(self):
        api = self.add_repo("api")
        (api / ".claude/local").mkdir(parents=True)
        navigation = api / ".claude/local/qa-navigation.json"
        navigation.write_text('{"approved":true,"steps":[]}')
        scopes = self.root / ".claude/scopes"
        scopes.mkdir()
        (scopes / "api.md").write_text("# Fixture scope\n")
        self.cli("sync", "--repo", "api", "--apply", guard=True)
        self.assertFalse((api / "CLAUDE.md").exists())
        self.cli("mode", "optional")
        main_config = self.settings_path.read_bytes()
        base = self.git(api, "rev-parse", "HEAD").stdout
        path = self.create(repo="api", change=False)
        # Claude Code does not inherit an ancestor's settings, so the app worktree carries its own.
        self.assertTrue(self.settings_match(path))
        self.assertFalse((api / GUARD.CONFIG_REL).exists())
        self.assertEqual((path / ".claude/local/qa-navigation.json").read_bytes(), navigation.read_bytes())
        self.assertEqual({entry.name for entry in (path / ".claude").iterdir()}, {"local", "settings.json"})
        self.assertFalse((path / "CLAUDE.md").exists())
        self.assertFalse((api / "CLAUDE.md").exists())
        self.assertNotEqual(self.git(api, "check-ignore", "CLAUDE.md", check=False).returncode, 0)
        for name in (".claude/local/qa-navigation.json", GUARD.CONFIG_REL):
            self.git(path, "check-ignore", name)
        self.assertEqual(self.settings_path.read_bytes(), main_config)
        self.assertEqual(self.git(api, "rev-parse", "HEAD").stdout, base)
        self.assertEqual(self.hook("Bash", {"command": "git push"}, cwd=path), "deny")

    def test_sync_and_create_preserve_handwritten_app_instructions(self):
        app = self.add_repo("inventory")
        instructions = app / "CLAUDE.md"
        instructions.write_text("# Existing application instructions\n")
        self.commit(app)
        main_config = self.settings_path.read_bytes()
        preview = self.cli("sync", "--repo", "inventory", guard=True)
        self.assertNotIn("CLAUDE.md", preview.stdout)
        self.cli("sync", "--repo", "inventory", "--apply", guard=True)
        path = self.create(repo="inventory", change=False)
        for checkout in (app, path):
            self.assertEqual((checkout / "CLAUDE.md").read_text(),
                             "# Existing application instructions\n")
        self.assertFalse((app / GUARD.CONFIG_REL).exists())
        self.assertTrue(self.settings_match(path))
        self.assertEqual(self.settings_path.read_bytes(), main_config)

    def test_control_only_template_map_and_empty_apps_validate_without_scopes(self):
        (self.root / ".claude/repos.json").write_text('{"control": "."}\n')
        self.assertEqual(WORKTREE.load_repos(str(self.root)), ({"control": "."}, None))
        self.assertFalse((self.root / "apps").exists())
        self.cli("check-repos", guard=True)
        (self.root / "apps").mkdir()
        self.cli("check-repos", guard=True)
        self.cli("sync", "--repo", "control", "--apply", guard=True)
        self.assertEqual(list((self.root / "apps").iterdir()), [])
        self.assertFalse((self.root / ".claude/scopes").exists())
        self.assertFalse((self.root / ".claude/catalog").exists())
        self.assertEqual(json.loads((self.root / ".claude/repos.json").read_text()), {"control": "."})
        self.cli("check-policy", guard=True)
        self.add_repo("inventory")
        self.cli("check-repos", guard=True)
        unregistered = self.root / "apps/unregistered"
        unregistered.mkdir()
        self.git(unregistered, "init")
        result = self.cli("check-repos", guard=True, success=False)
        self.assertIn("apps/unregistered is a git repository but is not registered", result.stderr)

    def test_sync_bootstraps_project_harness_without_scope_or_catalog_propagation(self):
        self.assertEqual(GUARD.SYNC_SLICE, ["agents", "commands", "skills", "policies"])
        skill = Path(".claude/skills/engineering-practices")
        shutil.copytree(SOURCE / skill, self.root / skill)
        axe = Path(".claude/skills/qa-review/vendor/axe-core")
        shutil.copytree(SOURCE / axe, self.root / axe)
        for folder in ("agents", "commands", "scopes", "catalog"):
            source = self.root / ".claude" / folder
            source.mkdir(exist_ok=True)
            (source / "fixture.md").write_text(folder + " fixture\n")
        shutil.copyfile(SOURCE / ".claude/.gitignore", self.root / ".claude/.gitignore")
        project = self.root / "new-project"
        (project / ".claude").mkdir(parents=True)
        (project / "docs").mkdir()
        (project / ".claude/repos.json").write_text('{"control": "."}\n')
        for relative in (".gitignore", "CLAUDE.md"):
            shutil.copyfile(SOURCE / "templates/project" / relative, project / relative)
        (project / "docs/BOARD.md").write_bytes((self.root / "docs/BOARD.md").read_bytes())
        (project / "apps").mkdir()
        self.git(project, "init")
        (project / axe).mkdir(parents=True)
        (project / axe / "axe.min.js").write_text("previous distribution\n")
        (self.root / ".claude/repos.json").write_text('{"control":".","new-project":"new-project"}')
        instructions = (project / "CLAUDE.md").read_bytes()
        before = {path.relative_to(project): path.read_bytes()
                  for path in project.rglob("*") if path.is_file()}
        preview = self.cli("sync", "--repo", "new-project", guard=True)
        self.assertNotIn("CLAUDE.md", preview.stdout)
        self.assertEqual(before, {path.relative_to(project): path.read_bytes()
                                  for path in project.rglob("*") if path.is_file()})
        self.cli("sync", "--repo", "new-project", "--apply", guard=True)
        for folder in GUARD.SYNC_SLICE:
            for source in (self.root / ".claude" / folder).rglob("*"):
                if source.is_file() and "__pycache__" not in source.parts:
                    destination = project / source.relative_to(self.root)
                    self.assertEqual(source.read_bytes(), destination.read_bytes())
        self.assertEqual((project / ".claude/.gitignore").read_bytes(),
                         (self.root / ".claude/.gitignore").read_bytes())
        self.assertEqual((project / "CLAUDE.md").read_bytes(), instructions)
        self.assertEqual(json.loads((project / ".claude/repos.json").read_text()), {"control": "."})
        self.assertFalse((project / ".claude/scopes").exists())
        self.assertFalse((project / ".claude/catalog").exists())
        self.assertEqual(list((project / "apps").iterdir()), [])
        self.assertEqual(self.git(project, "rev-list", "--all").stdout, "")
        self.cli("check-policy", cwd=project, guard=True)
        self.assertTrue(self.settings_match(project))
        self.cli("check-repos", cwd=project, guard=True)

    def test_create_app_writes_matching_settings_in_both_modes(self):
        for mode in ("optional", "required"):
            with self.subTest(mode=mode):
                self.cli("mode", mode)
                repo = "api-" + mode
                api = self.add_repo(repo)
                main_config = self.settings_path.read_bytes()
                base = self.git(api, "rev-parse", "HEAD").stdout
                self.cli("check-policy", guard=True)
                path = self.create(repo=repo, change=False)
                self.assertTrue(self.settings_match(path))
                self.assertFalse((api / GUARD.CONFIG_REL).exists())
                self.assertEqual(self.settings_path.read_bytes(), main_config)
                self.assertEqual(self.git(api, "rev-parse", "HEAD").stdout, base)
                self.assertEqual(self.status(), "In Progress")

    def test_create_app_regenerates_stale_committed_settings_without_modifying_base(self):
        api = self.add_repo("api")
        config = json.loads(self.settings_path.read_text())
        config["permissions"]["allow"].reverse()
        (api / ".claude").mkdir()
        (api / GUARD.CONFIG_REL).write_text(json.dumps(config))
        self.commit(api)
        self.assertFalse(self.settings_match(api))
        main_config = (api / GUARD.CONFIG_REL).read_bytes()
        base = self.git(api, "show", "main:" + GUARD.CONFIG_REL).stdout
        path = self.create(repo="api", change=False)
        self.assertTrue(self.settings_match(path))
        self.assertEqual((api / GUARD.CONFIG_REL).read_bytes(), main_config)
        self.assertEqual(self.git(api, "show", "main:" + GUARD.CONFIG_REL).stdout, base)
        self.assertEqual({entry.name for entry in (path / ".claude").iterdir()}, {"settings.json"})

    def test_create_invalid_map_reports_partial_and_preserves_new_workspace(self):
        self.settings_path.write_text("{invalid")
        self.commit(self.root)
        board = (self.root / "docs/BOARD.md").read_bytes()
        result = self.cli("create", "--board", "BOARD-001", success=False)
        self.assertIn("creation incomplete", result.stderr)
        path = self.root / ".claude/worktrees/shared-lifecycle"
        self.assertTrue(path.is_dir())
        self.git(self.root, "rev-parse", "--verify", "refs/heads/feat/shared-lifecycle")
        self.assertIn("settings initialization failed", result.stderr)
        self.assertEqual((path / GUARD.CONFIG_REL).read_text(), "{invalid")
        self.assertEqual(self.settings_path.read_text(), "{invalid")
        self.assertEqual((self.root / "docs/BOARD.md").read_bytes(), board)
        self.assertEqual(self.status(), "Ready")
        self.assertIn("settings initialization failed", WORKTREE.local_state(str(self.root))["workspaces"][str(path)]["error"])

    def test_fix_reuses_parent_and_discard_updates_all_shared_rows(self):
        self.add_row("BOARD-002", "Fix shared lifecycle", "Fix", "BOARD-001")
        path = self.create()
        self.cli("create", "--board", "BOARD-002", "--reuse", "BOARD-001")
        self.assertEqual(len(WORKTREE.list_worktrees(str(self.root))), 2)
        (path / "dirty.txt").write_text("uncommitted")
        self.cli("discard", "--board", "BOARD-002")
        self.assertTrue(path.exists())
        self.cli("discard", "--board", "BOARD-002", "--apply", success=False)
        self.assertTrue(path.exists())
        self.cli("discard", "--board", "BOARD-002", "--apply", "--discard")
        self.assertFalse(path.exists())
        self.assertEqual(self.status(), "Dropped")
        self.assertEqual(self.status("BOARD-002"), "Dropped")
        self.assertNotEqual(self.git(self.root, "rev-parse", "--verify", "refs/heads/feat/shared-lifecycle", check=False).returncode, 0)

    def test_merge_refuses_dirty_source_target_and_control_untracked(self):
        path = self.create()
        self.set_status("BOARD-001", "Pending Merge")
        for checkout, relative in ((path, "untracked.txt"), (self.root, "untracked.txt"),
                                   (self.root, "data.txt")):
            original = (checkout / relative).read_text() if (checkout / relative).exists() else None
            (checkout / relative).write_text("dirty\n")
            self.cli("merge", "--board", "BOARD-001", "--apply", success=False)
            self.assertTrue(path.exists())
            if original is None:
                (checkout / relative).unlink()
            else:
                (checkout / relative).write_text(original)
        self.cli("merge", "--board", "BOARD-001")
        self.assertTrue(path.exists())
        self.cli("merge", "--board", "BOARD-001", "--apply")
        self.assertEqual(self.status(), "Merged")
        self.assertEqual((self.root / "data.txt").read_text(), "feature\n")
        self.assertFalse(path.exists())

    def test_review_readiness_and_ahead_are_required(self):
        path = self.create(change=False)
        self.cli("merge", "--board", "BOARD-001", success=False)
        self.set_status("BOARD-001", "Pending Merge")
        self.assertIn("no commits ahead", self.cli("merge", "--board", "BOARD-001", success=False).stderr)
        self.assertTrue(path.exists())

    def test_multi_repo_success_and_partial_discard(self):
        self.add_repo("api")
        one = self.create()
        two = self.create(repo="api")
        self.set_status("BOARD-001", "Pending Merge")
        self.cli("merge", "--board", "BOARD-001", "--repo", "api", "--apply")
        self.assertEqual(self.status(), "Pending Merge")
        self.assertTrue(one.exists())
        self.assertFalse(two.exists())
        self.cli("merge", "--board", "BOARD-001", "--apply")
        self.assertEqual(self.status(), "Merged")
        self.assertFalse(one.exists())

    def test_multi_repo_conflict_records_partial_state_and_preserves_rest(self):
        api = self.add_repo("api")
        self.add_repo("web")
        one = self.create()
        two = self.create(repo="api")
        three = self.create(repo="web")
        (api / "data.txt").write_text("conflicting main\n")
        self.commit(api)
        self.set_status("BOARD-001", "Pending Merge")
        self.cli("merge", "--board", "BOARD-001", "--apply", success=False)
        self.assertFalse(one.exists())
        self.assertTrue(two.exists())
        self.assertTrue(three.exists())
        self.assertEqual(self.status(), "Pending Merge")
        state = WORKTREE.local_state(str(self.root))["workspaces"]
        self.assertEqual(state[str(one)]["outcome"], "merged")
        self.assertIn("error", state[str(two)])
        self.assertEqual(state[str(three)]["outcome"], "active")
        self.assertTrue(self.git(api, "ls-files", "--unmerged").stdout)
        (api / "data.txt").write_text("human resolution\n")
        self.commit(api)
        self.cli("merge", "--board", "BOARD-001", "--apply")
        self.assertFalse(two.exists())
        self.assertFalse(three.exists())
        self.assertEqual(self.status(), "Merged")
        self.assertEqual((api / "data.txt").read_text(), "human resolution\n")

    def test_pending_merge_rejects_unrelated_human_commit(self):
        path = self.create()
        (self.root / "data.txt").write_text("conflicting target\n")
        self.commit(self.root)
        self.set_status("BOARD-001", "Pending Merge")
        self.cli("merge", "--board", "BOARD-001", "--apply", success=False)
        (self.root / "data.txt").write_text("resolution\n")
        self.commit(self.root)
        (self.root / "unrelated.txt").write_text("unrelated\n")
        self.commit(self.root)
        result = self.cli("merge", "--board", "BOARD-001", "--apply", success=False)
        self.assertIn("saved source and target parents", result.stderr)
        self.assertTrue(path.exists())
        self.assertEqual(self.status(), "Pending Merge")

    def test_merge_options_no_commit_cannot_trigger_premature_cleanup(self):
        path = self.create()
        self.git(self.root, "config", "branch.main.mergeOptions", "--no-commit")
        self.set_status("BOARD-001", "Pending Merge")
        source = self.git(path, "rev-parse", "HEAD").stdout.strip()
        self.cli("merge", "--board", "BOARD-001", "--apply")
        self.assertFalse(path.exists())
        self.assertEqual(self.status(), "Merged")
        self.git(self.root, "merge-base", "--is-ancestor", source, "refs/heads/main")
        self.assertEqual(self.git(self.root, "status", "--porcelain", "--", "data.txt").stdout, "")
        self.assertNotEqual(self.git(self.root, "rev-parse", "--quiet", "--verify", "MERGE_HEAD", check=False).returncode, 0)

    def test_success_exit_without_committed_merge_preserves_workspace(self):
        path = self.create()
        self.set_status("BOARD-001", "Pending Merge")
        args = type("Args", (), {"command": "merge", "board": ["BOARD-001"], "repo": None,
                                  "apply": True, "target": None})()
        actual = WORKTREE.git

        def no_commit(cwd, *parts, **kwargs):
            if "merge" in parts:
                return actual(cwd, *[part for part in parts if part != "--commit"], "--no-commit", **kwargs)
            return actual(cwd, *parts, **kwargs)

        with mock.patch.object(WORKTREE, "git", side_effect=no_commit):
            self.assertEqual(WORKTREE.cmd_lifecycle(args, str(self.root)), WORKTREE.REFUSED)
        self.assertTrue(path.exists())
        self.git(self.root, "rev-parse", "--verify", "refs/heads/feat/shared-lifecycle")
        self.assertEqual(self.status(), "Pending Merge")
        self.git(self.root, "commit", "-m", "human completes merge")
        self.cli("merge", "--board", "BOARD-001", "--apply")
        self.assertFalse(path.exists())
        self.assertEqual(self.status(), "Merged")

    def test_mode_from_any_mapped_checkout_leaves_every_settings_file_unchanged(self):
        api = self.add_repo("api")
        control_tree = self.create(change=False)
        app_tree = self.create(repo="api", change=False)
        checkouts = (self.root, control_tree, app_tree)
        originals = {checkout: (checkout / GUARD.CONFIG_REL).read_bytes() for checkout in checkouts}
        for cwd, mode in ((self.root, "optional"), (control_tree, "required"),
                          (app_tree, "optional"), (api, "required")):
            with self.subTest(cwd=cwd, mode=mode):
                self.cli("mode", mode, cwd=cwd)
                self.assertEqual(WORKTREE.local_state(str(self.root))["mode"], mode)
                for checkout in checkouts:
                    self.assertEqual((checkout / GUARD.CONFIG_REL).read_bytes(), originals[checkout])
                self.assertFalse((api / GUARD.CONFIG_REL).exists())
                self.assertEqual(self.hook("Edit", {"file_path": str(self.root / "data.txt")}),
                                 None if mode == "optional" else "ask")
                self.cli("check-policy", cwd=control_tree, guard=True)
                self.cli("check-git", "--", "git commit -m test", cwd=api, guard=True, success=False)

    def test_mode_ignores_malformed_settings_and_refuses_without_repo_map(self):
        path = self.create(change=False)
        original = self.settings_path.read_bytes()
        (path / GUARD.CONFIG_REL).write_text("{malformed")
        self.cli("mode", "optional", cwd=path)
        self.assertEqual(self.settings_path.read_bytes(), original)
        self.assertEqual((path / GUARD.CONFIG_REL).read_text(), "{malformed")
        self.assertEqual(WORKTREE.local_state(str(self.root))["mode"], "optional")
        (self.root / ".claude/repos.json").write_text('{"control": "elsewhere"}\n')
        self.assertIn("control", self.cli("mode", "required", success=False).stderr)
        self.assertEqual(WORKTREE.local_state(str(self.root))["mode"], "optional")
        self.assertEqual(self.settings_path.read_bytes(), original)

    def test_mode_write_error_leaves_settings_and_does_not_persist_mode(self):
        path = self.create(change=False)
        originals = {checkout / GUARD.CONFIG_REL: (checkout / GUARD.CONFIG_REL).read_bytes()
                     for checkout in (self.root, path)}
        original_state = WORKTREE.local_state

        def fail_write(root, value=None):
            if value is not None:
                raise OSError("injected state-write failure")
            return original_state(root)

        args = type("Args", (), {"value": "optional"})()
        with mock.patch.object(WORKTREE, "local_state", side_effect=fail_write):
            with self.assertRaisesRegex(OSError, "injected state-write failure"):
                WORKTREE.cmd_mode(args, str(path))
        for config, content in originals.items():
            self.assertEqual(config.read_bytes(), content)
        self.assertEqual(WORKTREE.local_state(str(self.root))["mode"], "required")

    def test_historical_merged_row_does_not_adopt_reused_slug(self):
        path = self.create()
        self.set_status("BOARD-001", "Pending Merge")
        self.cli("merge", "--board", "BOARD-001", "--apply")
        table, _ = self.board.read_table(self.root / "docs/BOARD.md")
        self.rows = [self.board.cell_texts(table["lines"], index) for index in table["rows"]]
        self.add_row("BOARD-002", "Shared lifecycle", "Chore")
        self.cli("create", "--board", "BOARD-002")
        self.assertTrue(path.exists())
        self.cli("verify", "shared-lifecycle", success=False)
        self.cli("discard", "--board", "BOARD-002", "--apply", "--discard")
        self.assertEqual(self.status(), "Merged")
        self.assertEqual(self.status("BOARD-002"), "Dropped")

    def test_verify_uses_saved_base_unless_explicitly_overridden(self):
        self.git(self.root, "checkout", "-b", "integration")
        (self.root / "integration.txt").write_text("base-only change\n")
        self.commit(self.root)
        self.cli("create", "--board", "BOARD-001", "--base", "integration")
        path = self.root / ".claude/worktrees/shared-lifecycle"
        result = self.cli("verify", "shared-lifecycle", success=False)
        self.assertIn("NOT READY: no commit ahead of integration", result.stdout)
        self.cli("verify", "shared-lifecycle", "--base", "main")
        (path / "data.txt").write_text("feature\n")
        self.commit(path)
        self.assertIn("ahead of integration", self.cli("verify", "shared-lifecycle").stdout)

    def test_all_repos_are_preflighted_before_first_merge(self):
        api = self.add_repo("api")
        one = self.create()
        two = self.create(repo="api")
        self.set_status("BOARD-001", "Pending Merge")
        (api / "untracked.txt").write_text("dirty target")
        self.cli("merge", "--board", "BOARD-001", "--apply", success=False)
        self.assertTrue(one.exists())
        self.assertTrue(two.exists())
        self.assertEqual((self.root / "data.txt").read_text(), "initial\n")

    def test_batch_merge_by_board_id(self):
        self.add_row("BOARD-002", "Second workspace")
        one = self.create(change=False)
        self.cli("create", "--board", "BOARD-002", "--new")
        two = self.root / ".claude/worktrees/second-workspace"
        for index, path in enumerate((one, two)):
            (path / ("file-%s.txt" % index)).write_text("feature")
            self.commit(path)
        for board_id in ("BOARD-001", "BOARD-002"):
            self.set_status(board_id, "Pending Merge")
        self.cli("merge", "--board", "BOARD-001", "--board", "BOARD-002", "--apply")
        self.assertEqual(self.status(), "Merged")
        self.assertEqual(self.status("BOARD-002"), "Merged")
        self.assertFalse(one.exists())
        self.assertFalse(two.exists())

    def test_cleanup_error_is_recorded_and_resumable(self):
        path = self.create()
        self.set_status("BOARD-001", "Pending Merge")
        args = type("Args", (), {"command": "merge", "board": ["BOARD-001"], "repo": None,
                                  "apply": True, "target": None})()
        actual = WORKTREE.git

        def broken(cwd, *parts, **kwargs):
            if parts[:2] == ("branch", "-D"):
                return 128, "", "injected branch failure"
            return actual(cwd, *parts, **kwargs)

        with mock.patch.object(WORKTREE, "git", side_effect=broken):
            self.assertEqual(WORKTREE.cmd_lifecycle(args, str(self.root)), WORKTREE.REFUSED)
        self.assertFalse(path.exists())
        state = WORKTREE.local_state(str(self.root))["workspaces"][str(path)]
        self.assertEqual(state["outcome"], "merged-pending-cleanup")
        self.assertIn("injected branch failure", state["error"])
        self.assertEqual(self.status(), "Pending Merge")
        self.cli("merge", "--board", "BOARD-001", "--apply")
        self.assertEqual(self.status(), "Merged")

    def test_cleanup_preview_and_refusal_do_not_create_recovery_tsv(self):
        path = self.create(change=False)
        cleanup_dir = Path(WORKTREE.common_dir(str(self.root))) / "cleanup-wt"

        self.cli("cleanup", "shared-lifecycle")
        self.assertFalse(list(cleanup_dir.glob("*.tsv")))
        self.assertTrue(path.exists())

        (path / "data.txt").write_text("unmerged\n")
        self.commit(path)
        self.cli("cleanup", "shared-lifecycle", success=False)
        self.assertFalse(list(cleanup_dir.glob("*.tsv")))
        self.assertTrue(path.exists())

    def test_custom_base_is_persisted_and_origin_default_is_protected(self):
        self.git(self.root, "checkout", "-b", "integration")
        self.cli("create", "--board", "BOARD-001", "--base", "integration")
        path = self.root / ".claude/worktrees/shared-lifecycle"
        (path / "data.txt").write_text("feature\n")
        self.commit(path)
        self.set_status("BOARD-001", "Pending Merge")
        self.cli("merge", "--board", "BOARD-001", "--apply")
        self.assertEqual(self.git(self.root, "branch", "--show-current").stdout.strip(), "integration")
        self.assertEqual((self.root / "data.txt").read_text(), "feature\n")
        self.git(self.root, "update-ref", "refs/remotes/origin/integration", "HEAD")
        self.git(self.root, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/integration")
        self.cli("mode", "optional")
        self.cli("check-git", "--", "git commit -m test", guard=True, success=False)

    def test_locked_and_ambiguous_workspaces_are_preserved(self):
        self.add_repo("api")
        one = self.create()
        self.create(repo="api")
        self.cli("cleanup", "shared-lifecycle", success=False)
        self.git(self.root, "worktree", "lock", str(one))
        self.cli("discard", "--board", "BOARD-001", "--repo", "control", "--apply", "--discard", success=False)
        self.assertTrue(one.exists())

    def test_selected_repo_discard_keeps_parent_open_until_all_discarded(self):
        self.add_repo("api")
        one = self.create()
        two = self.create(repo="api")
        self.cli("discard", "--board", "BOARD-001", "--repo", "api", "--apply", "--discard")
        self.assertNotEqual(self.status(), "Dropped")
        self.assertTrue(one.exists())
        self.assertFalse(two.exists())
        self.cli("discard", "--board", "BOARD-001", "--apply", "--discard")
        self.assertEqual(self.status(), "Dropped")

    def test_handoff_lists_all_repo_diffs_and_batch_commands(self):
        renamed = self.root.with_name("control root's workspace")
        self.root.rename(renamed)
        self.root = renamed
        self.script = self.root / ".claude/skills/git-worktree/scripts/worktree.py"
        self.guard = self.root / ".claude/skills/git-worktree/scripts/guard.py"
        self.add_repo("api")
        self.add_row("BOARD-002", "Shared lifecycle fix", kind="Fix", blocked="BOARD-001")
        one = self.create()
        two = self.create(repo="api")
        for repo in ("control", "api"):
            self.cli("create", "--board", "BOARD-002", "--reuse", "BOARD-001", "--repo", repo)
        for board_id in ("BOARD-001", "BOARD-002"):
            self.set_status(board_id, "Pending Merge")
        before = {path.relative_to(self.root): path.read_bytes()
                  for path in self.root.rglob("*") if path.is_file()}
        arguments = ["--board", "BOARD-001", "--board", "BOARD-002",
                     "--repo", "control", "--repo", "api", "--target", "main"]
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", GIT_CONFIG_GLOBAL="/dev/null",
                   GIT_CONFIG_NOSYSTEM="1")
        for script in (self.script, one / ".claude/skills/git-worktree/scripts/worktree.py"):
            with self.subTest(script=script):
                self.script = script
                result = self.cli("handoff", *arguments)
                self.assertNotIn(str(self.root), result.stdout)
                self.assertNotIn("cd ", result.stdout)
                self.assertNotIn("discard", result.stdout)
                lines = result.stdout.splitlines()
                for index, (repo, path) in enumerate(((self.root, one), (self.root / "apps/api", two))):
                    branch = self.git(path, "branch", "--show-current").stdout.strip()
                    diff = ["git", "-C", os.path.relpath(repo, self.root), "diff"]
                    self.assertEqual(lines[index * 3], shlex.join(diff + ["main..." + branch]))
                    self.assertEqual(lines[index * 3 + 1],
                                     shlex.join(diff + ["--stat", "main..." + branch]))
                    self.assertEqual(lines[index * 3 + 2],
                                     "workspace: " + os.path.relpath(path, self.root))
                preview, apply = lines[-2:]
                expected = shlex.join(["python3", os.path.relpath(script, self.root), "merge", *arguments])
                self.assertEqual(preview, expected)
                self.assertEqual(apply, expected + " --apply")
                for command in [line for line in lines if line.startswith("git ")] + [preview]:
                    result = subprocess.run(["sh", "-c", command], cwd=self.root, env=env,
                                            text=True, capture_output=True, timeout=30)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("preview: merge control", result.stdout)
                self.assertIn("preview: merge api", result.stdout)
                self.assertIn("dry run; human CLI only: add --apply", result.stdout)
        self.assertEqual(before, {path.relative_to(self.root): path.read_bytes()
                                  for path in self.root.rglob("*") if path.is_file()})

    def test_confinement_protected_and_symlink_rejection(self):
        path = self.create()
        item = {"repo": str(self.root), "repo_id": "control", "path": str(path), "branch": "main"}
        with self.assertRaisesRegex(ValueError, "protected"):
            WORKTREE.validate_workspace(item, str(self.root))
        item["branch"] = "feat/shared-lifecycle"
        item["path"] = str(self.root)
        with self.assertRaises(ValueError):
            WORKTREE.validate_workspace(item, str(self.root))
        link = self.root / ".claude/worktrees/escape"
        link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            WORKTREE.confined(str(link), str(link.parent))
        with self.assertRaisesRegex(ValueError, "escapes"):
            WORKTREE.confined(str(self.root.parent), str(self.root))

    def test_git_errors_fail_closed_before_removal(self):
        path = self.create()
        args = type("Args", (), {"board": "BOARD-001", "repo": None,
                                  "apply": True, "discard": True})()
        actual = WORKTREE.git

        def broken(cwd, *parts, **kwargs):
            if parts[:2] == ("worktree", "remove"):
                return 128, "", "injected removal failure"
            return actual(cwd, *parts, **kwargs)

        with mock.patch.object(WORKTREE, "git", side_effect=broken):
            self.assertNotEqual(WORKTREE.cmd_discard(args, str(self.root)), 0)
        self.assertTrue(path.exists())
        with mock.patch.object(WORKTREE, "git", return_value=(128, "", "injected list failure")):
            with self.assertRaisesRegex(ValueError, "injected list failure"):
                WORKTREE.list_worktrees(str(self.root))

    def test_discard_clears_board_when_branch_deletion_fails(self):
        path = self.create()
        args = type("Args", (), {"board": "BOARD-001", "repo": None,
                                  "apply": True, "discard": True})()
        actual = WORKTREE.git

        def broken(cwd, *parts, **kwargs):
            if parts[:2] == ("branch", "-D"):
                return 128, "", "injected branch deletion failure"
            return actual(cwd, *parts, **kwargs)

        stderr = io.StringIO()
        with mock.patch.object(WORKTREE, "git", side_effect=broken):
            with mock.patch("sys.stderr", stderr):
                result = WORKTREE.cmd_discard(args, str(self.root))

        self.assertEqual(result, WORKTREE.REFUSED)
        self.assertFalse(path.exists())
        self.assertEqual(self.git(self.root, "rev-parse", "--verify",
                                   "refs/heads/feat/shared-lifecycle", check=False).returncode, 0)
        table, error = self.board.read_table(self.root / "docs/BOARD.md")
        self.assertIsNone(error)
        index = self.board.row_by_id(table, "BOARD-001")
        cells = self.board.cell_texts(table["lines"], index)
        self.assertEqual(cells[3], "Dropped")
        self.assertEqual(cells[8], "-")
        self.assertIn("leftover branch feat/shared-lifecycle remains", stderr.getvalue())

    def partial(self):
        args = WORKTREE.argparse.Namespace(board="BOARD-001", repo="control", base=None,
                                           slug=None, reuse=None, new=False)
        with mock.patch.object(WORKTREE, "initialize_settings", side_effect=ValueError("injected initialization")):
            self.assertEqual(WORKTREE.cmd_create(args, str(self.root)), WORKTREE.REFUSED)
        return self.root / ".claude/worktrees/shared-lifecycle"

    def test_partial_resume_preserves_files_base_and_association_and_blocks_slug_retry(self):
        path = self.partial()
        (path / "data.txt").write_text("keep dirty source")
        (path / ".env.local").write_text("keep ignored")
        (self.root / ".env.local").write_text("do not replace")
        config = path / GUARD.CONFIG_REL
        value = json.loads(config.read_text())
        value["model"] = "manual-selection"
        config.write_text(json.dumps(value))
        manual = config.read_bytes()
        board_before = (self.root / "docs/BOARD.md").read_bytes()
        branches = self.git(self.root, "branch", "--list").stdout
        for flags in (("--slug", "retry"), ("--slug", "retry", "--new")):
            result = self.cli("create", "--board", "BOARD-001", *flags, success=False)
            self.assertIn("resume", result.stderr)
        self.assertEqual((self.root / "docs/BOARD.md").read_bytes(), board_before)
        record = WORKTREE.local_state(str(self.root))["workspaces"][str(path)].copy()
        self.cli("resume", "--board", "BOARD-001")
        self.cli("resume", "--board", "BOARD-001")
        self.assertEqual(self.status(), "In Progress")
        self.assertEqual(self.git(self.root, "branch", "--list").stdout, branches)
        self.assertEqual((path / "data.txt").read_text(), "keep dirty source")
        self.assertEqual((path / ".env.local").read_text(), "keep ignored")
        self.assertEqual(config.read_bytes(), manual)
        record.pop("error")
        self.assertEqual(WORKTREE.local_state(str(self.root))["workspaces"][str(path)], record)

    def test_recovery_provisioning_and_board_errors_remain_retryable(self):
        path = self.partial()
        board_before = (self.root / "docs/BOARD.md").read_bytes()
        for stage in ("provision", "board"):
            args = WORKTREE.argparse.Namespace(board="BOARD-001", repo="control", worktree=None)
            if stage == "provision":
                patcher = mock.patch.object(WORKTREE, "provision_local_files", side_effect=OSError("injected"))
            else:
                board = WORKTREE.load_board_module(str(self.root))
                patcher = mock.patch.object(board, "write_atomic", side_effect=OSError("injected"))
            with patcher, mock.patch.object(WORKTREE, "load_board_module", return_value=board if stage == "board" else self.board):
                self.assertEqual(WORKTREE.cmd_resume(args, str(self.root)), WORKTREE.REFUSED)
            self.assertEqual((self.root / "docs/BOARD.md").read_bytes(), board_before)
            self.assertIn("failed", WORKTREE.local_state(str(self.root))["workspaces"][str(path)]["error"])
        self.cli("resume", "--board", "BOARD-001")
        self.assertNotIn("error", WORKTREE.local_state(str(self.root))["workspaces"][str(path)])

    def test_resume_repairs_exclusion_failure_after_env_copy_without_overwriting(self):
        api = self.add_repo("api")
        fixture = b"FIXTURE_ONLY=value\n"
        (api / ".env.retry").write_bytes(fixture)
        path = api / ".claude/worktrees/shared-lifecycle"
        exclude = Path(WORKTREE.common_dir(str(api))) / "info/exclude"
        before = (self.root / "docs/BOARD.md").read_bytes()
        real_open = open

        def fail_exclusion(file, mode="r", *args, **kwargs):
            if Path(file) == exclude and mode == "a":
                raise PermissionError("injected exclusion failure after copy")
            return real_open(file, mode, *args, **kwargs)

        create = WORKTREE.argparse.Namespace(board="BOARD-001", repo="api", base=None,
                                             slug=None, reuse=None, new=False)
        resume = WORKTREE.argparse.Namespace(board="BOARD-001", repo="api", worktree=None)
        with mock.patch.object(WORKTREE, "open", side_effect=fail_exclusion, create=True):
            self.assertEqual(WORKTREE.cmd_create(create, str(self.root)), WORKTREE.REFUSED)
            self.assertEqual((path / ".env.retry").read_bytes(), fixture)
            self.assertNotEqual(self.git(path, "check-ignore", ".env.retry", check=False).returncode, 0)
            self.assertEqual((self.root / "docs/BOARD.md").read_bytes(), before)
            self.assertIn("provisioning failed", WORKTREE.local_state(str(self.root))["workspaces"][str(path)]["error"])
            self.assertEqual(WORKTREE.cmd_resume(resume, str(self.root)), WORKTREE.REFUSED)
            self.assertEqual((self.root / "docs/BOARD.md").read_bytes(), before)
            self.assertIn("provisioning failed", WORKTREE.local_state(str(self.root))["workspaces"][str(path)]["error"])

        # A retry must not read env values, even when primary and destination differ.
        (api / ".env.retry").write_bytes(b"FIXTURE_ONLY=changed-primary\n")
        (path / ".env.unrelated").write_bytes(b"FIXTURE_ONLY=unrelated\n")
        real_os_open = os.open

        def no_env_open(file, *args, **kwargs):
            if Path(file).name.startswith(".env"):
                raise AssertionError("retry opened an existing env file")
            return real_os_open(file, *args, **kwargs)

        with mock.patch.object(WORKTREE.os, "open", side_effect=no_env_open):
            self.assertEqual(WORKTREE.cmd_resume(resume, str(self.root)), WORKTREE.OK)
            self.assertEqual(WORKTREE.cmd_resume(resume, str(self.root)), WORKTREE.OK)
        self.assertEqual((path / ".env.retry").read_bytes(), fixture)
        self.git(path, "check-ignore", ".env.retry")
        self.assertNotEqual(self.git(path, "check-ignore", ".env.unrelated", check=False).returncode, 0)
        self.assertNotIn("error", WORKTREE.local_state(str(self.root))["workspaces"][str(path)])
        self.assertEqual(self.status(), "In Progress")

    def test_existing_env_exclusion_must_be_effective_before_resume_succeeds(self):
        api = self.add_repo("api")
        # Create a partial before env provisioning, then supply an existing destination.
        create = WORKTREE.argparse.Namespace(board="BOARD-001", repo="api", base=None,
                                             slug=None, reuse=None, new=False)
        with mock.patch.object(WORKTREE, "initialize_settings", side_effect=ValueError("fixture")):
            self.assertEqual(WORKTREE.cmd_create(create, str(self.root)), WORKTREE.REFUSED)
        path = api / ".claude/worktrees/shared-lifecycle"
        (api / ".env.retry").write_text("FIXTURE_ONLY=source\n")
        (path / ".env.retry").write_text("FIXTURE_ONLY=destination\n")
        ignore = path / ".gitignore"
        original = ignore.read_bytes()
        ignore.write_bytes(original + b"!.env.retry\n")
        before = (self.root / "docs/BOARD.md").read_bytes()
        self.cli("resume", "--board", "BOARD-001", "--repo", "api", success=False)
        self.assertEqual((self.root / "docs/BOARD.md").read_bytes(), before)
        self.assertIn("provisioning failed", WORKTREE.local_state(str(self.root))["workspaces"][str(path)]["error"])
        self.assertNotEqual(self.git(path, "check-ignore", ".env.retry", check=False).returncode, 0)
        ignore.write_bytes(original)
        self.cli("resume", "--board", "BOARD-001", "--repo", "api")
        self.git(path, "check-ignore", ".env.retry")
        self.assertEqual((path / ".env.retry").read_text(), "FIXTURE_ONLY=destination\n")
        self.assertNotIn("error", WORKTREE.local_state(str(self.root))["workspaces"][str(path)])

    def test_multiple_partials_require_selection_then_prefer_linked_assignment(self):
        one = self.partial()
        two = self.root / ".claude/worktrees/older-retry"
        self.git(self.root, "worktree", "add", str(two), "-b", "feat/older-retry", "main")
        state = WORKTREE.local_state(str(self.root))
        state["workspaces"][str(two)] = dict(state["workspaces"][str(one)], branch="feat/older-retry")
        WORKTREE.local_state(str(self.root), state)
        before = (self.root / "docs/BOARD.md").read_bytes()
        result = self.cli("resume", "--board", "BOARD-001", success=False)
        for path in (one, two):
            self.assertIn("--worktree " + str(path), result.stderr)
        self.assertEqual((self.root / "docs/BOARD.md").read_bytes(), before)
        self.cli("resume", "--board", "BOARD-001", "--worktree", str(one))
        linked = (self.root / "docs/BOARD.md").read_bytes()
        self.cli("resume", "--board", "BOARD-001")
        self.assertEqual((self.root / "docs/BOARD.md").read_bytes(), linked)
        self.assertIn("error", WORKTREE.local_state(str(self.root))["workspaces"][str(two)])
        self.cli("resume", "--board", "BOARD-001", "--worktree", str(two))
        self.assertTrue(one.exists())
        self.assertTrue(two.exists())
        table, _ = self.board.read_table(self.root / "docs/BOARD.md")
        cell = self.board.cell_texts(table["lines"], self.board.row_by_id(table, "BOARD-001"))[8]
        self.assertNotIn("shared-lifecycle", cell)
        self.assertIn("older-retry", cell)

    def test_new_task_requires_reuse_or_explicit_new_but_never_for_same_task(self):
        self.add_row("BOARD-002", "Other task")
        self.add_row("BOARD-003", "Independent task")
        path = self.create(change=False)
        before = self.git(self.root, "worktree", "list", "--porcelain").stdout
        self.assertIn("--reuse", self.cli("create", "--board", "BOARD-002", success=False).stderr)
        self.assertEqual(self.git(self.root, "worktree", "list", "--porcelain").stdout, before)
        self.cli("create", "--board", "BOARD-002", "--reuse", "BOARD-001")
        self.cli("create", "--board", "BOARD-003", "--new")
        self.cli("create", "--board", "BOARD-001", "--slug", "no-bypass", "--new", success=False)
        self.assertEqual(WORKTREE.local_state(str(self.root))["workspaces"][str(path)]["boards"],
                         ["BOARD-001", "BOARD-002"])

    def test_selection_refuses_other_task_repo_outside_and_unassociated_paths(self):
        self.add_row("BOARD-002", "Other task")
        self.add_repo("api")
        path = self.partial()
        before = (self.root / "docs/BOARD.md").read_bytes()
        state = WORKTREE.local_state(str(self.root))
        for board_id, repo, selection in (("BOARD-002", "control", path),
                                           ("BOARD-001", "api", path),
                                           ("BOARD-001", "unknown", path),
                                           ("BOARD-001", "control", self.root),
                                           ("BOARD-001", "control", self.root / ".claude/worktrees/unknown")):
            with self.subTest(board=board_id, repo=repo, selection=selection):
                self.cli("resume", "--board", board_id, "--repo", repo, "--worktree", str(selection), success=False)
        self.assertEqual((self.root / "docs/BOARD.md").read_bytes(), before)
        self.assertEqual(WORKTREE.local_state(str(self.root)), state)

    def test_selection_refuses_locked_detached_branch_base_and_identity_mismatches(self):
        path = self.partial()
        before = (self.root / "docs/BOARD.md").read_bytes()
        state = WORKTREE.local_state(str(self.root))
        self.git(self.root, "worktree", "lock", str(path))
        self.cli("resume", "--board", "BOARD-001", "--worktree", str(path), success=False)
        self.git(self.root, "worktree", "unlock", str(path))
        self.git(path, "checkout", "--detach")
        self.cli("resume", "--board", "BOARD-001", success=False)
        self.git(path, "checkout", "feat/shared-lifecycle")
        for field, value in (("branch", "feat/wrong"), ("base", "gone-base"),
                             ("control", str(self.root.parent)), ("repo", str(self.root.parent)),
                             ("repo_id", "wrong"), ("boards", ["BOARD-002"])):
            with self.subTest(field=field):
                changed = json.loads(json.dumps(state))
                changed["workspaces"][str(path)][field] = value
                WORKTREE.local_state(str(self.root), changed)
                self.cli("resume", "--board", "BOARD-001", "--worktree", str(path), success=False)
        WORKTREE.local_state(str(self.root), state)
        self.assertEqual((self.root / "docs/BOARD.md").read_bytes(), before)

    def test_wrong_common_dir_and_prunable_selection_refuse_without_mutation(self):
        path = self.partial()
        args = WORKTREE.argparse.Namespace(board="BOARD-001", repo="control", worktree=str(path))
        board_before = (self.root / "docs/BOARD.md").read_bytes()
        actual = WORKTREE.common_dir
        with mock.patch.object(WORKTREE, "common_dir", side_effect=lambda p: "/wrong" if p == str(path) else actual(p)):
            with self.assertRaisesRegex(ValueError, "common-dir mismatch"):
                WORKTREE.cmd_resume(args, str(self.root))
        missing = path.with_name("retained-fixture")
        path.rename(missing)
        self.cli("resume", "--board", "BOARD-001", "--worktree", str(path), success=False)
        self.assertTrue(missing.exists())
        self.assertEqual((self.root / "docs/BOARD.md").read_bytes(), board_before)

    def test_missing_registration_with_leftovers_refuses_new_and_preserves_directory(self):
        path = self.partial()
        # Only disposable fixture registration is removed; source directory is retained.
        entries = WORKTREE.list_worktrees(str(self.root))
        with mock.patch.object(WORKTREE, "list_worktrees", return_value=entries[:1]):
            with self.assertRaisesRegex(ValueError, "leftover directory or branch"):
                WORKTREE.task_workspaces(str(self.root), str(self.root), "control", "BOARD-001", "-")
        self.assertTrue(path.exists())

    def test_source_settings_match_policy_and_apply_requires_approval(self):
        policy = json.loads((SOURCE / ".claude/policies/git-policy.json").read_text())
        config = json.loads((SOURCE / GUARD.CONFIG_REL).read_text())
        self.assertTrue(GUARD.settings_match(config, policy))
        self.assertEqual(GUARD.bash_verdict(policy, "python3 worktree.py merge --board BOARD-001 --apply")[0], "ask")
        self.assertEqual(GUARD.bash_verdict(policy, "python3 worktree.py discard --board BOARD-001 --apply --discard")[0], "deny")
        self.assertEqual(GUARD.bash_verdict(policy, "git status")[0], "allow")

    def test_review_artifact_permissions_preserve_protections_in_all_modes(self):
        policy = json.loads((SOURCE / ".claude/policies/git-policy.json").read_text())
        for mode in ("required", "optional", "adaptive"):
            with self.subTest(mode=mode):
                mapping = GUARD.ordered_rules(policy, mode)["edit"]
                patterns = list(mapping)
                for pattern in ("artifacts/reviews/**", "**/artifacts/reviews/**"):
                    self.assertGreater(patterns.index(pattern), patterns.index("**/.claude/worktrees/**"))
                    self.assertLess(patterns.index(pattern), patterns.index("docs/BOARD.md"))
                    self.assertLess(patterns.index(pattern), patterns.index("**/.env"))
                cases = {}
                # Edit globs match path strings, not Git roots. Model both absolute
                # contexts explicitly rather than depending on the host's TMPDIR.
                linked_prefix = "/workspace/control/.claude/worktrees/assigned/"
                for prefix in ("", "/workspace/control/", linked_prefix):
                    for name in ("BOARD-113-qa.md", "BOARD-113-review.md", "BOARD-113-ledger.md"):
                        cases[prefix + "artifacts/reviews/" + name] = "allow"
                    for name in (".env", ".env.local", ".npmrc", "private.pem", "private.key",
                                 "private.p12", "id_rsa", ".git/config", ".git-credentials"):
                        cases[prefix + "artifacts/reviews/" + name] = "deny"
                    cases[prefix + "artifacts/reviews/docs/BOARD.md"] = "deny"
                    cases[prefix + "docs/BOARD.md"] = "deny"
                    for name in ("apps/web/src/main.ts", "artifacts/other/report.md"):
                        cases[prefix + name] = "allow" if mode == "optional" or prefix == linked_prefix else "ask"
                    cases[prefix + ".claude/worktrees/assigned/apps/web/src/main.ts"] = "allow"
                for path, action in cases.items():
                    with self.subTest(path=path):
                        actual = None
                        for pattern, verdict in mapping.items():
                            if GUARD.pattern_matches(path, pattern):
                                actual = verdict
                        self.assertEqual(actual, action)
                        self.assertEqual(GUARD.path_verdict(mapping, {path})[0], action)
                # The settings file is mode-independent: the hook applies the mode at runtime.
                settings, error = GUARD.write_settings(str(self.settings_path), policy)
                self.assertIsNotNone(settings, error)
                self.assertTrue(GUARD.settings_match(json.loads(self.settings_path.read_text()), policy))
                with mock.patch.object(GUARD, "load_worktree_module") as loader:
                    loader.return_value.workspace_mode.return_value = mode
                    self.assertEqual(GUARD.cmd_check_policy(False, str(self.root),
                                                          GUARD.repo_context(str(self.root))), 0)

    def test_generated_settings_keep_env_example_out_of_static_denies(self):
        policy = json.loads((SOURCE / ".claude/policies/git-policy.json").read_text())
        settings = GUARD.generated_settings(policy)
        deny = settings["permissions"]["deny"]
        # A static .env.* deny would beat the .env.example exception, so only the hook enforces it.
        self.assertFalse([rule for rule in deny if ".env." in rule], deny)
        for rule in deny:
            pattern = rule[rule.index("(") + 1:-1]
            for exception in policy["hidden_paths"]["allow"]:
                self.assertFalse(GUARD.pattern_matches(exception, pattern), (rule, exception))
        # No static deny may shadow a later, narrower ask or allow of the same kind.
        ordered = {"Bash": [(rule["pattern"], rule["action"]) for rule in policy["bash"]],
                   "Edit": [(rule["pattern"], rule["action"]) for rule in policy["edit"]],
                   "Read": [(path, "deny") for path in policy["hidden_paths"]["paths"]] +
                           [(path, "allow") for path in policy["hidden_paths"]["allow"]]}
        for rule in deny:
            tool, pattern = rule[:rule.index("(")], rule[rule.index("(") + 1:-1]
            rules = ordered[tool]
            index = rules.index((pattern, "deny"))
            for later, action in rules[index + 1:]:
                if action != "deny":
                    self.assertFalse(GUARD.pattern_matches(later, pattern), (rule, later))
        self.assertIn("Edit(docs/BOARD.md)", deny)
        self.assertNotIn("Edit(**/docs/BOARD.md)", deny)
        self.assertFalse(any(GUARD.pattern_matches("templates/project/docs/BOARD.md", rule[5:-1])
                             for rule in deny if rule.startswith("Edit(")))
        self.assertIn("Bash(git push*)", deny)
        self.assertIn("Edit(.env)", deny)
        self.assertIn("Read(.env)", deny)
        self.assertNotIn("Edit(*)", settings["permissions"]["allow"])
        self.assertEqual(settings["hooks"]["PreToolUse"],
                         [{"matcher": GUARD.GUARDED_TOOLS,
                           "hooks": [{"type": "command", "command": GUARD.HOOK_COMMAND}]}])
        merged = GUARD.merged_settings({"model": "fixture-model", "permissions": {"ask": ["Bash(make *)"]},
                                        "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": []}]}}, policy)
        self.assertTrue(GUARD.settings_match(merged, policy))
        self.assertEqual(merged["model"], "fixture-model")
        self.assertEqual(merged["permissions"]["ask"], ["Bash(make *)"])
        self.assertEqual(merged["hooks"]["PreToolUse"][1], {"matcher": "Bash", "hooks": []})

    def test_hook_denies_push_including_inside_chains(self):
        self.assertEqual(self.hook("Bash", {"command": "git push"}), "deny")
        self.assertEqual(self.hook("Bash", {"command": "git push origin main"}), "deny")
        self.assertEqual(self.hook("Bash", {"command": "ls && git push"}), "deny")
        self.assertEqual(self.hook("Bash", {"command": "ls; git -C . push"}), "deny")

    def test_hook_denies_primary_commit_in_required_mode_and_defers_reads(self):
        self.git(self.root, "switch", "-c", "feat/current")
        self.assertEqual(self.hook("Bash", {"command": "git commit -m test"}), "deny")
        self.assertIsNone(self.hook("Bash", {"command": "git status"}))
        self.assertIsNone(self.hook("Bash", {"command": "git log --oneline"}))
        self.assertEqual(self.hook("Bash", {"command": "git remote -v"}), "ask")
        path = self.create(change=False)
        self.assertIsNone(self.hook("Bash", {"command": "git commit -m test"}, cwd=path))
        self.assertEqual(self.hook("Bash", {"command": "git checkout main"}, cwd=path), "deny")

    def test_hook_denies_primary_deletion_and_allows_worktree_deletion(self):
        path = self.create(change=False)
        (path / "scratch").mkdir()

        def decision(command, cwd):
            # The fixture lives under a temp root, where deletion is allowed by design, so the
            # hook runs in-process with temp roots pointed away from the fixture.
            event = io.StringIO(json.dumps({"tool_name": "Bash", "tool_input": {"command": command},
                                            "cwd": str(cwd)}))
            stdout = io.StringIO()
            with mock.patch.object(GUARD, "TEMP_ROOTS", []), \
                    mock.patch.dict(os.environ, {"TMPDIR": "/nonexistent-fixture-temp"}), \
                    mock.patch("sys.stdout", stdout):
                self.assertEqual(GUARD.cmd_hook(event), GUARD.OK)
            output = stdout.getvalue().strip()
            return json.loads(output)["hookSpecificOutput"] if output else None

        denied = decision("rm -rf docs", self.root)
        self.assertEqual(denied["permissionDecision"], "deny")
        self.assertIn("main checkout", denied["permissionDecisionReason"])
        self.assertEqual(decision("ls && rm -r docs", self.root)["permissionDecision"], "deny")
        self.assertTrue((self.root / "docs/BOARD.md").exists())
        self.assertIsNone(decision("rm -r scratch", path))
        self.assertEqual(decision("rm -rf scratch", path)["permissionDecision"], "ask")

    def test_hook_edit_verdict_follows_saved_mode(self):
        primary_file = {"file_path": str(self.root / "data.txt")}
        linked_file = {"file_path": str(self.root / ".claude/worktrees/x/data.txt")}
        self.assertEqual(self.hook("Edit", primary_file), "ask")
        self.assertEqual(self.hook("Write", {"file_path": "data.txt"}), "ask")
        self.assertIsNone(self.hook("Edit", linked_file))
        self.cli("mode", "optional")
        self.assertIsNone(self.hook("Edit", primary_file))
        self.assertIsNone(self.hook("Edit", linked_file))
        self.assertEqual(self.hook("Edit", {"file_path": str(self.root / "docs/BOARD.md")}), "deny")
        # Nested boards are denied by the hook even though only the root board is a static deny.
        self.assertEqual(self.hook("Edit", {"file_path": str(self.root / "project/docs/BOARD.md")}), "deny")
        self.assertEqual(self.hook("Edit", {"file_path": str(self.root / "templates/project/docs/BOARD.md")}), "ask")
        self.cli("mode", "adaptive")
        self.assertEqual(self.hook("Edit", primary_file), "ask")
        self.assertIsNone(self.hook("Edit", linked_file))

    def test_hook_env_files_are_denied_except_the_example(self):
        for mode in ("required", "optional"):
            with self.subTest(mode=mode):
                self.cli("mode", mode)
                self.assertEqual(self.hook("Write", {"file_path": str(self.root / ".env.local")}), "deny")
                self.assertEqual(self.hook("Edit", {"file_path": str(self.root / "nested/.env")}), "deny")
                self.assertIsNone(self.hook("Write", {"file_path": str(self.root / ".claude/worktrees/x/.env.example")}))
                self.assertEqual(self.hook("Read", {"file_path": str(self.root / ".env.production")}), "deny")
                self.assertEqual(self.hook("Grep", {"pattern": "TOKEN", "path": ".env"}), "deny")
                self.assertIsNone(self.hook("Read", {"file_path": str(self.root / ".env.example")}))
                self.assertIsNone(self.hook("Read", {"file_path": str(self.root / "data.txt")}))
        self.assertIsNone(self.hook("Write", {"file_path": str(self.root / ".env.example")}))

    def test_hook_fails_closed_on_malformed_input_and_missing_policy(self):
        for raw in ("", "not json", "[]", '{"tool_name": "Bash", "tool_input": "git push"}'):
            with self.subTest(raw=raw):
                self.assertEqual(self.hook(None, None, raw=raw), "deny")
        outside = Path(self.temporary.name) / "outside"
        outside.mkdir()
        self.initialize(outside)
        guard_copy = outside / "guard-only/.claude/skills/git-worktree/scripts"
        guard_copy.mkdir(parents=True)
        shutil.copyfile(self.guard, guard_copy / "guard.py")
        event = json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}, "cwd": str(outside)})
        result = subprocess.run([sys.executable, str(guard_copy / "guard.py"), "hook"], cwd=outside,
                                input=event, text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn("not found", output["permissionDecisionReason"])

    def test_settings_hook_command_resolves_guard_from_a_linked_worktree(self):
        self.git(self.root, "rm", "-r", "--cached", "--quiet", ".claude/skills")
        with (self.root / ".gitignore").open("a") as ignore_file:
            ignore_file.write(".claude/skills/\n")
        self.commit(self.root)
        path = self.create(change=False)
        self.assertFalse((path / ".claude/skills").exists())
        command = json.loads((path / GUARD.CONFIG_REL).read_text())["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        for tool_input, decision in (({"command": "git push"}, "deny"), ({"command": "git status"}, None)):
            with self.subTest(command=tool_input["command"]):
                event = json.dumps({"tool_name": "Bash", "tool_input": tool_input, "cwd": str(path)})
                result = subprocess.run(["sh", "-c", command], cwd=path, input=event, text=True,
                                        capture_output=True, timeout=30,
                                        env=dict(os.environ, CLAUDE_PROJECT_DIR=str(path)))
                self.assertEqual(result.returncode, 0, result.stderr)
                output = result.stdout.strip()
                actual = json.loads(output)["hookSpecificOutput"]["permissionDecision"] if output else None
                self.assertEqual(actual, decision)

if __name__ == "__main__":
    unittest.main()
