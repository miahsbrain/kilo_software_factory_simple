#!/usr/bin/env python3
"""Board refresh regressions using temporary trees, without a live server."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import board_serve as viewer


class BoardRefreshTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="board-refresh-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.factory = self.root / "docs" / "BOARD.md"
        self.project = self.root / "project" / "docs" / "BOARD.md"
        self.board = viewer.load_module("board_fixture_parser", Path(__file__).with_name("board.py"))
        self.worktree = SimpleNamespace(list_worktrees=lambda root: [])
        previous_state = viewer.Handler.state
        self.addCleanup(setattr, viewer.Handler, "state", previous_state)
        self.write_board(self.factory, "Factory task")
        (self.root / ".gitignore").write_text("/project/\n", encoding="utf-8")

    def write_board(self, path, task):
        path.parent.mkdir(parents=True, exist_ok=True)
        cells = ["BOARD-001", task, "Fix", "Ready", "P2", "low", "None.", "control", "-", "- [ ] Check"]
        path.write_text(
            "| " + " | ".join(viewer.COLUMNS) + " |\n"
            + "| " + " | ".join(["---"] * len(viewer.COLUMNS)) + " |\n"
            + "| " + " | ".join(cells) + " |\n", encoding="utf-8")

    def initialize(self, *args):
        server = Mock()
        with patch.object(viewer, "load_helpers", return_value=(self.board, self.worktree)), \
                patch.object(viewer, "repo_root", return_value=str(self.root)), \
                patch.object(viewer, "ThreadingHTTPServer", return_value=server), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(viewer.main(list(args)), 0)
        server.serve_forever.assert_called_once_with()
        server.server_close.assert_called_once_with()

    def request(self, path):
        response = Mock()
        handler = SimpleNamespace(
            path=path, state=viewer.Handler.state,
            send_json=lambda code, payload: response(code, json.dumps(payload)),
            send_bytes=lambda code, body, content_type: response(code, body.decode("utf-8")))
        viewer.Handler.do_GET(handler)
        code, body = response.call_args.args
        self.assertEqual(code, 200)
        return json.loads(body) if path.startswith("/api/") else body

    def test_project_appears_and_disappears_after_initialization(self):
        self.initialize()
        for present in (False, True, False, True):
            with self.subTest(project_present=present):
                if present:
                    self.write_board(self.project, "Project task")
                elif self.project.exists():
                    self.project.unlink()
                payload = self.request("/api/board")
                self.assertEqual(set(payload), {"boards", "generated_at"})
                entries = payload["boards"]
                self.assertEqual([entry["label"] for entry in entries],
                                 ["harness", "project"] if present else ["harness"])
                self.assertEqual([row["Task"] for row in entries[0]["rows"]], ["Factory task"])
                if present:
                    self.assertEqual([row["Task"] for row in entries[1]["rows"]], ["Project task"])
                    self.assertEqual(entries[1]["lanes"]["Ready"], ["BOARD-001"])
                page = self.request("/")
                self.assertIn('data-board-panel="harness"', page)
                self.assertEqual('data-board-panel="project"' in page, present)
                self.assertEqual("Project task" in page, present)
                self.assertIn("Factory task", page)
                self.assertEqual(self.request("/api/worktrees"), [])

    def test_explicit_file_stays_fixed_and_reads_edits(self):
        self.initialize("--file", str(self.factory))
        self.write_board(self.project, "Project task")
        self.write_board(self.factory, "Edited factory task")
        entries = self.request("/api/board")["boards"]
        self.assertEqual([entry["label"] for entry in entries], ["board"])
        self.assertEqual(entries[0]["path"], str(self.factory))
        self.assertEqual(entries[0]["rows"][0]["Task"], "Edited factory task")
        self.assertNotIn("Project task", self.request("/"))

    def test_default_refresh_and_existing_controls(self):
        self.initialize()
        self.assertEqual(viewer.DEFAULT_REFRESH, 60)
        self.assertEqual(viewer.Handler.state["refresh"], 60)
        page = self.request("/")
        self.assertIn('data-refresh="60"', page)
        self.assertIn("refresh every 60s, pausable", page)
        self.assertIn('getAttribute("data-refresh"), 10) || 60', page)
        self.assertIn('id="refresh">Refresh now</button>', page)
        self.assertIn('id="pause" aria-pressed="false">Pause</button>', page)
        self.assertIn('refreshBtn.addEventListener("click", function () { window.location.reload(); });', page)
        self.assertIn('if (paused) { return false; }', page)
        self.assertIn('pauseBtn.textContent = paused ? "Resume" : "Pause";', page)
        self.assertIn('if (boardIdle()) { window.location.reload(); }', page)
        self.assertIn('}, refreshSeconds * 1000);', page)

    def test_refresh_override(self):
        self.initialize("--refresh", "17")
        self.assertEqual(viewer.Handler.state["refresh"], 17)
        self.assertIn('data-refresh="17"', self.request("/"))


if __name__ == "__main__":
    unittest.main()
