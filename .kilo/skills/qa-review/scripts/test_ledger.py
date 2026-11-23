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
        source = subprocess.run(["git", "rev-parse", "--show-toplevel"], check=True,
                                capture_output=True, text=True).stdout.strip()
        fixtures = Path(source) / "artifacts" / "tmp" / "tests"
        ledger.artifact_path(str(fixtures))
        fixtures.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="qa-ledger-", dir=fixtures)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / "artifacts" / "reviews"
        self.git(self.root, "init", "--quiet")
        cwd = patch("os.getcwd", return_value=str(self.root))
        cwd.start()
        self.addCleanup(cwd.stop)

    def run_ledger(self, *args):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = ledger.main(list(args))
        return code, output.getvalue(), errors.getvalue()

    def git(self, cwd, *args):
        return subprocess.run(["git", "-C", str(cwd), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def test_linked_checkout_keeps_outputs_in_source_worktree(self):
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
                expected = self.directory if cwd == self.root else linked / "artifacts" / "reviews"
                self.assertEqual(ledger.default_ledger_dir(str(cwd)), str(expected))
                with patch("os.getcwd", return_value=str(cwd)):
                    self.assertEqual(self.run_ledger("status", "--task-id", "BOARD-TEST")[0], 0)
        with patch("os.getcwd", return_value=str(linked)):
            self.assertEqual(self.run_ledger("next-round", "--task-id", "BOARD-TEST")[0], 0)
        self.assertTrue((linked / "artifacts" / "reviews" / "BOARD-TEST-ledger.md").exists())
        for suffix in ("qa", "ui", "review", "ledger"):
            path = "artifacts/reviews/BOARD-TEST-%s.md" % suffix
            self.assertEqual(self.git(self.root, "check-ignore", path), path)
        self.assertFalse(self.directory.exists())
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
        relative = os.path.relpath(self.directory, self.root)
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

    def test_outside_directory_and_task_traversal_refuse_without_writes(self):
        for directory in (self.root / "outside", self.root / "artifacts" / ".." / "outside"):
            code, _, error = self.run_ledger("--ledger-dir", str(directory), "next-round", "--task-id", "BOARD-TEST")
            self.assertEqual(code, 1)
            self.assertIn("inside caller worktree artifacts/", error)
            self.assertFalse(directory.exists())
        for task in (".", "..", "../escape", "/absolute", "a/b", "a\\b", ""):
            code, _, error = self.run_ledger("--ledger-dir", str(self.directory), "next-round", "--task-id", task)
            self.assertEqual(code, 1)
            self.assertIn("safe path segment", error)
        self.assertFalse(self.directory.exists())

    def test_symlink_root_ancestors_and_ledger_refuse_without_writes(self):
        target = self.root / "target"
        target.mkdir()
        artifacts = self.root / "artifacts"
        artifacts.symlink_to(target, target_is_directory=True)
        self.assertEqual(self.run_ledger("--ledger-dir", str(self.directory), "next-round", "--task-id", "BOARD-TEST")[0], 1)
        self.assertEqual(list(target.iterdir()), [])
        artifacts.unlink()
        artifacts.mkdir()
        (artifacts / "link").symlink_to(target, target_is_directory=True)
        self.assertEqual(self.run_ledger("--ledger-dir", str(artifacts / "link" / "absent"),
                                        "next-round", "--task-id", "BOARD-TEST")[0], 1)
        self.directory.mkdir()
        (self.directory / "BOARD-TEST-ledger.md").symlink_to(target / "untouched.md")
        self.assertEqual(self.run_ledger("--ledger-dir", str(self.directory), "next-round", "--task-id", "BOARD-TEST")[0], 1)
        self.assertEqual(list(target.iterdir()), [])

    def test_unknown_control_root_refuses_without_fallback(self):
        exists = os.path.exists
        # Fixtures now live inside the factory's artifacts tree. Hide only the
        # surrounding control markers so this test still represents an unknown repo.
        def isolated_exists(path):
            if str(path).endswith((".kilo/repos.json", "docs/BOARD.md")):
                return False
            return exists(path)
        with patch("os.path.exists", side_effect=isolated_exists):
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
