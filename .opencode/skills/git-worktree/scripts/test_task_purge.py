"""Task-purge regressions run only in disposable repositories inside this worktree."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import task_purge as purge
import test_env
import worktree as wt


ROOT = Path(__file__).resolve().parents[4]


class TaskPurgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="purge-", dir=ROOT / ".tmp")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(test_env.make_repo(self.temp.name))
        self.board = wt.load_board_module(str(ROOT))
        self.board.initialize_board(str(self.repo))
        self.database = self.board.database_path(str(self.repo))
        self.board.migrate_normalized(self.database, apply=True)
        self.task = "BOARD-910"
        self.manifest = self.repo / ".factory-state" / "purges" / self.task / "manifest.json"

    def call(self, apply=False, backup=False, orphan=None, cwd=None, confirm=True):
        args = SimpleNamespace(board=self.task, apply=apply, backup=backup, orphan=orphan or [])
        output, error = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            with patch.object(purge, "confirm", return_value=None) if confirm else contextlib.nullcontext():
                code = purge.command(args, str(cwd or self.repo), wt)
        self.last_error = error.getvalue()
        return code, output.getvalue()

    def exists(self):
        with self.board.readonly_connection(self.database) as connection:
            return connection.execute("SELECT 1 FROM planned_items WHERE id=?", (self.task,)).fetchone() is not None

    def worktree(self):
        path = self.repo / wt.WORKTREES_DIR / "purge-selected"
        branch = "feat/purge-selected"
        self.assertEqual(test_env.git(str(self.repo), "worktree", "add", "-b", branch, str(path))[0], 0)
        with self.board.connect(self.database) as connection:
            connection.execute("UPDATE active_work SET branch_worktree=? WHERE plan_item_id=?",
                               (str(path) + " · branch " + branch, self.task))
            self.board.persist_normalized_projection(connection)
        return path, branch

    def reports(self):
        selected = self.repo / "artifacts/factory/qa/2026-11-12" / self.task
        selected.mkdir(parents=True)
        (selected / "qa.md").write_text("selected evidence")
        ledger = self.repo / ".factory-state/reviews" / (self.task + "-ledger.md")
        ledger.parent.mkdir(parents=True)
        ledger.write_text("selected ledger")
        unrelated = selected.with_name("BOARD-909")
        unrelated.mkdir()
        (unrelated / "qa.md").write_text("unrelated evidence")
        return selected, ledger, unrelated

    def test_preview_is_read_only(self):
        path, _ = self.worktree()
        self.reports()
        def snapshot():
            return {str(file.relative_to(self.repo)): file.read_bytes() for file in self.repo.rglob("*")
                    if ".git" not in file.relative_to(self.repo).parts and file.is_file()}
        before = snapshot()
        self.assertEqual(self.call()[0], wt.OK, self.last_error)
        self.assertEqual(snapshot(), before)
        self.assertFalse(self.manifest.exists())
        self.assertTrue(path.exists())

    def test_missing_database_is_not_initialized(self):
        Path(self.database).unlink()
        before = sorted(str(path.relative_to(self.repo)) for path in self.repo.rglob("*"))
        self.assertEqual(self.call()[0], wt.REFUSED)
        self.assertEqual(sorted(str(path.relative_to(self.repo)) for path in self.repo.rglob("*")), before)
        self.assertFalse(Path(self.database).exists())

    def test_purge_removes_selected_resources_and_preserves_other_content(self):
        path, branch = self.worktree()
        (path / "dirty.txt").write_text("uncommitted work")
        selected, ledger, unrelated = self.reports()
        history = test_env.git(str(self.repo), "rev-parse", "HEAD")[1]
        legacy = (self.repo / "docs/BOARD.md").read_bytes()
        with self.board.connect(self.database) as connection:
            connection.execute("INSERT INTO acceptance_criteria VALUES (?, 0, 'criterion', 0, NULL)", (self.task,))
        self.assertEqual(self.call(apply=True)[0], wt.OK, self.last_error)
        self.assertFalse(path.exists())
        self.assertNotEqual(test_env.git(str(self.repo), "show-ref", "--verify", "refs/heads/" + branch)[0], 0)
        self.assertFalse(selected.exists())
        self.assertFalse(ledger.exists())
        self.assertTrue(unrelated.exists())
        self.assertFalse(self.exists())
        self.assertEqual(test_env.git(str(self.repo), "rev-parse", "HEAD")[1], history)
        self.assertEqual((self.repo / "docs/BOARD.md").read_bytes(), legacy)
        with self.board.readonly_connection(self.database) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM planned_items").fetchone()[0], 10)
            self.assertEqual(connection.execute("SELECT count(*) FROM acceptance_criteria WHERE plan_item_id=?",
                                                (self.task,)).fetchone()[0], 0)
            self.assertNotIn(self.task, connection.execute("SELECT markdown FROM board").fetchone()[0])
        self.assertTrue(json.loads(self.manifest.read_text())["complete"])

    def test_optional_backup_is_private_and_historical_backup_is_preserved(self):
        path, _ = self.worktree()
        (path / "draft.txt").write_text("recoverable content")
        recovery = self.repo / ".factory-state/cleanup-wt/control"
        recovery.mkdir(parents=True)
        old = recovery / "historical.tsv"
        old.write_text("shared historical backup")
        self.assertEqual(self.call(apply=True, backup=True)[0], wt.OK, self.last_error)
        backup = self.manifest.parent / "content"
        self.assertEqual((backup / "0/draft.txt").read_text(), "recoverable content")
        self.assertEqual((backup.stat().st_mode & 0o777), 0o700)
        self.assertEqual(((backup / "0/draft.txt").stat().st_mode & 0o777), 0o600)
        self.assertTrue(old.exists())

    def test_cancel_retains_identity_until_explicit_orphan_purge(self):
        path, branch = self.worktree()
        self.board.transition_plan_item(self.database, self.task, "cancel")
        self.assertTrue(self.exists())
        self.assertTrue(path.exists())
        self.assertEqual(self.call()[0], wt.REFUSED)
        self.assertIn("explicit --orphan", self.last_error)
        evidence = [["control", str(path), branch]]
        self.assertEqual(self.call(apply=True, orphan=evidence)[0], wt.OK, self.last_error)
        self.assertFalse(path.exists())
        self.assertFalse(self.exists())

    def test_dependent_task_refuses_before_writes(self):
        with self.board.connect(self.database) as connection:
            connection.execute("UPDATE planned_items SET blocked_by=? WHERE id='BOARD-909'", (self.task,))
        self.assertEqual(self.call(apply=True)[0], wt.REFUSED)
        self.assertIn("dependent tasks", self.last_error)
        self.assertFalse(self.manifest.exists())
        self.assertTrue(self.exists())

    def test_path_and_branch_claimed_by_other_task_refuses(self):
        path, branch = self.worktree()
        with self.board.connect(self.database) as connection:
            connection.execute("UPDATE active_work SET branch_worktree=? WHERE plan_item_id='BOARD-909'",
                               (str(path) + " · branch " + branch,))
        self.assertEqual(self.call()[0], wt.REFUSED)
        self.assertIn("another task claims", self.last_error)

    def test_symlink_report_refuses(self):
        selected, _, unrelated = self.reports()
        (selected / "link").symlink_to(unrelated, target_is_directory=True)
        self.assertEqual(self.call()[0], wt.REFUSED)
        self.assertTrue(self.exists())

    def test_traversal_and_foreign_paths_refuse(self):
        for path in (self.repo / "../foreign", self.repo.parent):
            with self.subTest(path=path), self.assertRaises(ValueError):
                purge.safe_path(path, self.repo)

    def test_apply_requires_primary_checkout_and_terminal(self):
        path, _ = self.worktree()
        self.assertEqual(self.call(apply=True, cwd=path)[0], wt.REFUSED)
        self.assertIn("primary control checkout", self.last_error)
        self.assertEqual(self.call(apply=True, confirm=False)[0], wt.REFUSED)
        self.assertIn("interactive terminal", self.last_error)
        self.assertTrue(path.exists())

    def test_exact_named_confirmation_no_bypass(self):
        class Terminal(io.StringIO):
            def isatty(self):
                return True
        for text in ("yes\n", "BOARD-909\n", "BOARD-910", " BOARD-910\n"):
            with self.subTest(text=text), patch("sys.stdin", Terminal(text)), patch("sys.stderr", Terminal()):
                with self.assertRaises(ValueError):
                    purge.confirm(self.task)
        with patch("sys.stdin", Terminal(self.task + "\n")), patch("sys.stderr", Terminal()):
            purge.confirm(self.task)

    def test_changed_target_during_confirmation_refuses(self):
        selected, _, _ = self.reports()
        with patch.object(purge, "confirm", side_effect=lambda _: (selected / "qa.md").write_text("changed")):
            self.assertEqual(self.call(apply=True, confirm=False)[0], wt.REFUSED)
        self.assertIn("targets changed", self.last_error)
        self.assertTrue(self.exists())

    def test_failure_retains_task_and_resume_finishes(self):
        path, branch = self.worktree()
        real = purge.checked_git
        def fail_branch(wt_module, repo, *args):
            if args[0] == "update-ref":
                raise ValueError("injected branch-delete failure")
            return real(wt_module, repo, *args)
        with patch.object(purge, "checked_git", side_effect=fail_branch):
            self.assertEqual(self.call(apply=True)[0], wt.REFUSED)
        self.assertTrue(self.exists())
        self.assertFalse(path.exists())
        self.assertEqual(json.loads(self.manifest.read_text())["targets"][1]["phase"], "running")
        self.assertEqual(self.call(apply=True)[0], wt.OK, self.last_error)
        self.assertFalse(self.exists())
        self.assertNotEqual(test_env.git(str(self.repo), "show-ref", "--verify", "refs/heads/" + branch)[0], 0)

    def test_high_water_survives_purge(self):
        self.assertEqual(self.call(apply=True)[0], wt.OK, self.last_error)
        item = {"key": "next", "task": "Next approved task", "type": "Feature", "priority": "P2",
                "risk": "low", "user_story": "As a human I need the next task", "acceptance_criteria": ["A checked outcome", "No ID reuse"],
                "repos": ["control"]}
        accepted = self.board.accept_plan_batch(self.database, [item])
        self.assertEqual(accepted[0]["id"], "BOARD-911")

    def test_commit_completed_before_manifest_acknowledgment_can_resume(self):
        selected, _, _ = self.reports()
        real = purge.save_manifest
        def fail_ack(wt_module, path, record):
            if record.get("complete"):
                raise OSError("injected final acknowledgment failure")
            return real(wt_module, path, record)
        with patch.object(purge, "save_manifest", side_effect=fail_ack):
            self.assertEqual(self.call(apply=True)[0], wt.REFUSED)
        self.assertFalse(self.exists())
        self.assertFalse(selected.exists())
        self.assertFalse(json.loads(self.manifest.read_text())["complete"])
        self.assertEqual(self.call(apply=True)[0], wt.OK, self.last_error)
        selected.mkdir()
        self.assertEqual(self.call(apply=True)[0], wt.REFUSED)
        self.assertTrue(selected.exists())

    def test_recovery_refuses_recreated_done_target(self):
        path, _ = self.worktree()
        real = purge.checked_git
        def fail_branch(wt_module, repo, *args):
            if args[0] == "update-ref":
                raise ValueError("injected branch-delete failure")
            return real(wt_module, repo, *args)
        with patch.object(purge, "checked_git", side_effect=fail_branch):
            self.assertEqual(self.call(apply=True)[0], wt.REFUSED)
        path.mkdir()
        (path / "new.txt").write_text("do not delete")
        self.assertEqual(self.call(apply=True)[0], wt.REFUSED)
        self.assertTrue(self.exists())
        self.assertTrue((path / "new.txt").exists())

    def test_invalid_manifest_refuses(self):
        self.manifest.parent.mkdir(parents=True)
        self.manifest.write_text("[]")
        self.assertEqual(self.call()[0], wt.REFUSED)
        self.assertTrue(self.exists())

    def test_cancelled_orphan_protected_branch_refuses(self):
        path, _ = self.worktree()
        self.board.transition_plan_item(self.database, self.task, "cancel")
        self.assertEqual(self.call(orphan=[["control", str(path), "main"]])[0], wt.REFUSED)
        self.assertIn("protected", self.last_error)
        self.assertTrue(path.exists())

    def test_repository_mapping_change_during_confirmation_refuses(self):
        mapping = self.repo / ".opencode/repos.json"
        with patch.object(purge, "confirm", side_effect=lambda _: mapping.write_text('{"control":".","other":"missing"}')):
            self.assertEqual(self.call(apply=True, confirm=False)[0], wt.REFUSED)
        self.assertIn("registration changed", self.last_error)
        self.assertTrue(self.exists())

    def test_cli_preview_and_no_unattended_flag(self):
        script = ROOT / ".opencode/skills/git-worktree/scripts/worktree.py"
        preview = subprocess.run(["python3", str(script), "purge", "--board", self.task],
                                 cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertFalse(self.manifest.exists())
        invalid = subprocess.run(["python3", str(script), "purge", "--board", self.task, "--yes"],
                                 cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(invalid.returncode, 2)


if __name__ == "__main__":
    (ROOT / ".tmp").mkdir(exist_ok=True)
    unittest.main()
