import importlib.util
import json
import os
from pathlib import Path
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
GUARD = module("lifecycle_test_guard", SCRIPTS / "guard.py")


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="lifecycle-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "control"
        self.root.mkdir()
        for relative in (".kilo/skills/git-worktree/scripts/worktree.py",
                         ".kilo/skills/git-worktree/scripts/guard.py",
                         ".kilo/skills/git-worktree/scripts/scope.py",
                         ".kilo/skills/board/scripts/board.py",
                         ".kilo/policies/git-policy.json", "kilo.jsonc"):
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / relative, destination)
        (self.root / "docs").mkdir()
        (self.root / ".kilo/repos.json").write_text('{"control": "."}\n')
        (self.root / ".gitignore").write_text(".kilo/worktrees/\n__pycache__/\napps/\n")
        self.board = module("test_board", self.root / ".kilo/skills/board/scripts/board.py")
        self.rows = []
        self.add_row("BOARD-001", "Shared lifecycle")
        self.initialize(self.root)
        self.script = self.root / ".kilo/skills/git-worktree/scripts/worktree.py"
        self.guard = self.root / ".kilo/skills/git-worktree/scripts/guard.py"

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
        env.pop("KILO_CONFIG", None)
        result = subprocess.run([sys.executable, str(self.guard if guard else self.script), *args],
                                cwd=cwd or self.root, text=True, capture_output=True, env=env, timeout=30)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def create(self, board_id="BOARD-001", repo="control", change=True):
        self.cli("create", "--board", board_id, "--repo", repo)
        root = self.root if repo == "control" else self.root / "apps" / repo
        path = root / ".kilo/worktrees/shared-lifecycle"
        if change:
            (path / "data.txt").write_text("feature\n")
            self.commit(path)
        return path

    def add_repo(self, name):
        path = self.root / "apps" / name
        path.mkdir(parents=True)
        (path / ".gitignore").write_text(".kilo/worktrees/\n")
        self.initialize(path)
        mapping = json.loads((self.root / ".kilo/repos.json").read_text())
        mapping[name] = "apps/" + name
        (self.root / ".kilo/repos.json").write_text(json.dumps(mapping))
        self.commit(self.root)
        return path

    def test_mode_is_local_persistent_and_regenerates_permissions(self):
        self.assertIn("required", self.cli("mode", "status").stdout)
        self.git(self.root, "checkout", "-b", "feat/current")
        self.cli("check-git", "--", "git commit -m test", guard=True, success=False)
        self.assertIn("Restart Kilo", self.cli("mode", "optional").stdout)
        self.cli("check-git", "--", "git commit -m test", guard=True)
        config = json.loads((self.root / "kilo.jsonc").read_text())
        self.assertEqual(config["permission"]["edit"]["*"], "allow")
        self.assertEqual(config["permission"]["edit"][".env"], "deny")
        self.assertEqual(config["permission"]["edit"]["docs/BOARD.md"], "deny")
        self.assertEqual(config["permission"]["edit"]["AGENTS.md"], "ask")
        self.cli("check-policy", guard=True)
        self.git(self.root, "checkout", "main")
        self.cli("check-git", "--", "git commit -m test", guard=True, success=False)
        self.cli("mode", "required")
        self.assertEqual(json.loads((self.root / "kilo.jsonc").read_text())["permission"]["edit"]["*"], "deny")
        other = Path(self.temporary.name) / "other"
        other.mkdir()
        self.initialize(other)
        self.assertEqual(WORKTREE.local_state(str(other))["mode"], "required")

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
        self.cli("check-git", "--", "git commit -m test", cwd=self.temporary.name,
                 guard=True, success=False)

    def test_fix_reuses_parent_and_discard_updates_all_shared_rows(self):
        self.add_row("BOARD-002", "Fix shared lifecycle", "Fix", "BOARD-001")
        path = self.create()
        self.cli("create", "--board", "BOARD-002")
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

    def test_mode_updates_control_linked_and_mapped_inherited_maps(self):
        api = self.add_repo("api")
        control_tree = self.create(change=False)
        app_tree = self.create(repo="api", change=False)
        shutil.copyfile(self.root / "kilo.jsonc", api / "kilo.jsonc")
        shutil.copyfile(self.root / "kilo.jsonc", app_tree / "kilo.jsonc")
        for cwd, mode in ((self.root, "optional"), (control_tree, "required"),
                          (app_tree, "optional"), (api, "required")):
            with self.subTest(cwd=cwd, mode=mode):
                self.cli("mode", mode, cwd=cwd)
                self.assertEqual(WORKTREE.local_state(str(self.root))["mode"], mode)
                for checkout in (self.root, control_tree, api, app_tree):
                    permissions = json.loads((checkout / "kilo.jsonc").read_text())["permission"]["edit"]
                    self.assertEqual(permissions["*"], "allow" if mode == "optional" else "deny")
                    self.assertEqual(permissions[".env"], "deny")
                    self.assertEqual(permissions["AGENTS.md"], "ask")
                self.cli("check-policy", cwd=control_tree, guard=True)
                self.cli("check-git", "--", "git commit -m test", cwd=api, guard=True, success=False)

    def test_mode_preflight_malformed_maps_has_no_partial_changes(self):
        path = self.create(change=False)
        original = (self.root / "kilo.jsonc").read_bytes()
        (path / "kilo.jsonc").write_text("{malformed")
        self.cli("mode", "optional", cwd=path, success=False)
        self.assertEqual((self.root / "kilo.jsonc").read_bytes(), original)
        self.assertEqual((path / "kilo.jsonc").read_text(), "{malformed")
        self.assertEqual(WORKTREE.local_state(str(self.root))["mode"], "required")
        (path / "kilo.jsonc").unlink()
        self.cli("mode", "optional", success=False)
        self.assertEqual((self.root / "kilo.jsonc").read_bytes(), original)

    def test_mode_write_error_restores_maps_and_does_not_persist_mode(self):
        path = self.create(change=False)
        originals = {checkout / "kilo.jsonc": (checkout / "kilo.jsonc").read_bytes()
                     for checkout in (self.root, path)}
        original_state = WORKTREE.local_state

        def fail_write(root, value=None):
            if value is not None:
                raise OSError("injected state-write failure")
            return original_state(root)

        args = type("Args", (), {"value": "optional"})()
        with mock.patch.object(WORKTREE, "local_state", side_effect=fail_write), mock.patch.dict(os.environ, {"KILO_CONFIG": ""}):
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
        path = self.root / ".kilo/worktrees/shared-lifecycle"
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
        self.cli("create", "--board", "BOARD-002")
        two = self.root / ".kilo/worktrees/second-workspace"
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

    def test_custom_base_is_persisted_and_origin_default_is_protected(self):
        self.git(self.root, "checkout", "-b", "integration")
        self.cli("create", "--board", "BOARD-001", "--base", "integration")
        path = self.root / ".kilo/worktrees/shared-lifecycle"
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
        self.add_repo("api")
        one = self.create()
        two = self.create(repo="api")
        result = self.cli("handoff", "--board", "BOARD-001")
        self.assertIn(str(one), result.stdout)
        self.assertIn(str(two), result.stdout)
        self.assertIn("--stat", result.stdout)
        self.assertIn("merge --board BOARD-001 --apply", result.stdout)
        self.assertIn("discard --board BOARD-001 --apply --discard", result.stdout)

    def test_confinement_protected_and_symlink_rejection(self):
        path = self.create()
        item = {"repo": str(self.root), "repo_id": "control", "path": str(path), "branch": "main"}
        with self.assertRaisesRegex(ValueError, "protected"):
            WORKTREE.validate_workspace(item, str(self.root))
        item["branch"] = "feat/shared-lifecycle"
        item["path"] = str(self.root)
        with self.assertRaises(ValueError):
            WORKTREE.validate_workspace(item, str(self.root))
        link = self.root / ".kilo/worktrees/escape"
        link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            WORKTREE.confined(str(link), str(link.parent))
        with self.assertRaisesRegex(ValueError, "escapes"):
            WORKTREE.confined(str(self.root.parent), str(self.root))

    def test_git_errors_fail_closed_before_removal(self):
        path = self.create()
        args = type("Args", (), {"command": "discard", "board": ["BOARD-001"], "repo": None,
                                  "apply": True, "discard": True, "target": None})()
        actual = WORKTREE.git

        def broken(cwd, *parts, **kwargs):
            if parts and parts[0] == "status":
                return 128, "", "injected status failure"
            return actual(cwd, *parts, **kwargs)

        with mock.patch.object(WORKTREE, "git", side_effect=broken):
            with self.assertRaisesRegex(ValueError, "injected status failure"):
                WORKTREE.cmd_lifecycle(args, str(self.root))
        self.assertTrue(path.exists())
        with mock.patch.object(WORKTREE, "git", return_value=(128, "", "injected list failure")):
            with self.assertRaisesRegex(ValueError, "injected list failure"):
                WORKTREE.list_worktrees(str(self.root))

    def test_generated_map_matches_policy_and_apply_requires_approval(self):
        policy = json.loads((SOURCE / ".kilo/policies/git-policy.json").read_text())
        config = json.loads((SOURCE / "kilo.jsonc").read_text())
        self.assertEqual(config["permission"], GUARD.generated_permission(policy))
        self.assertEqual(GUARD.bash_verdict(policy, "python3 worktree.py merge --board BOARD-001 --apply")[0], "ask")
        self.assertEqual(GUARD.bash_verdict(policy, "git status")[0], "allow")


if __name__ == "__main__":
    unittest.main()
