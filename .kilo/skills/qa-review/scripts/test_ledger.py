import contextlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import ledger


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / "artifacts" / "reviews"

    def run_ledger(self, *args):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = ledger.main(list(args))
        return code, output.getvalue(), errors.getvalue()

    def git(self, cwd, *args):
        return subprocess.run(["git", "-C", str(cwd), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def test_main_and_linked_checkout_share_ignored_outputs(self):
        self.git(self.root, "init", "--quiet")
        (self.root / ".kilo").mkdir()
        (self.root / ".kilo" / "repos.json").write_text('{"control": "."}\n')
        (self.root / "docs").mkdir()
        (self.root / "docs" / "BOARD.md").write_text("# Board\n")
        (self.root / ".gitignore").write_text("artifacts/\n")
        self.git(self.root, "add", ".")
        self.git(self.root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "fixture")
        linked = self.root / ".kilo" / "worktrees" / "review"
        linked.parent.mkdir()
        self.git(self.root, "worktree", "add", "--quiet", "-b", "review", str(linked))
        for cwd in (self.root, linked, linked / "docs"):
            with self.subTest(cwd=cwd):
                self.assertEqual(ledger.default_ledger_dir(str(cwd)), str(self.directory))
                with patch("os.getcwd", return_value=str(cwd)):
                    self.assertEqual(self.run_ledger("status", "--task-id", "BOARD-TEST")[0], 0)
        with patch("os.getcwd", return_value=str(linked)):
            self.assertEqual(self.run_ledger("next-round", "--task-id", "BOARD-TEST")[0], 0)
        self.assertTrue((self.directory / "BOARD-TEST-ledger.md").exists())
        for suffix in ("qa", "ui", "review", "ledger"):
            path = "artifacts/reviews/BOARD-TEST-%s.md" % suffix
            self.assertEqual(self.git(self.root, "check-ignore", path), path)
        self.assertFalse((linked / "artifacts").exists())
        self.assertEqual(self.git(self.root, "ls-files", "artifacts"), "")

    def test_three_rounds_then_refusal_preserves_bytes_and_escalates_conditionally(self):
        args = ("--ledger-dir", str(self.directory))
        for number in range(1, 4):
            code, output, _ = self.run_ledger(*args, "next-round", "--task-id", "BOARD-TEST")
            self.assertEqual(code, 0)
            self.assertIn("round %d opened" % number, output)
        path = self.directory / "BOARD-TEST-ledger.md"
        before = path.read_bytes()
        code, _, error = self.run_ledger(*args, "next-round", "--task-id", "BOARD-TEST")
        self.assertEqual(code, 1)
        self.assertEqual(path.read_bytes(), before)
        for text in ("If round 3", "severity", "user impact", "evidence", "attempted fixes",
                     "stop reason", "orchestrator", "ask the user", "revised approach",
                     "defer/drop", "scoped follow-up", "successful round 3 does not imply blockers"):
            self.assertIn(text, error)
        code, output, _ = self.run_ledger(*args, "status", "--task-id", "BOARD-TEST")
        self.assertEqual(code, 0)
        self.assertIn("next round: none (cap reached)", output)
        self.assertNotIn("Blocked", output)

    def test_explicit_override_needs_no_control_root(self):
        relative = os.path.relpath(self.directory)
        with patch("os.getcwd", return_value=str(self.root)), \
                patch.object(ledger, "default_ledger_dir", side_effect=AssertionError("resolved")):
            code, _, _ = self.run_ledger("--ledger-dir", str(self.directory), "next-round",
                                       "--task-id", "BOARD-TEST")
            relative_code, _, _ = self.run_ledger("--ledger-dir", relative, "next-round",
                                                "--task-id", "BOARD-RELATIVE")
        self.assertEqual(code, 0)
        self.assertEqual(relative_code, 0)
        self.assertTrue((self.directory / "BOARD-RELATIVE-ledger.md").exists())
        self.assertEqual(ledger.ledger_path("relative", "BOARD-TEST"),
                         os.path.join("relative", "BOARD-TEST-ledger.md"))

    def test_unknown_control_root_refuses_without_fallback(self):
        with patch("os.getcwd", return_value=str(self.root)):
            code, _, error = self.run_ledger("next-round", "--task-id", "BOARD-TEST")
        self.assertEqual(code, 1)
        self.assertIn("refused:", error)
        self.git(self.root, "init", "--quiet")
        with patch("os.getcwd", return_value=str(self.root)):
            code, _, error = self.run_ledger("next-round", "--task-id", "BOARD-TEST")
        self.assertEqual(code, 1)
        self.assertIn("repo map and board are required", error)
        self.assertFalse((self.root / "docs" / "reviews").exists())
        self.assertFalse(self.directory.exists())

    def test_migrated_capped_ledger_is_preserved(self):
        original = self.root / "old-ledger.md"
        text = "# Historical ledger\n\n" + "".join(
            "## Round %d\n- Findings: historical evidence\n- Stop reason: capped\n\n" % n
            for n in range(1, 4))
        original.write_bytes(text.encode("utf-8"))
        self.directory.mkdir(parents=True)
        migrated = self.directory / "BOARD-OLD-ledger.md"
        shutil.copy2(original, migrated)
        args = ("--ledger-dir", str(self.directory))
        self.assertEqual(self.run_ledger(*args, "status", "--task-id", "BOARD-OLD")[0], 0)
        self.assertEqual(self.run_ledger(*args, "next-round", "--task-id", "BOARD-OLD")[0], 1)
        self.assertEqual(migrated.read_bytes(), original.read_bytes())

    def test_unreadable_ledger_does_not_become_new_history(self):
        with patch.object(ledger, "read_ledger", side_effect=PermissionError("denied")):
            code, _, error = self.run_ledger("--ledger-dir", str(self.directory), "next-round",
                                           "--task-id", "BOARD-TEST")
        self.assertEqual(code, 1)
        self.assertIn("denied", error)
        self.assertFalse(self.directory.exists())


if __name__ == "__main__":
    unittest.main()
