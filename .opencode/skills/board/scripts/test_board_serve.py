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
        self.worktree = viewer.load_module(
            "worktree_fixture_helpers", Path(__file__).parents[2] / "git-worktree/scripts/worktree.py")
        self.worktree.list_worktrees = Mock(return_value=[])
        self.worktree.is_git_repo = Mock(return_value=False)
        self.registry = self.root / ".opencode" / "repos.json"
        self.registry.parent.mkdir()
        self.registry.write_text(json.dumps({"control": ".", "project": "project"}), encoding="utf-8")
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

    def mock_repository_git(self):
        self.worktree = viewer.load_module(
            "worktree_registry_helpers", Path(__file__).parents[2] / "git-worktree/scripts/worktree.py")
        results = {}
        project = self.root / "registered-product"
        marker = self.root / "templates/project/AGENTS.md"
        marker.parent.mkdir(parents=True)
        marker.write_text("fixture", encoding="utf-8")
        project.mkdir()
        (project / "DOMAIN.md").write_text("fixture", encoding="utf-8")
        for target, base, counts in ((self.root, "opencode", (2, 1)),
                                     (project, "main", (5, 3))):
            linked = target / ".opencode/worktrees/shared"
            results[(str(target), "rev-parse", "--show-toplevel")] = str(target)
            results[(str(target), "rev-parse", "-q", "--verify", "refs/heads/" + base)] = "base-sha"
            results[(str(target), "worktree", "list", "--porcelain")] = (
                "worktree %s\nHEAD abcdef012345\nbranch refs/heads/%s\n\n"
                "worktree %s\nHEAD fedcba987654\nbranch refs/heads/fix/shared\n\n"
                % (target, base, linked))
            for path, main in ((target, True), (linked, False)):
                results[(str(path), "rev-parse", "--short", "HEAD")] = "abcdef0" if main else "fedcba9"
                results[(str(path), "rev-list", "--count", base + "..HEAD")] = "0" if main else str(counts[0])
                results[(str(path), "rev-list", "--count", "HEAD.." + base)] = "0" if main else str(counts[1])
                results[(str(path), "status", "--porcelain")] = (
                    " M fixture" if target == project and not main else "")

        def git(path, *args, **kwargs):
            value = results.get((str(path), *args))
            return (0, value, "") if value is not None else (1, "", "fixture: unavailable")

        self.worktree.git = Mock(side_effect=git)
        return project, results

    def test_registered_worktrees_are_fresh_and_isolated_by_repository(self):
        project, results = self.mock_repository_git()
        self.initialize()
        control = self.request("/api/worktrees")
        self.assertEqual([entry["repo"] for entry in control], ["control", "control"])

        self.registry.write_text(json.dumps({"control": ".", "project": project.name}), encoding="utf-8")
        entries = self.request("/api/worktrees")
        self.assertEqual(len(entries), 4)
        old_keys = {"path", "branch", "sha", "ahead", "behind", "dirty", "main"}
        for entry in entries:
            self.assertEqual(set(entry), old_keys | {"repo", "base"})
        for repo_id, base, expected in (("control", "opencode", (2, 1, False)),
                                         ("project", "main", (5, 3, True))):
            group = [entry for entry in entries if entry["repo"] == repo_id]
            self.assertEqual([entry["main"] for entry in group], [True, False])
            self.assertEqual([entry["base"] for entry in group], [base, base])
            self.assertEqual(group[0]["branch"], base)
            self.assertEqual((group[0]["ahead"], group[0]["behind"]), (0, 0))
            self.assertEqual(group[1]["branch"], "fix/shared")
            self.assertEqual(group[1]["sha"], "fedcba9")
            self.assertEqual((group[1]["ahead"], group[1]["behind"], group[1]["dirty"]), expected)
        page = self.request("/")
        self.assertIn("4 worktrees · 2 non-main", page)
        self.assertIn(str(project / ".opencode/worktrees/shared"), page)

        linked = str(project / ".opencode/worktrees/shared")
        results.pop((linked, "rev-parse", "--short", "HEAD"))
        results.pop((linked, "rev-list", "--count", "main..HEAD"))
        fresh = self.request("/api/worktrees")
        self.assertEqual(fresh[-1]["sha"], "fedcba9")
        self.assertIsNone(fresh[-1]["ahead"])
        self.assertEqual(fresh[:2], control)

        for registry in ({"control": ".", "project": "missing"},
                         {"control": ".", "project": "uninitialized"},
                         {"control": "."}):
            with self.subTest(registry=registry):
                uninitialized = self.root / "uninitialized"
                uninitialized.mkdir(exist_ok=True)
                # Git in an uninitialized child can report the enclosing control repo.
                results[(str(uninitialized), "rev-parse", "--show-toplevel")] = str(self.root)
                self.registry.write_text(json.dumps(registry), encoding="utf-8")
                self.assertEqual(self.request("/api/worktrees"), control)
                self.assertIn("2 worktrees · 1 non-main", self.request("/"))

    def test_invalid_registry_uses_existing_payload_error_handling(self):
        self.initialize()
        for content in ("{", json.dumps({"control": ".", "project": "../outside"})):
            with self.subTest(content=content):
                self.worktree.list_worktrees.reset_mock()
                self.registry.write_text(content, encoding="utf-8")
                self.assertEqual(self.request("/api/worktrees"), [])
                self.assertIn("could not read the board:", self.request("/"))
                self.assertTrue(all(call.args == (str(self.root),)
                                    for call in self.worktree.list_worktrees.call_args_list))


if __name__ == "__main__":
    unittest.main()
