#!/usr/bin/env python3
import contextlib
import io
import os
from pathlib import Path
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
        code, out, err = test_env.run(self.repo, self.script, "finalize", "--board", "BOARD-904")
        self.assertEqual(code, 0, out + err)
        self.assertFalse(os.path.exists(self.path))
        self.assertEqual(test_env.git(self.repo, "branch", "--list", "feat/hand-off-a-worktree")[1], "")
        self.assertEqual(board_file.read_bytes(), before)
        self.assertEqual(self.board_cells()[3], "Merged")
        self.assertEqual(self.board_cells()[8], "-")
        self.assertIn("recovery record:", out)

    def board_cells(self):
        import importlib.util
        path = Path(self.repo, ".opencode/skills/board/scripts/board.py")
        spec = importlib.util.spec_from_file_location("scratch_board", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        table, error = module.read_table(str(Path(self.repo, "docs/BOARD.md")))
        self.assertIsNone(error)
        return module.cell_texts(table["lines"], module.row_by_id(table, "BOARD-904"))

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
        test_env.write(os.path.join(self.repo, "kept.txt"), "competing base edit\n")
        code, _, err = test_env.git(self.repo, "add", "kept.txt")
        self.assertEqual(code, 0, err)
        code, _, err = test_env.git(self.repo, "commit", "-m", "competing base")
        self.assertEqual(code, 0, err)
        code, out, err = test_env.run(self.repo, self.script, "finalize", "--board", "BOARD-904")
        self.assertNotEqual(code, 0, out + err)
        self.assertIn("kept.txt", err)
        self.assertTrue(os.path.isdir(self.path))
        self.assertEqual(self.board_cells()[3], "Pending Merge")

    def test_retry_after_interrupted_board_update(self):
        with patch.object(worktree, "script_root", return_value=self.repo):
            with patch.object(worktree, "clear_row_worktree", return_value=(False, "injected")):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(worktree.cmd_finalize(SimpleNamespace(board="BOARD-904", repo=None),
                                                            self.repo), worktree.REFUSED)
        self.assertFalse(os.path.exists(self.path))
        self.assertEqual(self.board_cells()[3], "Pending Merge")
        code, out, err = test_env.run(self.repo, self.script, "finalize", "--board", "BOARD-904")
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


if __name__ == "__main__":
    unittest.main()
