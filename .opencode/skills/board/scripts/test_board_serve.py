#!/usr/bin/env python3
"""Board refresh regressions using temporary trees, without a live server."""
import contextlib
import io
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
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
        (self.root / ".gitignore").write_text(
            "/project/\n/.factory-state/\n", encoding="utf-8")

    def write_board(self, path, task):
        path.parent.mkdir(parents=True, exist_ok=True)
        cells = ["BOARD-001", task, "Fix", "Ready", "P2", "low", "None.", "control", "-", "- [ ] Check"]
        path.write_text(
            "| " + " | ".join(viewer.COLUMNS) + " |\n"
            + "| " + " | ".join(["---"] * len(viewer.COLUMNS)) + " |\n"
            + "| " + " | ".join(cells) + " |\n", encoding="utf-8")

    def independent_project(self):
        project = self.root / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main", str(project)], check=True)
        (project / ".gitignore").write_text("/.factory-state/\n", encoding="utf-8")
        self.write_board(self.project, "Independent task")
        subprocess.run(["git", "-C", str(project), "add", ".gitignore", "docs/BOARD.md"], check=True)
        subprocess.run(["git", "-C", str(project), "-c", "user.name=Fixture",
                        "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture"], check=True)
        self.worktree.is_git_repo = Mock(side_effect=lambda target: target == str(project))
        self.initialize()
        return project

    def independent_status(self, project):
        result = subprocess.run(["git", "-C", str(project), "status", "--porcelain",
                                 "--untracked-files=all"], capture_output=True, text=True, check=True)
        return result.stdout

    def initialize(self, *args):
        server = Mock()
        with patch.object(viewer, "load_helpers", return_value=(self.board, self.worktree)), \
                patch.object(viewer, "repo_root", return_value=str(self.root)), \
                patch.object(self.board, "initialize_board", return_value=str(self.factory)), \
                patch.object(viewer, "ThreadingHTTPServer", return_value=server), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(viewer.main(list(args)), 0)
        server.serve_forever.assert_called_once_with()
        server.server_close.assert_called_once_with()

    def request(self, path):
        code, body = self.response(path)
        self.assertEqual(code, 200)
        return body

    def response(self, path):
        response = Mock()
        handler = SimpleNamespace(
            path=path, state=viewer.Handler.state,
            send_json=lambda code, payload: response(code, json.dumps(payload)),
            send_bytes=lambda code, body, content_type: response(code, body.decode("utf-8")))
        viewer.Handler.do_GET(handler)
        code, body = response.call_args.args
        return code, json.loads(body) if path.startswith("/api/") else body

    def test_all_registered_boards_and_worktrees_keep_their_ids(self):
        self.initialize()
        for name in ("alpha", "beta", "gamma"):
            target = self.root / name
            self.write_board(target / "docs/BOARD.md", name + " task")
            (target / ".git").mkdir()
        self.registry.write_text(json.dumps({"control": ".", "alpha": "alpha",
                                             "beta": "beta", "gamma": "gamma"}))
        self.worktree.is_git_repo = Mock(return_value=True)
        self.worktree.list_worktrees = Mock(side_effect=lambda target: [
            {"path": target, "head": "abc1234", "branch": "main"}])
        self.worktree.default_base = Mock(return_value="main")
        self.worktree.git = Mock(return_value=(1, "", ""))
        labels = [entry["label"] for entry in self.request("/api/board")["boards"]]
        self.assertEqual(labels, ["harness", "alpha", "beta", "gamma"])
        self.assertEqual([entry["repo"] for entry in self.request("/api/worktrees")],
                         ["control", "alpha", "beta", "gamma"])
        page = self.request("/")
        for label in labels:
            self.assertIn('data-wb-scope-tab="%s"' % label, page)

    def test_registered_missing_board_reports_existing_read_error_without_creating_one(self):
        self.initialize()
        target = self.root / "alpha"
        target.mkdir()
        self.registry.write_text(json.dumps({"control": ".", "alpha": "alpha"}))
        entry = self.request("/api/board")["boards"][1]
        self.assertEqual(entry["label"], "alpha")
        self.assertEqual(entry["rows"], [])
        self.assertIn("cannot read", entry["error"])
        self.assertFalse((target / "docs/BOARD.md").exists())

    def test_candidate_scan_is_names_only_and_does_not_follow_symlinks(self):
        self.initialize()
        projects = self.root / "projects"
        projects.mkdir()
        for relative in ("group-one/shared", "group-two/shared", "registered",
                         "group-three/linked", "plain"):
            target = projects / relative
            target.mkdir(parents=True)
            if relative.endswith("linked"):
                (target / ".git").write_text("gitdir: /private/elsewhere")
            else:
                (target / ".git").mkdir()
        (projects / "group-one" / "alias").symlink_to(projects / "group-two/shared", target_is_directory=True)
        (projects / "group-three" / "symlink-marker").mkdir()
        (projects / "group-three" / "symlink-marker" / ".git").symlink_to(
            projects / "plain/.git", target_is_directory=True)
        (projects / "outside").symlink_to(self.root, target_is_directory=True)
        (projects / "registered" / "private").mkdir()
        (projects / "registered" / "private" / ".git").mkdir()
        self.registry.write_text(json.dumps({"control": ".", "registered": str(projects / "registered")}))
        with patch.object(viewer, "PROJECTS_ROOT", str(projects)), \
                patch.object(self.board, "read_table", wraps=self.board.read_table) as board_read, \
                patch.object(self.worktree, "git", side_effect=AssertionError("candidate Git access")):
            payload = self.request("/api/repo-candidates")
        self.assertEqual(set(payload), {"candidates", "scanned_at"})
        self.assertEqual(payload["candidates"], [
            {"name": "shared", "relative_path": "group-one/shared"},
            {"name": "linked", "relative_path": "group-three/linked"},
            {"name": "shared", "relative_path": "group-two/shared"},
            {"name": "plain", "relative_path": "plain"}])
        board_read.assert_not_called()
        self.assertNotIn(str(projects), json.dumps(payload["candidates"]))

    def test_inaccessible_candidate_root_returns_safe_503(self):
        self.initialize()
        with patch.object(viewer, "PROJECTS_ROOT", str(self.root / "missing")), \
                contextlib.redirect_stderr(io.StringIO()) as log:
            code, payload = self.response("/api/repo-candidates")
        self.assertEqual((code, payload), (503, {"error": "Repository candidates unavailable."}))
        self.assertNotIn(str(self.root), log.getvalue())

    def test_independent_registered_board_get_never_initializes_sqlite(self):
        project = self.independent_project()
        db = Path(self.board.database_path(str(project)))

        self.assertFalse(db.exists())
        self.assertEqual(self.independent_status(project), "")
        with patch.object(self.board, "read_table", wraps=self.board.read_table) as read_table:
            entry = self.request("/api/board")["boards"][1]
            self.assertIn("Board not initialized", self.request("/"))
        self.assertEqual(entry["label"], "project")
        self.assertEqual(entry["rows"], [])
        self.assertEqual(entry["error"], "Board not initialized")
        self.assertEqual(read_table.call_count, 2)
        self.assertTrue(all(call.args[0] == str(self.factory) for call in read_table.call_args_list))
        self.assertEqual(list(db.parent.glob(db.name + "*")), [])
        self.assertEqual(self.independent_status(project), "")

        self.board.initialize_board(str(project))
        before = db.read_bytes()
        sidecars = sorted(path.name for path in db.parent.glob(db.name + "*"))
        entry = self.request("/api/board")["boards"][1]
        self.assertEqual([row["Task"] for row in entry["rows"]], ["Independent task"])
        self.assertIsNone(entry["error"])
        self.assertEqual(db.read_bytes(), before)
        self.assertEqual(sorted(path.name for path in db.parent.glob(db.name + "*")), sidecars)
        self.assertEqual(self.independent_status(project), "")

    def test_active_wal_secondary_board_reads_current_data_without_sidecar_writes(self):
        project = self.independent_project()
        self.board.initialize_board(str(project))
        db = Path(self.board.database_path(str(project)))
        with contextlib.closing(sqlite3.connect(str(db))) as writer:
            writer.execute("PRAGMA journal_mode=WAL")
            writer.execute("UPDATE board SET markdown=?, revision=revision+1 WHERE id=1",
                           (self.project.read_text().replace("Independent task", "Live WAL task"),))
            writer.commit()
            files = [db, db.with_name(db.name + "-wal"), db.with_name(db.name + "-shm")]
            self.assertTrue(all(path.exists() for path in files))
            sidecar_names = {path.name for path in db.parent.glob(db.name + "*")}
            before = {path.name: path.read_bytes() for path in files[:2]}
            status = self.independent_status(project)
            self.assertEqual(status, "")
            entry = self.request("/api/board")["boards"][1]
            self.assertEqual([row["Task"] for row in entry["rows"]], ["Live WAL task"])
            self.assertIsNone(entry["error"])
            self.assertEqual({path.name: path.read_bytes() for path in files[:2]}, before)
            self.assertEqual({path.name for path in db.parent.glob(db.name + "*")}, sidecar_names)
            self.assertIn("Live WAL task", writer.execute(
                "SELECT markdown FROM board WHERE id = 1").fetchone()[0])
            self.assertEqual(self.independent_status(project), status)

    def test_candidate_mid_scan_failure_and_invalid_registry_are_safe(self):
        self.initialize()
        projects = self.root / "projects"
        (projects / "group").mkdir(parents=True)
        scandir = viewer.os.scandir
        group_inode = (projects / "group").stat().st_ino
        open_dir = viewer.os.open
        close_dir = viewer.os.close
        opened, closed = [], []

        def record_open(*args, **kwargs):
            fd = open_dir(*args, **kwargs)
            opened.append(fd)
            return fd

        def record_close(fd):
            closed.append(fd)
            return close_dir(fd)

        def fail_nested(directory):
            if os.fstat(directory).st_ino == group_inode:
                raise PermissionError("private directory")
            return scandir(directory)

        with patch.object(viewer, "PROJECTS_ROOT", str(projects)), \
                patch.object(viewer.os, "scandir", side_effect=fail_nested), \
                patch.object(viewer.os, "open", side_effect=record_open), \
                patch.object(viewer.os, "close", side_effect=record_close), \
                contextlib.redirect_stderr(io.StringIO()) as log:
            code, payload = self.response("/api/repo-candidates")
        self.assertEqual((code, payload), (503, {"error": "Repository candidates unavailable."}))
        self.assertNotIn(str(projects), log.getvalue())
        self.assertEqual(sorted(opened), sorted(closed))

        self.registry.write_text(json.dumps({"control": ".", "invalid": "../outside"}))
        with patch.object(viewer, "PROJECTS_ROOT", str(projects)), \
                contextlib.redirect_stderr(io.StringIO()) as log:
            code, payload = self.response("/api/repo-candidates")
        self.assertEqual((code, payload), (503, {"error": "Repository candidates unavailable."}))
        self.assertNotIn(str(self.root), log.getvalue())

    def test_candidate_swapped_to_symlink_before_open_stays_outside(self):
        self.initialize()
        projects = self.root / "projects"
        projects.mkdir()
        swapped = projects / "swapped"
        swapped.mkdir()
        outside = self.root / "outside"
        outside.mkdir()
        (outside / ".git").mkdir()
        (outside / "private").mkdir()
        (outside / "private" / ".git").mkdir()
        safe = projects / "safe"
        safe.mkdir()
        (safe / ".git").mkdir()
        real_open = viewer.os.open
        root_inode = projects.stat().st_ino
        changed = []

        def replace_before_open(path, flags, **kwargs):
            if (path == "swapped" and "dir_fd" in kwargs
                    and os.fstat(kwargs["dir_fd"]).st_ino == root_inode and not changed):
                swapped.rmdir()
                swapped.symlink_to(outside, target_is_directory=True)
                changed.append(True)
            return real_open(path, flags, **kwargs)

        with patch.object(viewer, "PROJECTS_ROOT", str(projects)), \
                patch.object(viewer.os, "open", side_effect=replace_before_open):
            candidates = self.request("/api/repo-candidates")["candidates"]
        self.assertTrue(changed)
        self.assertEqual(candidates, [{"name": "safe", "relative_path": "safe"}])
        self.assertNotIn("outside", json.dumps(candidates))
        self.assertNotIn("private", json.dumps(candidates))

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
        page = self.request("/")
        self.assertNotIn("Project task", page)
        self.assertIn('data-wb-scope-tab="board"', page)

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
        self.assertIn('class="wb-live" data-ms="', page)
        self.assertIn('class="wb-live-text">updated ', page)
        self.assertIn('liveText.textContent = "updated " + time', page)
        self.assertIn('var stale = paused || age > refreshSeconds * 1500;', page)

    def test_refresh_override(self):
        self.initialize("--refresh", "17")
        self.assertEqual(viewer.Handler.state["refresh"], 17)
        self.assertIn('data-refresh="17"', self.request("/"))

    def test_requests_never_recreate_missing_fixture(self):
        self.initialize()
        self.factory.unlink()
        entries = self.request("/api/board")["boards"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["path"], str(self.factory))
        self.assertEqual(entries[0]["rows"], [])
        self.assertIn("cannot read", entries[0]["error"])
        self.request("/")
        self.assertFalse(self.factory.exists())
        self.assertFalse(self.project.exists())

    def test_startup_preserves_malformed_and_explicit_missing_board(self):
        self.factory.write_bytes(b"malformed\r\nunchanged")
        self.initialize()
        entry = self.request("/api/board")["boards"][0]
        self.assertIn("no board table", entry["error"])
        self.assertEqual(self.factory.read_bytes(), b"malformed\r\nunchanged")
        missing = self.root / "explicit.md"
        self.initialize("--file", str(missing))
        self.assertIn("cannot read", self.request("/api/board")["boards"][0]["error"])
        self.assertFalse(missing.exists())

    def test_viewer_refuses_symlink_before_binding(self):
        self.factory.unlink()
        self.factory.symlink_to(self.root / "outside.md")
        with patch.object(viewer, "load_helpers", return_value=(self.board, self.worktree)), \
                patch.object(viewer, "repo_root", return_value=str(self.root)), \
                patch.object(self.board, "initialize_board", side_effect=OSError("non-regular board")), \
                patch.object(viewer, "ThreadingHTTPServer") as server, \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(viewer.main([]), 1)
        server.assert_not_called()
        self.assertFalse((self.root / "outside.md").exists())

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
        self.write_board(project / "docs/BOARD.md", "Project task")
        page = self.request("/")
        self.assertEqual(page.count('2 worktrees</span>'), 2)
        self.assertEqual(page.count('class="wb-wt"'), 4)
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
                page = self.request("/")
                self.assertIn('2 worktrees</span>', page)
                self.assertNotIn('data-wb-scope-tab="project"', page)
                self.assertEqual(page.count('class="wb-wt"'), 2)

    def test_main_uses_real_scoped_data_and_shared_workbench(self):
        self.write_board(self.project, "Actual project task")
        self.initialize()
        with patch.object(viewer, "gallery_scope_fixtures", side_effect=AssertionError("fixture on main")):
            page = self.request("/")
        self.assertIn('<main class="wb-workbench">', page)
        self.assertNotIn('class="wb-layout"', page)
        self.assertNotIn('class="wb-sidebar"', page)
        self.assertNotIn('class="wb-kpi"', page)
        self.assertNotIn("labelled fixture data", page)
        self.assertNotIn("Empty and unavailable states", page)
        self.assertNotIn("/fixtures/", page)
        self.assertIn('href="/gallery"', page)
        tags = []
        parser = HTMLParser()
        parser.handle_starttag = lambda tag, attrs: tags.append((tag, dict(attrs)))
        parser.feed(page)
        ids = [attrs["id"] for _, attrs in tags if "id" in attrs]
        self.assertEqual(len(ids), len(set(ids)))
        tabs = [attrs for _, attrs in tags if attrs.get("role") == "tab"]
        panels = [attrs for _, attrs in tags if attrs.get("role") == "tabpanel"]
        self.assertEqual([tab["data-wb-scope-tab"] for tab in tabs], ["harness", "project"])
        for tab, panel in zip(tabs, panels):
            active = tab["data-wb-scope-tab"] == "project"
            self.assertEqual(tab["aria-controls"], panel["id"])
            self.assertEqual(panel["aria-labelledby"], tab["id"])
            self.assertEqual(tab["aria-selected"], "true" if active else "false")
            self.assertEqual("hidden" in panel, not active)
        cards = [attrs for _, attrs in tags if "data-card" in attrs]
        self.assertEqual([(card["data-board"], card["data-card"]) for card in cards],
                         [("harness", "BOARD-001"), ("project", "BOARD-001")])
        self.assertIn('getAttribute("data-board") + "::"', page)
        self.assertIn('class="notes"', page)
        self.assertIn('class="wb-card-task"', page)
        self.assertIn('class="wb-rail"', page)
        self.assertIn('id="main-type-filter"', page)
        self.assertIn('id="main-priority-filter"', page)
        self.assertIn('params.get("status")', page)
        self.assertIn('event.key === "j" || event.key === "k"', page)
        self.assertIn("labelled fixture data", self.request("/gallery"))

    def test_explicit_board_worktrees_follow_root_paths_not_label_guesses(self):
        self.initialize("--file", str(self.factory))
        worktrees = [
            {"main": True, "branch": "control-base", "path": str(self.root),
             "repo": "control", "base": "opencode", "ahead": 0, "behind": 0, "dirty": False},
            {"main": True, "branch": "project-base", "path": str(self.root / "project"),
             "repo": "project", "base": "main", "ahead": 0, "behind": 0, "dirty": False},
        ]
        with patch.object(viewer, "worktree_state", return_value=worktrees):
            page = self.request("/")
        self.assertIn("control-base", page)
        self.assertNotIn("project-base", page)
        self.write_board(self.project, "Explicit project task")
        self.initialize("--file", str(self.project))
        with patch.object(viewer, "worktree_state", return_value=worktrees):
            page = self.request("/")
        self.assertIn("project-base", page)
        self.assertNotIn("control-base", page)
        entry = viewer.board_states(self.board, [("board", str(self.root / "project-other/BOARD.md"))])[0]
        page = viewer.wb_scope_content(entry, worktrees, "board", root=str(self.root))
        self.assertIn("control-base", page)
        self.assertNotIn("project-base", page)
        entry = dict(entry, path="/unrelated/BOARD.md")
        page = viewer.wb_scope_content(entry, worktrees, "board", root=str(self.root))
        self.assertNotIn("control-base", page)
        self.assertNotIn("project-base", page)

    def test_main_counts_empty_fallback_and_hostile_paths(self):
        self.write_board(self.project, "Actual project task")
        self.initialize()
        entries = self.request("/api/board")["boards"]
        entries[1]["rows"][0]["Status"] = "Blocked"
        entries[1]["counts"] = {"Blocked": 1}
        entries[1]["path"] = '/project/<script>alert("board")</script>/BOARD.md'
        worktrees = [
            {"main": False, "branch": '<script>alert("branch")</script>',
             "path": '/project/" onmouseover="bad', "repo": "project",
             "base": '<img src=x onerror="bad">', "ahead": None, "behind": None, "dirty": True},
            {"main": False, "branch": "harness-only-branch", "path": "/harness/tree",
             "repo": "control", "base": "opencode", "ahead": 2, "behind": 1, "dirty": False},
        ]
        page = viewer.build_html(entries, worktrees, "2026-11-11T12:00:00+00:00", None, 60)
        harness, project = page.split('data-wb-scope-panel="harness"', 1)[1].split(
            'data-wb-scope-panel="project"', 1)
        self.assertIn("Factory task", harness)
        self.assertNotIn("Actual project task", harness)
        self.assertIn("0 pending merge · 0 blocked · 1 tasks total", harness)
        self.assertIn("harness-only-branch", harness)
        self.assertIn("Actual project task", project)
        self.assertNotIn("Factory task", project)
        self.assertNotIn("harness-only-branch", project)
        self.assertIn("0 pending merge · 1 blocked · 1 tasks total", project)
        self.assertIn('data-status-filter="Blocked" aria-pressed="false" data-peak="true"', project)
        self.assertIn('&lt;script&gt;alert(&quot;branch&quot;)&lt;/script&gt;', project)
        self.assertNotIn('<script>alert', page)
        self.assertNotIn('<img src=x', page)
        self.assertNotIn('" onmouseover="bad', page)
        entries[0] = dict(entries[0], rows=[], counts={})
        page = viewer.build_html(entries[:1], [], "2026-11-11T12:00:00+00:00", None, 60)
        self.assertIn('data-wb-scope-tab="harness">Harness <span>0 tasks', page)
        self.assertIn('aria-selected="true" tabindex="0"', page)
        self.assertNotIn('data-wb-scope-panel="project"', page)
        self.assertIn("No harness worktrees.", page)
        self.assertIn("Nothing ready. Add a row with board.py add.", page)
        empty = viewer.build_html([], [], "invalid-time", "Cannot read <board>", 60)
        self.assertIn("No board file found.", empty)
        self.assertIn('role="alert">Cannot read &lt;board&gt;', empty)
        self.assertIn('data-ms="0"', empty)

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


class BoardBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="board-bootstrap-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.board = viewer.load_module("bootstrap_board", Path(__file__).with_name("board.py"))
        self.worktree = viewer.load_module(
            "bootstrap_worktree", Path(__file__).parents[2] / "git-worktree/scripts/worktree.py")

    def git(self, root, *args):
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def repository(self, root):
        root.mkdir(parents=True, exist_ok=True)
        self.git(root, "init", "-b", "main")
        marker = root / ".opencode/repos.json"
        marker.parent.mkdir(exist_ok=True)
        marker.write_text('{"control":"."}\n')
        (root / ".gitignore").write_text("/.opencode/worktrees/\n/.factory-state/\n")
        self.git(root, "add", ".opencode/repos.json", ".gitignore")
        self.git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "-m", "fixture")

    def test_pre_merge_check_imports_missing_db_and_preserves_legacy_bytes(self):
        main = self.root / "main"
        self.repository(main)
        legacy = main / "docs/BOARD.md"
        legacy.parent.mkdir()
        source = (b"| ID | Task | Type | Status | Priority | Risk | Blocked by | Repos | Branch/Worktree | Notes |\r\n"
                  b"|---|---|---|---|---|---|---|---|---|---|\r\n"
                  b"| BOARD-001 | old | Fix | Ready | P2 | low | None. | control | - | note |\r\n")
        legacy.write_bytes(source)
        db = Path(self.board.database_path(str(main)))
        self.assertFalse(db.exists())
        script = str(Path(__file__).with_name("board.py").resolve())
        result = subprocess.run([sys.executable, script, "pre-merge-check"], cwd=main,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(db.exists())
        self.assertEqual(legacy.read_bytes(), source)
        self.assertEqual(db.with_name(self.board.LEGACY_BACKUP_NAME).read_bytes(), source)
        self.assertIn(str(db.with_name(self.board.LEGACY_BACKUP_NAME)), result.stdout)
        self.assertEqual(db.with_name(self.board.EXPORT_NAME).read_bytes(), source)
        self.assertIn(str(db.with_name(self.board.EXPORT_NAME)), result.stdout)
        with self.board.connect(str(db)) as connection:
            self.assertEqual(connection.execute("SELECT source_bytes FROM board").fetchone()[0], source)

        legacy.write_bytes(source.replace(b"old", b"new"))
        result = subprocess.run([sys.executable, script, "pre-merge-check"], cwd=main,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("differs from its SQLite import", result.stderr)
        self.assertEqual(db.with_name(self.board.LEGACY_BACKUP_NAME).read_bytes(), source)

    def test_pre_merge_check_missing_legacy_refuses_without_creating_empty_db(self):
        main = self.root / "main"
        self.repository(main)
        script = str(Path(__file__).with_name("board.py").resolve())
        result = subprocess.run([sys.executable, script, "pre-merge-check"], cwd=main,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("pre-merge check refused", result.stderr)
        self.assertFalse(Path(self.board.database_path(str(main))).exists())

    def test_legacy_runtime_state_blocks_board_bootstrap_before_empty_database(self):
        main = self.root / "main"
        self.repository(main)
        legacy_database = main / ".git/factory-board.sqlite3"
        with sqlite3.connect(legacy_database) as connection:
            connection.execute("CREATE TABLE legacy_state (value TEXT)")
        script = str(Path(__file__).with_name("board.py").resolve())
        result = subprocess.run([sys.executable, script, "show"], cwd=main,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, self.board.REFUSED)
        self.assertIn("run .opencode/skills/runtime-state/scripts/state.py migrate first",
                      result.stderr)
        self.assertFalse((main / ".factory-state").exists())

    def test_unverified_target_database_does_not_bypass_board_command_guard(self):
        main = self.root / "main"
        self.repository(main)
        with sqlite3.connect(main / ".git/factory-board.sqlite3") as connection:
            connection.execute("CREATE TABLE legacy_state (value TEXT)")
        target = main / ".factory-state/factory-board.sqlite3"
        target.parent.mkdir()
        target.write_bytes(b"unverified target")
        script = str(Path(__file__).with_name("board.py").resolve())
        result = subprocess.run([sys.executable, script, "show"], cwd=main,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, self.board.REFUSED)
        self.assertIn("complete verified destination", result.stderr)
        self.assertEqual(target.read_bytes(), b"unverified target")

    def test_clean_clone_board_command_initializes_normally(self):
        main = self.root / "fresh"
        self.repository(main)
        script = str(Path(__file__).with_name("board.py").resolve())
        result = subprocess.run([sys.executable, script, "show"], cwd=main,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((main / ".factory-state/factory-board.sqlite3").is_file())

    def test_import_once_preserves_source_bytes_and_main_status(self):
        main = self.root / "main"
        self.repository(main)
        legacy = main / "docs/BOARD.md"
        legacy.parent.mkdir()
        legacy.write_bytes(b"| ID | Task | Type | Status | Priority | Risk | Blocked by | Repos | Branch/Worktree | Notes |\r\n"
                           b"|---|---|---|---|---|---|---|---|---|---|\r\n"
                           b"| BOARD-001 | old | Fix | Ready | P2 | low | None. | control | - | note |\r\n")
        self.git(main, "add", "docs/BOARD.md")
        self.git(main, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "-m", "legacy")
        before = legacy.read_bytes()
        self.board.initialize_board(str(main))
        self.assertEqual(self.git(main, "status", "--porcelain"), "")
        legacy.write_text("invalid later change", encoding="utf-8")
        table, error = self.board.read_table(str(legacy))
        self.assertIsNone(error)
        self.assertEqual(self.board.cell_texts(table["lines"], table["rows"][0])[1], "old")
        self.assertEqual(legacy.read_text(), "invalid later change")
        import sqlite3
        with sqlite3.connect(self.board.database_path(str(main))) as connection:
            self.assertEqual(connection.execute("SELECT source_bytes FROM board").fetchone()[0], before)

    def test_worktree_cli_uses_common_database_and_export_without_markdown_writes(self):
        main = self.root / "main"
        self.repository(main)
        linked = main / ".opencode/worktrees/task"
        self.git(main, "worktree", "add", "-b", "feat/task", str(linked))
        script = str(Path(__file__).with_name("board.py").resolve())
        self.assertEqual(self.board.control_root(str(linked)), str(main))
        self.assertEqual(self.board.database_path(str(main)), self.board.database_path(str(linked)))
        add = subprocess.run([sys.executable, script, "add", "--id", "BOARD-001", "--task", "task",
                              "--type", "Feature", "--status", "Ready", "--priority", "P2",
                              "--risk", "low"], cwd=linked, capture_output=True)
        self.assertEqual(add.returncode, 0, add.stderr)
        self.assertFalse((main / "docs/BOARD.md").exists())
        self.assertFalse((linked / "docs/BOARD.md").exists())
        self.assertEqual(self.git(main, "status", "--porcelain"), "")
        output = subprocess.run([sys.executable, script, "export"], cwd=linked, capture_output=True)
        self.assertEqual(output.returncode, 0, output.stderr)
        export = Path(output.stdout.decode().strip())
        self.assertEqual(export.parent, main / ".factory-state")
        self.assertIn("BOARD-001", export.read_text())
        self.assertEqual(self.git(main, "status", "--porcelain"), "")

    def test_concurrent_different_rows_and_conflicting_cell(self):
        main = self.root / "main"
        self.repository(main)
        path = self.board.initialize_board(str(main))
        for number in range(2):
            table, _ = self.board.read_table(path)
            at = table["rows"][-1] + 1 if table["rows"] else table["header"] + 2
            self.board.write_atomic(path, table["lines"][:at]
                                    + ["| BOARD-00%d | task | Fix | Ready | P2 | low | None. | control | - | - |" % (number + 1)]
                                    + table["lines"][at:])

        def update(number, status="In Progress"):
            table, error = self.board.read_table(path)
            self.assertIsNone(error)
            i = self.board.row_by_id(table, "BOARD-00%d" % number)
            lines = list(table["lines"])
            lines[i] = self.board.replace_cell(lines[i], 3, status)
            self.board.write_atomic(path, lines)

        with ThreadPoolExecutor(2) as pool:
            list(pool.map(update, [1, 2]))
        table, _ = self.board.read_table(path)
        self.assertEqual([self.board.cell_texts(table["lines"], i)[3] for i in table["rows"]],
                         ["In Progress", "In Progress"])
        stale, _ = self.board.read_table(path)
        stale_lines = list(stale["lines"])
        stale_lines[stale["rows"][0]] = self.board.replace_cell(stale_lines[stale["rows"][0]], 3, "Blocked")
        with ThreadPoolExecutor(1) as pool:
            pool.submit(update, 1, "Pending Merge").result()
        with self.assertRaisesRegex(ValueError, "changed concurrently"):
            self.board.write_atomic(path, stale_lines)

    def test_explicit_fixture_is_read_only(self):
        main = self.root / "main"
        self.repository(main)
        script = str(Path(__file__).with_name("board.py").resolve())
        fixture = main / "fixture.md"
        fixture.write_text(self.board.empty_board())
        result = subprocess.run([sys.executable, script, "--file", str(fixture), "set-status",
                                 "BOARD-001", "Ready"], cwd=main, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(fixture.read_text(), self.board.empty_board())


class GalleryTests(unittest.TestCase):
    def test_scope_default_and_missing_selection_fallback(self):
        harness = {"label": "harness"}
        project = {"label": "project"}
        for boards, selected, expected in (
                ([harness, project], None, "project"),
                ([harness, project], "harness", "harness"),
                ([harness, project], "removed", "project"),
                ([harness], "project", "harness"),
                ([project], "harness", "project"),
                ([], "project", None)):
            with self.subTest(boards=boards, selected=selected):
                self.assertEqual(viewer.wb_scope_default(boards, selected), expected)

    def test_gallery_semantics_and_duplicate_task_scope(self):
        page = viewer.build_gallery_html()
        tags = []
        parser = HTMLParser()
        parser.handle_starttag = lambda tag, attrs: tags.append((tag, dict(attrs)))
        parser.feed(page)
        ids = [attrs["id"] for _, attrs in tags if "id" in attrs]
        self.assertEqual(len(ids), len(set(ids)))
        tabs = [attrs for _, attrs in tags if attrs.get("role") == "tab"]
        panels = [attrs for _, attrs in tags if attrs.get("role") == "tabpanel"]
        self.assertEqual(len(tabs), 2)
        self.assertEqual(len(panels), 2)
        for tab, panel in zip(tabs, panels):
            self.assertEqual(tab["aria-controls"], panel["id"])
            self.assertEqual(panel["aria-labelledby"], tab["id"])
            active = tab["data-wb-scope-tab"] == "project"
            self.assertEqual(tab["aria-selected"], "true" if active else "false")
            self.assertEqual(tab["tabindex"], "0" if active else "-1")
            self.assertEqual("hidden" in panel, not active)
        cards = [attrs for _, attrs in tags if "data-card" in attrs]
        self.assertEqual([(card["data-board"], card["data-card"]) for card in cards],
                         [("project", "BOARD-001"), ("project", "BOARD-002"),
                          ("harness", "BOARD-001")])
        self.assertIn("labelled fixture data", page)
        self.assertIn('data-refresh="60"', page)
        self.assertIn('id="refresh">Refresh now</button>', page)
        self.assertIn('id="pause" aria-pressed="false">Pause</button>', page)
        self.assertIn('id="theme-toggle"', page)
        self.assertIn('id="density-toggle"', page)

    def test_scope_content_counts_and_repository_worktrees(self):
        boards, worktrees = viewer.gallery_scope_fixtures()
        for entry, task_count, wt_count, base in (
                (boards[0], 2, 1, "main"), (boards[1], 1, 2, "opencode")):
            with self.subTest(scope=entry["label"]):
                page = viewer.wb_scope_content(entry, worktrees, "project")
                self.assertIn('<strong>%d</strong> in flight' % task_count, page)
                self.assertIn('%d tasks total' % task_count, page)
                self.assertIn('%d worktrees</span>' % wt_count, page)
                self.assertIn('Base: %s' % base, page)
                self.assertEqual(page.count('class="wb-wt"'), wt_count)
                self.assertEqual(page.count('data-card='), task_count)
                other = "harness" if entry["label"] == "project" else "project"
                self.assertNotIn('data-board="%s"' % other, page)
                if entry["label"] == "project":
                    self.assertIn("ahead +7 · behind −2", page)
                    self.assertIn('wb-chip--dirty', page)
                    self.assertNotIn('feat/rebuild-factory-pages-as-a-split', page)
                    self.assertIn("0 pending merge · 1 blocked", page)
                else:
                    self.assertNotIn('feat/project-search', page)
                    self.assertIn("0 pending merge · 0 blocked", page)
        self.assertEqual(viewer.active_counts([boards[0]])["Blocked"], 1)
        self.assertEqual(viewer.active_counts([boards[1]])["Blocked"], 0)

    def test_empty_error_escaping_and_worktree_compatibility(self):
        entry = {"label": "project", "path": "/fixture/docs/BOARD.md", "rows": [],
                 "counts": {}, "error": "Cannot read <board>; check the path"}
        page = viewer.wb_scope_content(entry, [], "project")
        self.assertIn("0 tasks total", page)
        self.assertIn("No project worktrees.", page)
        self.assertIn('role="alert">Cannot read &lt;board&gt;; check the path', page)
        self.assertIn("Nothing ready. Add a row with board.py add.", page)
        _, worktrees = viewer.gallery_scope_fixtures()
        wt = dict(worktrees[0], base='<script>bad</script>', ahead=None, behind=None)
        self.assertNotIn("Base:", viewer.wb_wt_row(wt))
        self.assertIn("Base: &lt;script&gt;bad&lt;/script&gt;", viewer.wb_wt_row(wt, show_base=True))
        self.assertIn("ahead +? · behind −?", viewer.wb_wt_row(wt, show_base=True))

    def test_workbench_uses_populated_lanes_and_preserves_live_defaults(self):
        boards, worktrees = viewer.gallery_scope_fixtures()
        entry = boards[0]
        page = viewer.wb_scope_content(entry, worktrees, "project")
        tags = []
        parser = HTMLParser()
        parser.handle_starttag = lambda tag, attrs: tags.append((tag, dict(attrs)))
        parser.feed(page)
        lane_groups = [attrs for tag, attrs in tags
                       if tag == "details" and "data-card" not in attrs]
        self.assertEqual([attrs["data-lane"] for attrs in lane_groups], ["In Review", "Blocked"])
        for lane in ("Ready", "In Progress", "Pending Merge", "Backlog", "Merged", "Dropped"):
            self.assertNotIn('data-lane="%s"' % lane, page)
        self.assertIn('data-status-filter="Ready"', page)
        self.assertIn('data-status-filter="Pending Merge"', page)
        self.assertNotIn('wb-meter-track', page.split('data-board-panel=')[1])
        live_panel = viewer.render_board_panel(entry)
        for lane in viewer.LANE_ORDER:
            self.assertIn('data-lane="%s"' % lane, live_panel)
        self.assertIn('class="wb-card-task"', page)
        self.assertIn('class="wb-card-detail"', page)
        self.assertIn('class="notes"', page)
        self.assertIn('class="wb-rail"', page)

    def test_shared_handlers_and_workbench_layout_contract(self):
        page = viewer.build_gallery_html()
        for key in ("ArrowLeft", "ArrowRight", "Home", "End"):
            self.assertIn("event.key === '%s'" % key, page)
        for contract in ("if (saved.scope) { state.scope = saved.scope; }",
                         "item.tabIndex = active ? 0 : -1;",
                         "if (focus) { tab.focus(); }",
                         "selectScope(state.scope, false);",
                         "return !panel || !panel.hidden;",
                         'refreshBtn.addEventListener("click", function () { window.location.reload(); });'):
            self.assertIn(contract, page)
        live = viewer.build_html([], [], "2026-11-11T12:00:00+00:00", None, 60)
        self.assertIn('class="wb-workbench"', live)
        self.assertNotIn('<div class="wb-layout">', live)
        self.assertNotIn('role="tablist"', live)
        self.assertNotIn('data-wb-scope-panel="', live)
        css = (Path(__file__).parents[1] / "static/board.css").read_text(encoding="utf-8")
        self.assertIn('.wb-workbench .wb-card > summary', css)
        self.assertIn('.wb-workbench .wb-card-id', css)
        self.assertIn(':root[data-theme="dark"]', css)
        self.assertIn(':root[data-theme="light"]', css)


class PlannedWorkApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="planned-work-api-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.factory = self.root / "docs" / "BOARD.md"
        self.project = self.root / "project"
        self.registry = self.root / ".opencode" / "repos.json"
        self.registry.parent.mkdir()
        self.registry.write_text(json.dumps({"control": "."}), encoding="utf-8")
        self.factory.parent.mkdir()
        self.factory.write_text(self.legacy_markdown(), encoding="utf-8")
        (self.root / ".gitignore").write_text("/.factory-state/\n/project/\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "add", ".gitignore",
                        ".opencode/repos.json", "docs/BOARD.md"], check=True)
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=Fixture",
                        "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture"],
                       check=True)
        self.board = viewer.load_module(
            "planned_work_board_fixture", Path(__file__).with_name("board.py"))
        self.db = self.root / ".factory-state" / "factory-board.sqlite3"
        original_database_path = self.board.database_path
        self.board.database_path = lambda root: (
            str(self.db) if os.path.realpath(root) == os.path.realpath(self.root)
            else original_database_path(root))
        self.worktree = viewer.load_module(
            "planned_work_helpers_fixture", Path(__file__).parents[2] / "git-worktree/scripts/worktree.py")
        self.worktree.list_worktrees = Mock(return_value=[])
        self.worktree.is_git_repo = Mock(return_value=False)
        previous_state = viewer.Handler.state
        self.addCleanup(setattr, viewer.Handler, "state", previous_state)

    @staticmethod
    def legacy_markdown():
        rows = [
            ["BOARD-001", "Legacy active", "Feature", "Ready", "P2", "🟢 low",
             "- None.", "control", "-", "- [x] Imported criterion; Proof: imported evidence"],
            ["BOARD-002", "Legacy completed", "Fix", "Merged", "P3", "🟡 medium",
             "- None.", "control", "-", "Legacy completed note"],
        ]
        header = "| " + " | ".join(viewer.COLUMNS) + " |\n"
        separator = "| " + " | ".join(["---"] * len(viewer.COLUMNS)) + " |\n"
        return header + separator + "".join(
            "| " + " | ".join(cells) + " |\n" for cells in rows)

    def setup_normalized(self):
        self.board.initialize_board(str(self.root))
        self.board.migrate_normalized(str(self.db), apply=True)
        drafts = []
        for key, task in (("queue-a", "Queue A"), ("queue-b", "Queue B"),
                          ("active", "Promoted active"), ("complete", "Completed history"),
                          ("cancel", "Cancelled history")):
            dependencies = ["queue-a"] if key == "queue-b" else []
            drafts.append({
                "key": key,
                "task": task,
                "type": "Feature",
                "priority": "P2",
                "risk": "🟢 low — fixture",
                "user_story": "As a fixture user, I can inspect " + task.lower() + ".",
                "acceptance_criteria": [task + " criterion one", task + " criterion two"],
                "blocked_by": dependencies,
                "repos": ["control"],
                "notes": task + " notes",
            })
        accepted = self.board.accept_plan_batch(str(self.db), drafts)
        ids = {entry["key"]: entry["id"] for entry in accepted}
        self.board.transition_plan_item(str(self.db), ids["active"], "promote")
        self.board.transition_plan_item(str(self.db), ids["complete"], "promote")
        self.board.transition_plan_item(str(self.db), ids["complete"], "complete")
        self.board.transition_plan_item(str(self.db), ids["cancel"], "cancel")
        self.ids = ids
        return ids

    def initialize(self, *args):
        server = Mock()
        with patch.object(viewer, "load_helpers", return_value=(self.board, self.worktree)), \
                patch.object(viewer, "repo_root", return_value=str(self.root)), \
                patch.object(self.board, "initialize_board", return_value=str(self.factory)), \
                patch.object(viewer, "ThreadingHTTPServer", return_value=server), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(viewer.main(list(args)), 0)
        server.serve_forever.assert_called_once_with()
        server.server_close.assert_called_once_with()

    def response(self, path):
        response = Mock()
        handler = SimpleNamespace(
            path=path, state=viewer.Handler.state,
            send_json=lambda code, payload: response(code, json.dumps(payload)),
            send_bytes=lambda code, body, content_type: response(code, body.decode("utf-8")))
        viewer.Handler.do_GET(handler)
        code, body = response.call_args.args
        return code, json.loads(body)

    def capture_request(self, path, method):
        class Capture:
            def __init__(capture_self):
                capture_self.path = path
                capture_self.command = method
                capture_self.state = viewer.Handler.state
                capture_self.headers = {}
                capture_self.body = io.BytesIO()
                capture_self.code = None
                capture_self.wfile = capture_self.body

            def send_response(capture_self, code):
                capture_self.code = code

            def send_header(capture_self, key, value):
                capture_self.headers[key] = value

            def end_headers(capture_self):
                pass

            def send_json(capture_self, code, payload):
                return viewer.Handler.send_json(capture_self, code, payload)

            def send_bytes(capture_self, code, body, content_type):
                return viewer.Handler.send_bytes(capture_self, code, body, content_type)

            def do_GET(capture_self):
                return viewer.Handler.do_GET(capture_self)

        handler = Capture()
        if method == "HEAD":
            viewer.Handler.do_HEAD(handler)
        else:
            viewer.Handler.do_GET(handler)
        return handler

    def test_planned_work_and_active_board_read_only_contract(self):
        ids = self.setup_normalized()
        self.initialize()
        writer = sqlite3.connect(str(self.db), isolation_level=None)
        self.addCleanup(writer.close)
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("BEGIN IMMEDIATE")
        writer.execute("UPDATE board SET revision=revision+1 WHERE id=1")
        writer.commit()
        wal = Path(str(self.db) + "-wal")
        shm = Path(str(self.db) + "-shm")
        self.assertTrue(wal.exists() and shm.exists())
        database_before = self.db.read_bytes()
        wal_before = wal.read_bytes()
        sidecars_before = sorted(path.name for path in self.db.parent.glob(self.db.name + "*"))
        tracked_before = {path: path.read_bytes() for path in
                          (self.root / ".gitignore", self.registry, self.factory)}
        status_before = subprocess.run(
            ["git", "-C", str(self.root), "status", "--porcelain", "--untracked-files=all"],
            capture_output=True, text=True, check=True).stdout

        with patch.object(self.board, "connect", side_effect=AssertionError("write-capable board connect")), \
                patch.object(self.board, "initialize_board",
                             side_effect=AssertionError("HTTP initialized board")):
            code, planned = self.response("/api/planned-work")
            self.assertEqual(code, 200)
            code, board = self.response("/api/board")
            self.assertEqual(code, 200)

        self.assertEqual([item["ID"] for item in planned["queue"]],
                         [ids["queue-a"], ids["queue-b"]])
        self.assertEqual([item["queue_position"] for item in planned["queue"]], [0, 1])
        self.assertEqual(planned["queue"][1]["Blocked by"], ids["queue-a"])
        self.assertEqual([item["ID"] for item in planned["history"]],
                         ["BOARD-002", ids["complete"], ids["cancel"]])
        self.assertEqual([item["terminal_outcome"] for item in planned["history"]],
                         ["completed", "completed", "cancelled"])
        all_planned_ids = {item["ID"] for item in planned["queue"] + planned["history"]}
        self.assertNotIn(ids["active"], all_planned_ids)
        self.assertEqual(planned["history"][0]["user_story"], None)
        self.assertEqual(planned["history"][0]["Notes"], "Legacy completed note")
        self.assertEqual(planned["queue"][0]["user_story"],
                         "As a fixture user, I can inspect queue a.")
        self.assertEqual(planned["queue"][0]["acceptance_criteria"][0], {
            "position": 0, "text": "Queue A criterion one", "verified": False, "proof": None})
        active = board["boards"][0]["rows"]
        self.assertEqual({row["ID"] for row in active}, {"BOARD-001", ids["active"]})
        self.assertEqual(set(active[0]), set(viewer.COLUMNS) | {
            "Notes raw", "user_story", "acceptance_criteria"})
        legacy = next(row for row in active if row["ID"] == "BOARD-001")
        self.assertIsNone(legacy["user_story"])
        self.assertEqual(legacy["Notes raw"],
                         "- [x] Imported criterion; Proof: imported evidence")
        self.assertEqual(legacy["acceptance_criteria"][0]["proof"], "imported evidence")
        self.assertIn("generated_at", planned)
        self.assertEqual(self.db.read_bytes(), database_before)
        self.assertEqual(wal.read_bytes(), wal_before)
        self.assertEqual(sorted(path.name for path in self.db.parent.glob(self.db.name + "*")),
                         sidecars_before)
        self.assertEqual({path: path.read_bytes() for path in tracked_before}, tracked_before)
        status_after = subprocess.run(
            ["git", "-C", str(self.root), "status", "--porcelain", "--untracked-files=all"],
            capture_output=True, text=True, check=True).stdout
        self.assertEqual(status_after, status_before)

        get = self.capture_request("/api/planned-work", "GET")
        head = self.capture_request("/api/planned-work", "HEAD")
        self.assertEqual(head.code, get.code)
        self.assertEqual(head.headers, get.headers)
        self.assertEqual(head.headers["Cache-Control"], "no-store")
        self.assertEqual(head.headers["Content-Length"], str(len(get.body.getvalue())))
        self.assertEqual(head.body.getvalue(), b"")

    def test_unavailable_or_unmigrated_factory_returns_sanitized_503(self):
        self.initialize()
        missing_db = self.db
        with contextlib.redirect_stderr(io.StringIO()) as log:
            code, payload = self.response("/api/planned-work")
        self.assertEqual((code, payload), (503, {"error": "Planned work unavailable."}))
        self.assertNotIn(str(self.root), log.getvalue())
        self.assertFalse(missing_db.exists())
        get = self.capture_request("/api/planned-work", "GET")
        head = self.capture_request("/api/planned-work", "HEAD")
        self.assertEqual(head.code, get.code)
        self.assertEqual(head.headers, get.headers)
        self.assertEqual(head.headers["Cache-Control"], "no-store")
        self.assertEqual(head.body.getvalue(), b"")

        self.board.initialize_board(str(self.root))
        db = self.db
        before = db.read_bytes()
        sidecars = sorted(path.name for path in db.parent.glob(db.name + "*"))
        with patch.object(self.board, "connect", side_effect=AssertionError("HTTP migrated board")), \
                patch.object(self.board, "initialize_board",
                             side_effect=AssertionError("HTTP initialized board")):
            code, payload = self.response("/api/planned-work")
        self.assertEqual((code, payload), (503, {"error": "Planned work unavailable."}))
        self.assertEqual(db.read_bytes(), before)
        self.assertEqual(sorted(path.name for path in db.parent.glob(db.name + "*")), sidecars)

    def test_planned_work_is_unavailable_for_explicit_markdown_fixture(self):
        self.initialize("--file", str(self.factory))
        code, payload = self.response("/api/planned-work")
        self.assertEqual((code, payload), (503, {"error": "Planned work unavailable."}))

    def test_planned_work_is_unavailable_for_project_control_root(self):
        (self.root / "DOMAIN.md").write_text("Project fixture", encoding="utf-8")
        self.initialize()
        code, payload = self.response("/api/planned-work")
        self.assertEqual((code, payload), (503, {"error": "Planned work unavailable."}))

    def test_registered_project_rows_keep_existing_shape(self):
        self.setup_normalized()
        self.project.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.project)], check=True)
        project_board = self.project / "docs" / "BOARD.md"
        project_board.parent.mkdir()
        project_board.write_text(self.legacy_markdown().replace("Legacy active", "Registered task"),
                                 encoding="utf-8")
        (self.project / ".gitignore").write_text("/.factory-state/\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.project), "add", ".gitignore", "docs/BOARD.md"],
                       check=True)
        subprocess.run(["git", "-C", str(self.project), "-c", "user.name=Fixture",
                        "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture"],
                       check=True)
        self.registry.write_text(json.dumps({"control": ".", "project": "project"}),
                                 encoding="utf-8")
        self.worktree.is_git_repo = Mock(side_effect=lambda root: root == str(self.project))
        self.board.initialize_board(str(self.project))
        self.initialize()
        boards = self.response("/api/board")[1]["boards"]
        registered = boards[1]["rows"][0]
        self.assertEqual(registered["Task"], "Registered task")
        self.assertEqual(set(registered), set(viewer.COLUMNS) | {"Notes raw"})
        code, payload = self.response("/api/planned-work")
        self.assertEqual(code, 200)
        self.assertEqual([item["ID"] for item in payload["queue"]],
                         ["BOARD-003", "BOARD-004"])


if __name__ == "__main__":
    unittest.main()
