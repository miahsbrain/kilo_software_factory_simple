"""Preview tests use independent repositories confined to this task worktree."""
import contextlib
import io
import json
import os
from pathlib import Path
import shlex
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import project_reset as reset
import task_purge as purge
import worktree as wt


ROOT = Path(__file__).resolve().parents[4]
GUARD = Path(__file__).with_name("guard.py")


class ProjectResetTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / ".tmp"
        scratch.mkdir(exist_ok=True)
        self.container = Path(tempfile.mkdtemp(prefix="reset-", dir=scratch))
        self.addCleanup(self.cleanup_fixture)
        self.repo = self.container / "selected"
        self.repo.mkdir()
        result = subprocess.run([sys.executable, str(GUARD), "check-git", "--", "git init"],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertIn(result.returncode, (0, 3), result.stderr)
        self.assertEqual(wt.git(str(self.repo), "init")[0], 0)
        self.board = wt.load_board_module(str(ROOT))
        self.state = self.board.runtime_state_module()
        self.assertEqual(Path(self.state.primary_checkout(str(self.repo))), self.repo)
        self.database = self.repo / ".factory-state" / self.board.DATABASE_NAME
        self.assertEqual(Path(self.state.state_root(str(self.repo))) / self.board.DATABASE_NAME,
                         self.database)
        self.assertIn(ROOT, self.database.parents)
        self.write(".opencode/repos.json", json.dumps({"control": "."}))
        self.write("DOMAIN.md", "project domain")
        self.write("ROADMAP.md", "project plans")
        self.database.parent.mkdir()
        with sqlite3.connect(self.database) as connection:
            self.board.normalized_schema(connection)
            connection.execute("CREATE TABLE board (id INTEGER PRIMARY KEY, markdown TEXT, revision INTEGER)")
            connection.execute("INSERT INTO board VALUES (1, 'fixture projection', 1)")
            connection.execute("INSERT INTO planned_items VALUES "
                               "('BOARD-910','Fixture','Feature','P2','low','None.','control','',NULL,0,NULL,0)")
            connection.execute("INSERT INTO acceptance_criteria VALUES ('BOARD-910',0,'fixture criterion',0,NULL)")
            connection.execute("CREATE TABLE plan_id_sequence (singleton INTEGER PRIMARY KEY, high_water INTEGER)")
            connection.execute("INSERT INTO plan_id_sequence VALUES (1, 999)")

    def cleanup_fixture(self):
        self.assertIn(ROOT, self.container.parents)
        command = "rm -rf -- " + shlex.quote(str(self.container))
        result = subprocess.run([sys.executable, str(GUARD), "check-delete", "--", command],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        shutil.rmtree(self.container)

    def write(self, relative, content):
        path = self.repo / relative
        self.assertIn(self.repo, path.parents)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def inventory(self):
        return reset.preview(SimpleNamespace(repo="control", backup=False), str(self.repo), wt)

    def snapshot(self):
        return {str(path.relative_to(self.repo)): (path.read_bytes(), path.stat().st_mtime_ns)
                for path in self.repo.rglob("*") if path.is_file() and not path.is_symlink()}

    def test_preview_exact_inventory_and_no_writes(self):
        evidence = self.write("artifacts/factory/qa/2026-11-13/BOARD-910/qa.md", "fixture evidence")
        ledger = self.write(".factory-state/reviews/BOARD-910-ledger.md", "fixture ledger")
        export = self.write(".factory-state/factory-board-export.md", "fixture export")
        self.write("apps/api/main.py", "source sentinel")
        self.write("AGENTS.md", "harness sentinel")
        self.write("docs/custom.md", "custom sentinel")
        self.write("docs/changelog/CHANGELOG.md", "engineering sentinel")
        self.write("docs/handover/api.md", "memory sentinel")
        self.write("README.md", "readme sentinel")
        before = self.snapshot()
        inventory = self.inventory()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(inventory["repository_kind"], "project")
        self.assertEqual(inventory["high_water_to_preserve"], 999)
        self.assertEqual({target["template"] for target in inventory["targets"] if "template" in target},
                         set(reset.DOCUMENTS))
        paths = {target["path"] for target in inventory["targets"]}
        self.assertEqual(paths - {str(self.repo / name) for name in reset.DOCUMENTS},
                         {str(self.database), str(evidence.parent), str(ledger), str(export)})
        self.assertFalse((self.database.parent / "clean-slates").exists())

    def test_apply_refuses_before_any_state_access(self):
        with patch.object(reset, "preview", side_effect=AssertionError("must not inspect")), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(reset.command(SimpleNamespace(apply=True), "unusable", wt), wt.REFUSED)

    def test_cli_dispatch_and_required_repo(self):
        output = io.StringIO()
        with patch.object(wt.os, "getcwd", return_value=str(self.repo)), contextlib.redirect_stdout(output):
            self.assertEqual(wt.main(["clean-slate", "--repo", "control", "--backup"]), wt.OK)
        self.assertTrue(json.loads(output.getvalue())["backup_requested"])
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            wt.main(["clean-slate"])
        self.assertEqual(error.exception.code, 2)

    def test_factory_preserves_all_documents(self):
        self.write("templates/project/AGENTS.md", "factory identifier")
        (self.repo / "docs").mkdir()
        self.repo.joinpath("DOMAIN.md").rename(self.repo / "docs/custom-domain.md")
        self.repo.joinpath("ROADMAP.md").rename(self.repo / "docs/custom-roadmap.md")
        self.assertFalse(any(target["kind"] == "replace-document" for target in self.inventory()["targets"]))

    def test_missing_state_is_not_created(self):
        self.database.rename(self.repo / "saved.sqlite3")
        self.database.parent.rename(self.repo / "saved-state")
        before = self.snapshot()
        self.assertIn("runtime state missing; preview never creates it", self.inventory()["blockers"])
        self.assertEqual(before, self.snapshot())

    def test_sidecars_block_without_sqlite_open(self):
        self.write(".factory-state/factory-board.sqlite3-wal", "fixture sidecar")
        before = self.snapshot()
        with patch.object(self.board, "readonly_connection", side_effect=AssertionError("must not open")):
            with patch.object(wt, "load_board_module", return_value=self.board):
                self.assertIn("stop SQLite writers and resolve sidecars before inventory", self.inventory()["blockers"])
        self.assertEqual(before, self.snapshot())

    def test_unknown_evidence_blocks_and_is_not_selected(self):
        unknown = self.write("artifacts/factory/qa/2026-11-13/BOARD-911/qa.md", "unowned evidence")
        inventory = self.inventory()
        self.assertTrue(any("unknown artifact ownership" in reason for reason in inventory["blockers"]))
        self.assertNotIn(str(unknown.parent), {target["path"] for target in inventory["targets"]})

    def test_retained_recovery_copies_disclosed(self):
        backup = self.write(".factory-state/purges/BOARD-910/manifest.json", "historic recovery")
        legacy = self.write(".factory-state/factory-board-legacy-backup.md", "historic board")
        old = self.write(".git/factory-board-export.md", "retained migration source")
        inventory = self.inventory()
        self.assertTrue({str(backup.parents[1]), str(legacy), str(old)}.issubset(set(inventory["retained_paths"])))
        self.assertNotIn(str(legacy), {target["path"] for target in inventory["targets"]})

    def test_active_worktree_blocks_without_inspecting_path(self):
        with sqlite3.connect(self.database) as connection:
            connection.execute("INSERT INTO active_work VALUES ('BOARD-910','In Progress','unavailable-worktree')")
        with patch.object(wt, "list_worktrees", return_value=[{"path": str(self.repo)}, {"path": "unavailable"}]):
            reasons = self.inventory()["blockers"]
        self.assertIn("linked or unresolved worktrees must be resolved separately", reasons)
        self.assertIn("active worktree references must be resolved separately", reasons)

    def test_document_symlink_refused(self):
        (self.repo / "docs").mkdir()
        (self.repo / "docs/STACK.md").symlink_to(self.repo / "DOMAIN.md")
        with self.assertRaisesRegex(ValueError, "symbolic link refused"):
            self.inventory()

    def test_hard_link_refused(self):
        (self.repo / "docs").mkdir()
        os.link(self.repo / "DOMAIN.md", self.repo / "docs/STACK.md")
        with self.assertRaisesRegex(ValueError, "hard-linked target refused"):
            self.inventory()

    def test_nested_git_marker_refused(self):
        self.write("artifacts/factory/qa/2026-11-13/BOARD-910/.git", "nested marker")
        with self.assertRaisesRegex(ValueError, "nested repository refused"):
            self.inventory()

    def test_secret_name_refused_without_content_read(self):
        path = self.repo / "artifacts/factory/qa/2026-11-13/BOARD-910/.env"
        path.parent.mkdir(parents=True)
        path.touch()
        with patch.object(purge, "tree_stamp", side_effect=AssertionError("must not hash evidence")):
            with self.assertRaisesRegex(ValueError, "secret-like target refused"):
                reset.evidence_inventory(self.repo, {"BOARD-910"})

    def test_app_shared_scope_refused(self):
        self.write(".opencode/repos.json", json.dumps({"control": ".."}))
        with self.assertRaisesRegex(ValueError, "traversal mapping"):
            self.inventory()

    def test_foreign_absolute_root_refused(self):
        self.write(".opencode/repos.json", json.dumps({"control": str(self.container)}))
        with self.assertRaisesRegex(ValueError, "outside selected boundary"):
            self.inventory()

    def test_ambiguous_project_kind_refused(self):
        self.write("templates/project/AGENTS.md", "conflicting marker")
        with self.assertRaisesRegex(ValueError, "ambiguous factory/project"):
            self.inventory()

    def test_template_manifest_drift_refused(self):
        bundle = self.container / "bundle"
        shutil.copytree(reset.BUNDLE, bundle)
        (bundle / "DOMAIN.md").write_text("changed fixture template")
        with patch.object(reset, "BUNDLE", bundle), self.assertRaisesRegex(ValueError, "template hash mismatch"):
            self.inventory()

    def test_unknown_template_version_refused(self):
        bundle = self.container / "bundle"
        shutil.copytree(reset.BUNDLE, bundle)
        (bundle / "manifest.json").write_text('{"format":"unknown","files":{}}')
        with patch.object(reset, "BUNDLE", bundle), self.assertRaisesRegex(ValueError, "unrecognized portable template"):
            self.inventory()

    def test_unknown_database_tables_refused(self):
        with sqlite3.connect(self.database) as connection:
            connection.execute("CREATE TABLE application_data (value TEXT)")
        with self.assertRaisesRegex(ValueError, "unrecognized database tables"):
            self.inventory()

    def test_unknown_dependency_and_repository_block(self):
        reasons = reset.validate_rows([("BOARD-910", "foreign", "BOARD-911")], [], {"control"})
        self.assertEqual(len(reasons), 2)


if __name__ == "__main__":
    unittest.main()
