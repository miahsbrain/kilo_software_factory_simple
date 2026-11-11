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
        self.assertLess(out.index("diff main"), out.index("git merge --no-ff"))
        self.assertLess(out.index("git merge --no-ff"), out.index("cleanup --board BOARD-904"))
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
        board = os.path.join(self.repo, "docs", "BOARD.md")
        content = Path(board).read_text().replace("| Pending Merge |", "|  |")
        Path(board).write_text(content)
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
        board = Path(self.repo, "docs", "BOARD.md")
        content = board.read_text().replace("branch feat/hand-off-a-worktree", "")
        board.write_text(content)
        self.assert_withheld("cannot confirm the live branch")

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

    def test_already_merged_has_review_and_cleanup_but_no_merge(self):
        code, out, err = test_env.git(self.repo, "merge", "--no-ff", "feat/hand-off-a-worktree",
                                     "-m", "scratch merge")
        self.assertEqual(code, 0, err)
        self.set_status("Merged")
        code, out, err = self.handoff()
        self.assertEqual(code, worktree.OK, err)
        self.assertIn("show --stat main..feat/hand-off-a-worktree", out)
        self.assertIn("already merged", out)
        self.assertIn("cleanup --board BOARD-904", out)
        self.assertNotIn("git merge --no-ff", out)


if __name__ == "__main__":
    unittest.main()
