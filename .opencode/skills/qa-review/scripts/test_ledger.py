#!/usr/bin/env python3
import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("qa_ledger", Path(__file__).with_name("ledger.py"))
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)


class LedgerTaskIdTests(unittest.TestCase):
    def test_default_writer_refuses_legacy_state_before_creating_ledger(self):
        with tempfile.TemporaryDirectory() as folder:
            subprocess.run(["git", "-C", folder, "init"], check=True,
                           capture_output=True, text=True)
            legacy = Path(folder, ".git/reviews/BOARD-125-ledger.md")
            legacy.parent.mkdir()
            legacy.write_text("old report", encoding="utf-8")
            with patch.object(ledger.os, "getcwd", return_value=folder), \
                    contextlib.redirect_stderr(io.StringIO()) as errors:
                result = ledger.main(["next-round", "--task-id", "BOARD-125"])
            self.assertEqual(result, ledger.REFUSED)
            self.assertIn("run .opencode/skills/runtime-state/scripts/state.py migrate first",
                          errors.getvalue())
            self.assertFalse(Path(folder, ".factory-state").exists())

    def test_invalid_id_refused_before_git_or_file_access(self):
        with tempfile.TemporaryDirectory() as folder:
            for task_id in ("../../outside", "BOARD-12/../../outside", "BOARD-1/../2",
                            "BOARD-", "BOARD-1.md", "BOARD-１２", "BOARD-1\n"):
                with self.subTest(task_id=task_id), \
                        patch.object(ledger.subprocess, "run", side_effect=AssertionError("git access")), \
                        patch.object(ledger, "read_ledger", side_effect=AssertionError("file access")), \
                        contextlib.redirect_stderr(io.StringIO()) as errors:
                    self.assertEqual(ledger.main(["--ledger-dir", folder, "next-round",
                                                  "--task-id", task_id]), ledger.USAGE)
                    self.assertIn("expected BOARD-[0-9]+", errors.getvalue())
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_valid_id_writes_only_inside_selected_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(ledger.main(["--ledger-dir", folder, "next-round", "--task-id", "BOARD-124"]),
                             ledger.OK)
            self.assertEqual([entry.name for entry in Path(folder).iterdir()], ["BOARD-124-ledger.md"])


class LedgerRoundLimitTests(unittest.TestCase):
    def test_round_ten_opens_and_round_eleven_is_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            for _ in range(10):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(ledger.main(["--ledger-dir", folder, "next-round",
                                                  "--task-id", "BOARD-145"]), ledger.OK)

            with contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()) as errors:
                self.assertEqual(ledger.main(["--ledger-dir", folder, "next-round",
                                              "--task-id", "BOARD-145"]), ledger.REFUSED)
            self.assertIn("round cap of 10 is reached", errors.getvalue())
            self.assertIn("what was tried and the question for the human", errors.getvalue())
            text = Path(folder, "BOARD-145-ledger.md").read_text(encoding="utf-8")
            self.assertIn("Round cap: 10.", text)
            self.assertIn("## Round 10", text)
            self.assertNotIn("## Round 11", text)

    def test_status_reports_ten_round_cap(self):
        with tempfile.TemporaryDirectory() as folder:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(ledger.main(["--ledger-dir", folder, "status",
                                              "--task-id", "BOARD-145"]), ledger.OK)
            self.assertIn("rounds used: 0 of 10", output.getvalue())


if __name__ == "__main__":
    unittest.main()
