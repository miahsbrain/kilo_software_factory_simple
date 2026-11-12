#!/usr/bin/env python3
import contextlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("qa_ledger", Path(__file__).with_name("ledger.py"))
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)


class LedgerTaskIdTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
