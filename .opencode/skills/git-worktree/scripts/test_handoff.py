#!/usr/bin/env python3
import contextlib
import io
import json
import os
import shlex
import sqlite3
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import test_env
import worktree


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="handoff-test-", dir=Path(__file__).parents[4])
        self.addCleanup(self.temp.cleanup)
        self.repo = test_env.make_repo(self.temp.name)
        self.script = os.path.join(self.repo, ".opencode", "skills", "git-worktree", "scripts",
                                   "worktree.py")
        code, out, err = test_env.run(self.repo, self.script, "create", "--board", "BOARD-904")
        self.assertEqual(code, 0, out + err)
        self.path = os.path.join(self.repo, ".opencode", "worktrees", "hand-off-a-worktree")
        test_env.write(os.path.join(self.path, "kept.txt"), "committed work\n")
        self.git("add", "kept.txt")
        self.git("commit", "-m", "task work")
        self.set_status("Pending Merge")
        self.args = SimpleNamespace(board="BOARD-904", repo=None, base="main")

    def test_recovery_path_refuses_legacy_state_before_creating_state_directory(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parents[4]) as folder:
            subprocess.run(["git", "-C", folder, "init"], check=True,
                           capture_output=True, text=True)
            old_recovery = Path(folder, ".git/cleanup-wt/recovery.patch")
            old_recovery.parent.mkdir()
            old_recovery.write_bytes(b"recovery")
            with self.assertRaisesRegex(OSError, "run .*state.py migrate"):
                worktree.recovery_directory(folder, "control")
            self.assertFalse(Path(folder, ".factory-state").exists())

    def git(self, *args):
        code, out, err = test_env.git(self.path, *args)
        self.assertEqual(code, 0, err)
        return out

    def set_status(self, status):
        script = os.path.join(self.repo, ".opencode", "skills", "board", "scripts", "board.py")
        code, out, err = test_env.run(self.repo, script, "set-status", "BOARD-904", status)
        self.assertEqual(code, 0, out + err)

    def handoff(self):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(worktree, "script_root", return_value=self.repo):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = worktree.cmd_handoff(self.args, self.repo)
        return code, out.getvalue(), err.getvalue()

    def assert_withheld(self, reason):
        code, out, err = self.handoff()
        self.assertEqual(code, worktree.REFUSED, out + err)
        self.assertIn(reason, out + err)
        self.assertNotIn("git merge --no-ff", out + err)
        self.assertNotIn("cleanup --board", out + err)
        self.assertNotIn("git worktree remove", out + err)
        self.assertNotIn("git branch -d", out + err)
        return out

    def test_clean_pending_merge_has_diff_before_merge_and_cleanup(self):
        code, out, err = self.handoff()
        self.assertEqual(code, worktree.OK, err)
        self.assertLess(out.index("diff main"), out.index("finalize --board BOARD-904"))
        self.assertNotIn("git merge --no-ff", out)
        self.assertNotIn("cleanup --board", out)
        self.assertIn("log --oneline main..HEAD", out)
        command = next(line.strip() for line in out.splitlines() if " finalize --board " in line)
        self.assertEqual(shlex.split(command), ["python3", self.script, "finalize", "--board", "BOARD-904"])

    def test_app_repo_handoff_uses_control_script_from_target_checkout(self):
        target = Path(self.repo, "apps", "app with spaces")
        target.mkdir(parents=True)
        self.args.repo = "app"
        with patch.object(worktree, "resolve_repo", return_value=(str(target), None)), \
                patch.object(worktree, "live_row_worktree", return_value=(self.path, "feat/hand-off-a-worktree")):
            code, out, err = self.handoff()
        self.assertEqual(code, worktree.OK, err)
        self.assertIn("run from '%s'" % target, out)
        command = next(line.strip() for line in out.splitlines() if " finalize --board " in line)
        self.assertEqual(shlex.split(command), ["python3", self.script, "finalize", "--board",
                                                 "BOARD-904", "--repo", "app"])
        self.assertFalse((target / ".opencode/skills/git-worktree/scripts/worktree.py").exists())

    def test_untracked_changes_withhold_merge(self):
        test_env.write(os.path.join(self.path, "untracked.txt"), "new\n")
        out = self.assert_withheld("untracked changes")
        self.assertIn("diff main", out)
        self.assertIn("log --oneline main..HEAD", out)

    def test_unstaged_changes_withhold_merge(self):
        test_env.write(os.path.join(self.path, "kept.txt"), "changed\n")
        self.assert_withheld("unstaged")

    def test_staged_changes_withhold_merge(self):
        test_env.write(os.path.join(self.path, "kept.txt"), "staged\n")
        self.git("add", "kept.txt")
        self.assert_withheld("staged")

    def test_nonready_statuses_withhold_merge(self):
        for status in ("In Progress", "Blocked", "In Review", "Ready", "Backlog", "Dropped", "Merged"):
            with self.subTest(status=status):
                self.set_status(status)
                self.assert_withheld("board status is %s, not Pending Merge" % status)

    def test_missing_status_withholds_merge(self):
        self.change_cell(3, "")
        self.assert_withheld("board status is missing")

    def test_no_task_commits_withholds_merge(self):
        self.args.base = "feat/hand-off-a-worktree"
        self.assert_withheld("no committed work ahead")

    def test_git_failures_and_empty_commit_count_fail_closed(self):
        original = worktree.git
        failures = (("status", (1, "", "failed")),
                    ("symbolic-ref", (1, "", "failed")),
                    ("rev-list", (1, "", "failed")),
                    ("rev-list", (0, "", "")),
                    ("merge-base", (128, "", "failed")),
                    ("rev-parse", (1, "", "failed")))
        for command, result in failures:
            with self.subTest(command=command, result=result):
                def failing_git(cwd, *args, **kwargs):
                    if cwd == self.path and args[0] == command:
                        return result
                    return original(cwd, *args, **kwargs)
                with patch.object(worktree, "git", side_effect=failing_git):
                    reason = "failed" if command in ("status", "merge-base") else "cannot"
                    self.assert_withheld(reason)

    def test_missing_branch_information_withholds_merge(self):
        self.change_cell(8, ".opencode/worktrees/hand-off-a-worktree · branch ")
        self.assert_withheld("cannot confirm the live branch")

    def change_cell(self, column, value):
        import importlib.util
        location = Path(self.repo, ".opencode/skills/board/scripts/board.py")
        spec = importlib.util.spec_from_file_location("scratch_board_edit", location)
        board = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(board)
        board_file = str(Path(self.repo, "docs/BOARD.md"))
        table, error = board.read_table(board_file)
        self.assertIsNone(error)
        index = board.row_by_id(table, "BOARD-904")
        lines = list(table["lines"])
        lines[index] = board.replace_cell(lines[index], column, value)
        board.write_atomic(board_file, lines)

    def test_missing_base_withholds_merge(self):
        self.args.base = "missing-base"
        self.assert_withheld("base branch missing-base does not exist")

    def test_handoff_does_not_change_board_or_worktree(self):
        board = Path(self.repo, "docs", "BOARD.md")
        before = board.read_bytes()
        status = self.git("status", "--porcelain", "--untracked-files=all")
        self.assertEqual(self.handoff()[0], worktree.OK)
        self.assertEqual(board.read_bytes(), before)
        self.assertEqual(self.git("status", "--porcelain", "--untracked-files=all"), status)

    def test_missing_board_or_worktree_refuses(self):
        self.args.board = "BOARD-901"
        self.assert_withheld("no live worktree")
        self.args.board = "BOARD-999"
        self.assert_withheld("no row with ID")

    def test_review_correction_resumes_same_worktree_without_fix_row(self):
        before = self.board_cells()
        self.set_status("In Progress")
        code, out, err = test_env.run(self.repo, self.script, "resume", "--board", "BOARD-904")
        self.assertEqual(code, 0, out + err)
        self.assertIn(self.path, out)
        code, out, err = test_env.run(self.repo, self.script, "create", "--board", "BOARD-904")
        self.assertNotEqual(code, 0)
        self.assertIn("already has a live worktree", err)
        self.assertEqual(self.board_cells()[8], before[8])
        self.assertEqual(len(worktree.list_worktrees(self.repo)), 2)

    def test_already_merged_pending_row_offers_finalize_but_no_merge(self):
        code, out, err = test_env.git(self.repo, "merge", "--no-ff", "feat/hand-off-a-worktree",
                                     "-m", "scratch merge")
        self.assertEqual(code, 0, err)
        code, out, err = self.handoff()
        self.assertEqual(code, worktree.OK, err)
        self.assertIn("show --stat main..feat/hand-off-a-worktree", out)
        self.assertIn("already merged", out)
        self.assertIn("finalize --board BOARD-904", out)
        self.assertNotIn("git merge --no-ff", out)
        self.set_status("Merged")
        self.assert_withheld("not Pending Merge")

    def test_human_finalize_integrates_cleans_and_preserves_board_file(self):
        board_file = Path(self.repo, "docs", "BOARD.md")
        before = board_file.read_bytes()
        code, out, err = self.finalize_confirmed()
        self.assertEqual(code, 0, out + err)
        self.assertFalse(os.path.exists(self.path))
        self.assertEqual(test_env.git(self.repo, "branch", "--list", "feat/hand-off-a-worktree")[1], "")
        self.assertEqual(board_file.read_bytes(), before)
        self.assertEqual(self.board_cells()[3], "Merged")
        self.assertEqual(self.board_cells()[8], "-")
        self.assertIn("recovery record:", out)

    def test_finalize_script_inside_removed_worktree_updates_sqlite(self):
        script = os.path.join(self.path, ".opencode/skills/git-worktree/scripts/worktree.py")
        self.assertTrue(os.path.isfile(script))
        code, out, err = self.finalize_confirmed(script=script)
        self.assertEqual(code, 0, out + err)
        self.assertFalse(os.path.exists(script))
        self.assertEqual(self.board_cells()[3], "Merged")
        self.assertEqual(self.board_cells()[8], "-")

    def test_replay_after_worktree_and_branch_removed_with_script_in_worktree(self):
        script = os.path.join(self.path, ".opencode/skills/git-worktree/scripts/worktree.py")
        with patch.object(worktree, "clear_row_worktree", return_value=(False, "injected")):
            code, out, err = self.finalize_confirmed(script=script)
        self.assertEqual(code, worktree.REFUSED, out + err)
        self.assertFalse(os.path.exists(self.path))
        self.assertEqual(test_env.git(self.repo, "branch", "--list", "feat/hand-off-a-worktree")[1], "")
        self.assertEqual(self.board_cells()[3], "Pending Merge")
        code, out, err = self.finalize_confirmed()
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.board_cells()[3], "Merged")
        self.assertEqual(self.board_cells()[8], "-")

    def test_invalid_recovery_record_refuses_before_cleanup(self):
        journal = Path(self.repo, ".factory-state/cleanup-wt/control/finalize-BOARD-904.json")
        journal.parent.mkdir(parents=True, exist_ok=True)
        journal.write_text('{"path":"wrong"}')
        code, out, err = self.finalize_confirmed()
        self.assertEqual(code, worktree.REFUSED, out + err)
        self.assertIn("recovery record does not match", err)
        self.assertTrue(os.path.isdir(self.path))
        self.assertEqual(self.board_cells()[3], "Pending Merge")

    def test_legacy_control_journal_is_replayed_without_renaming(self):
        journal = Path(self.repo, ".factory-state/cleanup-wt/control/"
                                 "finalize-BOARD-904-control.json")
        journal.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "path": self.path,
            "branch": "feat/hand-off-a-worktree",
            "tip": self.git("rev-parse", "HEAD"),
            "base": "main",
            "base_tip": self.git("rev-parse", "main"),
        }
        original = json.dumps(record).encode("utf-8")
        journal.write_bytes(original)

        code, out, err = self.finalize_confirmed()

        self.assertEqual(code, worktree.OK, out + err)
        self.assertFalse(os.path.exists(self.path))
        self.assertEqual(journal.read_bytes(), original)
        self.assertIn(str(journal), out)
        self.assertEqual(self.board_cells()[3], "Merged")

    def test_incomplete_journal_never_publishes_or_merges_and_retry_works(self):
        journal = Path(self.repo, ".factory-state/cleanup-wt/control/finalize-BOARD-904.json")
        for operation in ("fsync", "link"):
            with self.subTest(operation=operation):
                with patch.object(worktree.os, operation, side_effect=OSError("injected failure")):
                    code, out, err = self.finalize_confirmed()
                self.assertEqual(code, worktree.REFUSED, out + err)
                self.assertIn("recovery record is not durable", err)
                self.assertFalse(journal.exists())
                self.assertEqual(list(journal.parent.glob(".finalize-*.tmp")), [])
                self.assertTrue(os.path.isdir(self.path))
                self.assertEqual(self.board_cells()[3], "Pending Merge")
                self.assertEqual(test_env.git(self.repo, "rev-list", "--count",
                                              "main..feat/hand-off-a-worktree")[1], "1")
        code, out, err = self.finalize_confirmed()
        self.assertEqual(code, worktree.OK, out + err)
        self.assertEqual(self.board_cells()[3], "Merged")

    def test_board_writer_cannot_revoke_approval_during_git_integration(self):
        original = worktree.git
        lock_observed = []

        def check_lock(cwd, *args, **kwargs):
            if cwd == self.repo and args[:2] == ("merge", "--no-ff"):
                board = worktree.load_board_module(self.repo)
                with sqlite3.connect(board.database_path(self.repo), timeout=0) as rival:
                    with self.assertRaisesRegex(sqlite3.OperationalError, "locked"):
                        rival.execute("BEGIN IMMEDIATE")
                lock_observed.append(True)
            return original(cwd, *args, **kwargs)

        with patch.object(worktree, "git", side_effect=check_lock):
            code, out, err = self.finalize_confirmed()
        self.assertEqual(code, worktree.OK, out + err)
        self.assertEqual(lock_observed, [True])
        self.assertEqual(self.board_cells()[3], "Merged")

    def test_finalize_preserves_unrelated_sqlite_row(self):
        board_script = os.path.join(self.repo, ".opencode/skills/board/scripts/board.py")
        code, out, err = test_env.run(self.repo, board_script, "set-status", "BOARD-901", "Blocked")
        self.assertEqual(code, 0, out + err)
        code, out, err = self.finalize_confirmed()
        self.assertEqual(code, worktree.OK, out + err)
        board = worktree.load_board_module(self.repo)
        table, error = board.read_table(os.path.join(self.repo, "docs/BOARD.md"))
        self.assertIsNone(error)
        row = board.row_by_id(table, "BOARD-901")
        self.assertEqual(board.cell_texts(table["lines"], row)[3], "Blocked")

    def test_finalize_preserves_other_repo_worktree_entry(self):
        other = "apps/api/.opencode/worktrees/api-task · branch feat/api-task"
        board_script = os.path.join(self.repo, ".opencode/skills/board/scripts/board.py")
        cell = self.board_cells()[8] + ", " + other
        code, out, err = test_env.run(self.repo, board_script, "set-field", "BOARD-904",
                                      "--field", "branch-worktree", "--value", cell)
        self.assertEqual(code, 0, out + err)
        code, out, err = self.finalize_confirmed()
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.board_cells()[3], "Pending Merge")
        self.assertEqual(self.board_cells()[8], other)

    def test_board_change_during_confirmation_refuses(self):
        def change_board(*args):
            self.set_status("Blocked")
            return True
        with patch.object(worktree, "script_root", return_value=self.repo), \
                patch.object(worktree, "confirm_finalize", side_effect=change_board), \
                contextlib.redirect_stderr(io.StringIO()):
            code = worktree.cmd_finalize(self.args, self.repo)
        self.assertEqual(code, worktree.REFUSED)
        self.assertTrue(os.path.isdir(self.path))

    def board_cells(self):
        import importlib.util
        path = Path(self.repo, ".opencode/skills/board/scripts/board.py")
        spec = importlib.util.spec_from_file_location("scratch_board", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        table, error = module.read_table(str(Path(self.repo, "docs/BOARD.md")))
        self.assertIsNone(error)
        return module.cell_texts(table["lines"], module.row_by_id(table, "BOARD-904"))

    def finalize_confirmed(self, script=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        with (patch.object(worktree, "__file__", script) if script else
              patch.object(worktree, "script_root", return_value=self.repo)), \
                 patch.object(worktree, "confirm_finalize", return_value=True), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = worktree.cmd_finalize(SimpleNamespace(board="BOARD-904", repo=None), self.repo)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_confirmation_refuses_noninteractive_and_wrong_input(self):
        code, out, err = test_env.run(self.repo, self.script, "finalize", "--board", "BOARD-904")
        self.assertNotEqual(code, 0)
        self.assertIn("interactive terminal", err)
        self.assertTrue(Path(self.path).is_dir())
        self.assertEqual(self.board_cells()[3], "Pending Merge")
        tip = self.git("rev-parse", "HEAD")
        expected = "BOARD-904 main feat/hand-off-a-worktree %s" % tip

        class TtyStream(io.StringIO):
            def __init__(self, value="", *, tty=True, failure=None):
                super().__init__(value)
                self.tty = tty
                self.failure = failure

            def isatty(self):
                return self.tty

            def readline(self):
                if self.failure:
                    raise self.failure
                return super().readline()

        for answer, accepted in (("no\n", False), ("yes\n", True),
                                 ("yes\r\n", True), ("", False),
                                 ("YES\n", False), ("yes", False),
                                 (expected + "\n", False), ("yes\n\n", True)):
            with self.subTest(answer=answer):
                stdin, stderr = TtyStream(answer), TtyStream()
                with patch.object(worktree.sys, "stdin", stdin), patch.object(worktree.sys, "stderr", stderr):
                    self.assertIs(worktree.confirm_finalize("BOARD-904", "main",
                        "feat/hand-off-a-worktree", tip), accepted)
                for value in ("BOARD-904", "main", "feat/hand-off-a-worktree", tip):
                    self.assertIn(value, stderr.getvalue())
                self.assertIn("Type exactly yes", stderr.getvalue())
                self.assertEqual(stdin.readline(), "\n" if answer.endswith("\n\n") else "")

        for stdin_tty, stderr_tty in ((False, True), (True, False)):
            with self.subTest(stdin_tty=stdin_tty, stderr_tty=stderr_tty):
                stdin, stderr = TtyStream("yes\n", tty=stdin_tty), TtyStream(tty=stderr_tty)
                with patch.object(worktree.sys, "stdin", stdin), patch.object(worktree.sys, "stderr", stderr):
                    self.assertFalse(worktree.confirm_finalize("BOARD-904", "main",
                        "feat/hand-off-a-worktree", tip))
                self.assertNotIn(tip, stderr.getvalue())
                self.assertEqual(stdin.readline(), "yes\n")

        for failure in (OSError("read failed"), UnicodeError("invalid input"), KeyboardInterrupt()):
            with self.subTest(failure=type(failure).__name__):
                stdin, stderr = TtyStream(failure=failure), TtyStream()
                with patch.object(worktree.sys, "stdin", stdin), patch.object(worktree.sys, "stderr", stderr):
                    self.assertFalse(worktree.confirm_finalize("BOARD-904", "main",
                        "feat/hand-off-a-worktree", tip))
                self.assertIn("confirmation interrupted or unavailable", stderr.getvalue())

        stdin, stderr = TtyStream("yes\n"), TtyStream()
        with patch.object(worktree.sys, "stdin", stdin), patch.object(worktree.sys, "stderr", stderr), \
                patch.object(stderr, "flush", side_effect=OSError("write failed")):
            self.assertFalse(worktree.confirm_finalize("BOARD-904", "main",
                "feat/hand-off-a-worktree", tip))
        self.assertEqual(stdin.readline(), "yes\n")

    def test_failed_merge_aborts_only_own_merge_and_preserves_task(self):
        original = worktree.git
        aborted = []

        def failing_merge(cwd, *args, **kwargs):
            if cwd == self.repo and args[:2] == ("merge", "--no-ff"):
                Path(self.repo, ".git/MERGE_HEAD").write_text(self.git("rev-parse", "HEAD") + "\n")
                return 1, "", "injected merge failure"
            if cwd == self.repo and args[:2] == ("merge", "--abort"):
                aborted.append(True)
                Path(self.repo, ".git/MERGE_HEAD").unlink()
                return 0, "", ""
            return original(cwd, *args, **kwargs)

        with patch.object(worktree, "script_root", return_value=self.repo), \
                patch.object(worktree, "confirm_finalize", return_value=True), \
                patch.object(worktree, "git", side_effect=failing_merge), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(worktree.cmd_finalize(SimpleNamespace(board="BOARD-904", repo=None),
                                                    self.repo), worktree.REFUSED)
        self.assertEqual(aborted, [True])
        self.assertTrue(Path(self.path).is_dir())
        self.assertEqual(self.board_cells()[3], "Pending Merge")
        self.assertEqual(test_env.git(self.repo, "status", "--porcelain")[1], "")

    def test_finalize_refuses_unfinished_and_dirty(self):
        self.set_status("In Review")
        code, out, err = test_env.run(self.repo, self.script, "finalize", "--board", "BOARD-904")
        self.assertNotEqual(code, 0)
        self.assertIn("not Pending Merge", err)
        self.set_status("Pending Merge")
        test_env.write(os.path.join(self.path, "dirty.txt"), "scratch\n")
        code, out, err = test_env.run(self.repo, self.script, "finalize", "--board", "BOARD-904")
        self.assertNotEqual(code, 0)
        self.assertIn("dirty", err)
        self.assertTrue(os.path.isdir(self.path))

    def test_conflict_preflight_retains_both_worktrees_and_row(self):
        self.git("add", "kept.txt")
        test_env.write(os.path.join(self.path, "kept.txt"), "task side\n")
        self.git("add", "kept.txt")
        self.git("commit", "-m", "task edit")
        test_env.write(os.path.join(self.repo, "kept.txt"), "competing base edit\n")
        code, _, err = test_env.git(self.repo, "add", "kept.txt")
        self.assertEqual(code, 0, err)
        code, _, err = test_env.git(self.repo, "commit", "-m", "competing base")
        self.assertEqual(code, 0, err)
        code, out, err = test_env.run(self.repo, self.script, "finalize", "--board", "BOARD-904")
        self.assertNotEqual(code, 0, out + err)
        self.assertIn("kept.txt", err)
        self.assertIn("add/add", err)
        self.assertTrue(os.path.isdir(self.path))
        self.assertEqual(self.board_cells()[3], "Pending Merge")
        self.assertEqual(test_env.git(self.repo, "status", "--porcelain")[1], "")

    def test_retry_after_interrupted_board_update(self):
        with patch.object(worktree, "script_root", return_value=self.repo):
            with patch.object(worktree, "clear_row_worktree", return_value=(False, "injected")), \
                    patch.object(worktree, "confirm_finalize", return_value=True):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(worktree.cmd_finalize(SimpleNamespace(board="BOARD-904", repo=None),
                                                            self.repo), worktree.REFUSED)
        self.assertFalse(os.path.exists(self.path))
        self.assertEqual(self.board_cells()[3], "Pending Merge")
        code, out, err = self.finalize_confirmed()
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.board_cells()[3], "Merged")


class EnvFailureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="env-failure-", dir=Path(__file__).parents[4])
        self.addCleanup(self.temp.cleanup)
        self.repo = test_env.make_repo(self.temp.name)
        self.script = os.path.join(self.repo, ".opencode/skills/git-worktree/scripts/worktree.py")
        self.source = Path(self.repo, ".env")
        self.path = Path(self.repo, ".opencode/worktrees/hand-off-a-worktree")

    def test_source_symlink_blocks_create_and_records_partial_worktree(self):
        self.source.symlink_to(Path(self.temp.name, "missing"))
        code, out, err = test_env.run(self.repo, self.script, "create", "--board", "BOARD-904")
        self.assertNotEqual(code, 0)
        self.assertIn("source is not a regular file", err)
        self.assertTrue(self.path.is_dir())
        self.assertNotIn("board:    BOARD-904", out)
        code, out, err = test_env.run(self.repo, self.script, "create", "--board", "BOARD-904",
                                      "--slug", "different")
        self.assertNotEqual(code, 0)
        self.assertNotIn("new slug:", err)
        self.source.unlink()
        code, out, err = test_env.run(self.repo, self.script, "resume", "--board", "BOARD-904")
        self.assertEqual(code, 0, out + err)

    def test_failed_resume_does_not_advance_lane(self):
        code, out, err = test_env.run(self.repo, self.script, "create", "--board", "BOARD-904")
        self.assertEqual(code, 0, out + err)
        self.source.symlink_to(Path(self.temp.name, "missing"))
        code, out, err = test_env.run(self.repo, self.script, "resume", "--board", "BOARD-904")
        self.assertNotEqual(code, 0)
        self.assertNotIn("is In Progress", out)


class BoardMigrationTests(unittest.TestCase):
    def test_untracked_legacy_board_preserves_sqlite_and_fresh_clone_starts_empty(self):
        with tempfile.TemporaryDirectory(prefix="migration-test-", dir=Path(__file__).parents[4]) as temp:
            repo = test_env.make_repo(temp)
            test_env.write(str(Path(repo, ".gitignore")),
                           "/.factory-state/\n.opencode/worktrees/\n__pycache__/\ndocs/BOARD.md\n")
            self.assertEqual(test_env.git(repo, "add", ".gitignore")[0], 0)
            self.assertEqual(test_env.git(repo, "commit", "-m", "ignore runtime files")[0], 0)
            board_script = Path(repo, ".opencode/skills/board/scripts/board.py")
            original = Path(repo, "docs/BOARD.md").read_bytes()
            code, out, err = test_env.run(repo, str(board_script), "show", "BOARD-904")
            self.assertEqual(code, 0, out + err)
            module = worktree.load_board_module(repo)
            with module.connect(module.database_path(repo)) as connection:
                saved = connection.execute("SELECT source_bytes FROM board WHERE id = 1").fetchone()[0]
            self.assertEqual(saved, original)

            task = Path(repo, ".opencode/worktrees/migration")
            task.parent.mkdir(parents=True, exist_ok=True)
            code, out, err = test_env.git(repo, "worktree", "add", "-b", "migration", str(task))
            self.assertEqual(code, 0, err)
            code, out, err = test_env.git(str(task), "rm", "--cached", "--", "docs/BOARD.md")
            self.assertEqual(code, 0, err)
            self.assertEqual((task / "docs/BOARD.md").read_bytes(), original)
            code, out, err = test_env.git(str(task), "commit", "-m", "untrack legacy board")
            self.assertEqual(code, 0, err)
            code, out, err = test_env.git(repo, "merge", "--no-ff", "migration", "-m", "integrate")
            self.assertEqual(code, 0, err)
            self.assertEqual(test_env.git(repo, "status", "--porcelain")[1], "")
            code, out, err = test_env.run(repo, str(board_script), "export")
            self.assertEqual(code, 0, out + err)
            self.assertIn("BOARD-904", Path(module.database_path(repo)).with_name(
                "factory-board-export.md").read_text())

            clone = Path(temp, "fresh-clone")
            result = subprocess.run(["git", "clone", "--quiet", "--", repo, str(clone)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((clone / "docs/BOARD.md").exists())
            code, out, err = test_env.run(str(clone), str(clone / ".opencode/skills/board/scripts/board.py"),
                                          "show")
            self.assertEqual(code, 0, out + err)
            self.assertNotIn("BOARD-904", out)


if __name__ == "__main__":
    unittest.main()
