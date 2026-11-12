#!/usr/bin/env python3
"""Normalized board migration tests use only isolated SQLite databases."""
import importlib.util
import io
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import board


class NormalizedBoardMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="board-normalized-")
        self.addCleanup(self.temp.cleanup)
        self.path = str(Path(self.temp.name) / "factory-board.sqlite3")
        self.markdown = self.make_markdown()
        with sqlite3.connect(self.path) as connection:
            connection.execute("CREATE TABLE board (id INTEGER PRIMARY KEY, markdown TEXT NOT NULL, "
                               "source_bytes BLOB, revision INTEGER NOT NULL)")
            connection.execute("INSERT INTO board VALUES (1, ?, NULL, 0)", (self.markdown,))

    @staticmethod
    def make_markdown():
        lines = ["| " + " | ".join(board.COLUMNS) + " |",
                 "|" + "|".join("---" for _ in board.COLUMNS) + "|"]
        rows = [("BOARD-130", "Blocked", "None.", "- [x] Keep blocker; Proof: captured"),
                ("BOARD-131", "Merged", "None.", "historical note")]
        dependencies = {143: "None.", 132: "BOARD-143", 133: "BOARD-132", 134: "None.",
                        135: "BOARD-134", 136: "None.", 137: "BOARD-134,BOARD-135,BOARD-136",
                        138: "None.", 139: "None.", 140: "BOARD-133",
                        141: "BOARD-130,BOARD-133,BOARD-137",
                        142: "BOARD-130,BOARD-132,BOARD-133,BOARD-137,BOARD-141",
                        144: "BOARD-130"}
        for number in (143, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 144):
            rows.append(("BOARD-%03d" % number, "Backlog", dependencies[number],
                         "queue note %d" % number))
        rows.extend([("BOARD-145", "Merged", "None.", "completed note"),
                      ("BOARD-146", "In Progress", "BOARD-145",
                       "- [x] Active criterion; Proof: explicit; - [ ] Secondary criterion; Proof: second"),
                     ("BOARD-147", "Ready", "BOARD-146", "ready note"),
                     ("BOARD-148", "Merged", "None.", "later completed"),
                     ("BOARD-149", "In Review", "None.", "reviewing"),
                     ("BOARD-150", "Pending Merge", "None.", "awaiting merge"),
                     ("BOARD-151", "Dropped", "None.", "cancelled note")])
        for number, (board_id, status, blocked_by, notes) in enumerate(rows):
            cells = [board_id, "Task " + board_id, "Feature", status, "P1", "risk text",
                     blocked_by, "control", "branch/path" if status == "In Progress" else "-", notes]
            lines.append("| " + " | ".join(value.replace("|", "\\|") for value in cells) + " |")
        return "\n".join(lines)

    def snapshot(self):
        with sqlite3.connect(self.path) as connection:
            return connection.execute("SELECT markdown, source_bytes, revision FROM board").fetchall(), \
                connection.execute("SELECT name FROM sqlite_master WHERE type='table' "
                                   "AND name IN ('planned_items','acceptance_criteria','active_work')").fetchall()

    def test_dry_run_is_read_only_and_apply_maps_rows_and_preserves_data(self):
        before = self.snapshot()
        preview = board.migrate_normalized(self.path)
        self.assertEqual(preview, {"items": 22, "queued": 13, "active": 5,
                                   "completed": 3, "cancelled": 1})
        self.assertEqual(self.snapshot(), before)
        result = board.migrate_normalized(self.path, apply=True)
        self.assertEqual(result["items"], 22)
        self.assertEqual(Path(result["backup"]).is_file(), True)
        with board.connect(self.path) as connection:
            self.assertEqual(connection.execute(
                "SELECT id, blocked_by, notes FROM planned_items WHERE id='BOARD-130'").fetchone(),
                ("BOARD-130", "None.", "- [x] Keep blocker; Proof: captured"))
            self.assertEqual(connection.execute(
                "SELECT id, queue_position FROM planned_items WHERE queue_position IS NOT NULL "
                "ORDER BY queue_position LIMIT 2").fetchall(),
                [("BOARD-143", 0), ("BOARD-132", 1)])
            self.assertEqual(connection.execute(
                "SELECT status, branch_worktree FROM active_work WHERE plan_item_id='BOARD-146'").fetchone(),
                ("In Progress", "branch/path"))
            self.assertEqual(connection.execute(
                "SELECT status FROM active_work WHERE plan_item_id='BOARD-130'").fetchone(),
                ("Blocked",))
            self.assertEqual(connection.execute(
                "SELECT status FROM active_work WHERE plan_item_id='BOARD-147'").fetchone(), ("Ready",))
            self.assertEqual(connection.execute(
                "SELECT status FROM active_work WHERE plan_item_id='BOARD-149'").fetchone(), ("In Review",))
            self.assertEqual(connection.execute(
                "SELECT status FROM active_work WHERE plan_item_id='BOARD-150'").fetchone(),
                ("Pending Merge",))
            self.assertEqual(connection.execute(
                "SELECT terminal_outcome FROM planned_items WHERE id='BOARD-131'").fetchone(),
                ("completed",))
            self.assertEqual(connection.execute(
                "SELECT terminal_outcome FROM planned_items WHERE id='BOARD-148'").fetchone(),
                ("completed",))
            self.assertEqual(connection.execute(
                "SELECT terminal_outcome FROM planned_items WHERE id='BOARD-151'").fetchone(),
                ("cancelled",))
            self.assertEqual(connection.execute(
                "SELECT position, text, verified, proof FROM acceptance_criteria "
                "WHERE plan_item_id='BOARD-146'").fetchall(),
                [(0, "Active criterion", 1, "explicit"),
                 (1, "Secondary criterion", 0, "second")])
            self.assertEqual(connection.execute(
                "SELECT COUNT(*) FROM acceptance_criteria").fetchone(), (3,))
            rendered, error = board.parse_table(board.normalized_markdown(
                connection, self.markdown))
            self.assertIsNone(error)
            rendered_rows = [board.cell_texts(rendered["lines"], index) for index in rendered["rows"]]
            self.assertEqual([row[0] for row in rendered_rows],
                             ["BOARD-130", "BOARD-131"] +
                             ["BOARD-%03d" % number for number in
                              (143, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 144)] +
                              ["BOARD-145", "BOARD-146", "BOARD-147", "BOARD-148", "BOARD-149",
                               "BOARD-150", "BOARD-151"])
            self.assertEqual(rendered_rows[0][6], "None.")
            rendered_by_id = {row[0]: row for row in rendered_rows}
            expected_dependencies = {
                143: "None.", 132: "BOARD-143", 133: "BOARD-132", 134: "None.",
                135: "BOARD-134", 136: "None.", 137: "BOARD-134,BOARD-135,BOARD-136",
                138: "None.", 139: "None.", 140: "BOARD-133",
                141: "BOARD-130,BOARD-133,BOARD-137",
                142: "BOARD-130,BOARD-132,BOARD-133,BOARD-137,BOARD-141",
                144: "BOARD-130"}
            self.assertEqual({"BOARD-%03d" % number: rendered_by_id["BOARD-%03d" % number][6]
                              for number in expected_dependencies},
                             {"BOARD-%03d" % number: dependency
                              for number, dependency in expected_dependencies.items()})
            self.assertEqual(rendered_by_id["BOARD-146"][8], "branch/path")
            self.assertEqual(connection.execute(
                "SELECT notes FROM planned_items WHERE id='BOARD-130'").fetchone()[0],
                "- [x] Keep blocker; Proof: captured")
        with sqlite3.connect(result["backup"]) as backup:
            self.assertEqual(backup.execute("SELECT markdown FROM board").fetchone()[0], self.markdown)
            self.assertEqual(backup.execute("SELECT revision FROM board WHERE id=1").fetchone(), (0,))
        with board.connect(self.path) as connection:
            self.assertEqual(connection.execute("SELECT revision FROM board WHERE id=1").fetchone(), (1,))

    def test_compatibility_write_updates_active_fields_and_preserves_criteria(self):
        board.migrate_normalized(self.path, apply=True)
        with patch.object(board, "live_database", return_value=self.path), \
                patch.object(board, "database_path", return_value=self.path):
            parsed, error = board.read_table("fixture.md")
            self.assertIsNone(error)
            row_index = next(index for index in parsed["rows"]
                             if board.cell_texts(parsed["lines"], index)[0] == "BOARD-146")
            lines = list(parsed["lines"])
            cells = board.cell_texts(lines, row_index)
            for field, value in ((3, "Blocked"), (8, "new/worktree"),
                                 (9, "- [x] Changed criterion; Proof: revised")):
                lines[row_index] = board.replace_cell(lines[row_index], field, value)
            board.write_atomic("fixture.md", lines)
        with board.connect(self.path) as connection:
            self.assertEqual(connection.execute(
                "SELECT status, branch_worktree FROM active_work "
                "WHERE plan_item_id='BOARD-146'").fetchone(), ("Blocked", "new/worktree"))
            self.assertEqual(connection.execute(
                "SELECT text, verified, proof FROM acceptance_criteria "
                "WHERE plan_item_id='BOARD-146'").fetchall(),
                [("Active criterion", 1, "explicit"), ("Secondary criterion", 0, "second")])

    def test_remove_cancels_normalized_rows_and_retains_history(self):
        board.migrate_normalized(self.path, apply=True)
        with patch.object(board, "live_database", return_value=self.path), \
                patch.object(board, "database_path", return_value=self.path), \
                patch.object(board, "note_uncommitted"):
            self.assertEqual(board.cmd_remove(SimpleNamespace(id="BOARD-146"), "fixture.md"), board.OK)
            self.assertEqual(board.cmd_remove(SimpleNamespace(id="BOARD-143"), "fixture.md"), board.OK)
        with board.connect(self.path) as connection:
            for board_id in ("BOARD-146", "BOARD-143"):
                self.assertEqual(connection.execute(
                    "SELECT terminal_outcome, queue_position FROM planned_items WHERE id=?",
                    (board_id,)).fetchone(), ("cancelled", None))
                self.assertIsNone(connection.execute(
                    "SELECT 1 FROM active_work WHERE plan_item_id=?", (board_id,)).fetchone())
            self.assertEqual(connection.execute(
                "SELECT notes FROM planned_items WHERE id='BOARD-146'").fetchone()[0],
                "- [x] Active criterion; Proof: explicit; - [ ] Secondary criterion; Proof: second")
            self.assertEqual(connection.execute(
                "SELECT text, verified, proof FROM acceptance_criteria "
                "WHERE plan_item_id='BOARD-146' ORDER BY position").fetchall(),
                [("Active criterion", 1, "explicit"), ("Secondary criterion", 0, "second")])

    def test_same_line_checklists_extract_individual_state_and_proofs(self):
        notes = "- [x] First criterion; Proof: first proof; - [ ] Second criterion; Proof: second proof"
        self.assertEqual(board.criteria_from_notes(notes),
                         [("First criterion", True, "first proof"),
                          ("Second criterion", False, "second proof")])

    def test_duplicate_ids_fail_transaction_and_leave_source_rows_unchanged(self):
        duplicate = self.markdown + "\n" + self.markdown.splitlines()[2]
        with sqlite3.connect(self.path) as connection:
            connection.execute("UPDATE board SET markdown=? WHERE id=1", (duplicate,))
        before = self.snapshot()
        with self.assertRaises(sqlite3.IntegrityError):
            board.migrate_normalized(self.path, apply=True)
        after = self.snapshot()
        self.assertEqual(after, before)
        with sqlite3.connect(self.path) as connection:
            self.assertEqual(connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name IN ('planned_items','acceptance_criteria','active_work')").fetchall(), [])

    def test_repeat_migration_refuses_without_replacing_backup(self):
        result = board.migrate_normalized(self.path, apply=True)
        backup_bytes = Path(result["backup"]).read_bytes()
        with self.assertRaisesRegex(ValueError, "already exists"):
            board.migrate_normalized(self.path, apply=True)
        self.assertEqual(Path(result["backup"]).read_bytes(), backup_bytes)

    def test_schema_rejects_duplicate_positions_and_orphan_criteria(self):
        board.migrate_normalized(self.path, apply=True)
        with self.assertRaises(sqlite3.IntegrityError):
            with board.connect(self.path) as connection:
                connection.execute("UPDATE planned_items SET queue_position=1 WHERE id='BOARD-143'")
        with self.assertRaises(sqlite3.IntegrityError):
            with board.connect(self.path) as connection:
                connection.execute("INSERT INTO acceptance_criteria "
                                    "(plan_item_id, position, text) VALUES ('BOARD-146', 0, 'duplicate')")
        with self.assertRaises(sqlite3.IntegrityError):
            with board.connect(self.path) as connection:
                connection.execute("INSERT INTO acceptance_criteria "
                                    "(plan_item_id, position, text) VALUES ('BOARD-999', 0, 'orphan')")


class PlannedLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="board-plan-lifecycle-")
        self.addCleanup(self.temp.cleanup)
        self.path = str(Path(self.temp.name) / "factory-board.sqlite3")
        markdown = NormalizedBoardMigrationTests.make_markdown()
        with sqlite3.connect(self.path) as connection:
            connection.execute("CREATE TABLE board (id INTEGER PRIMARY KEY, markdown TEXT NOT NULL, "
                               "source_bytes BLOB, revision INTEGER NOT NULL)")
            connection.execute("INSERT INTO board VALUES (1, ?, NULL, 0)", (markdown,))
        board.migrate_normalized(self.path, apply=True)

    @staticmethod
    def draft(key, task, dependencies=None):
        return {"key": key, "task": task, "type": "Feature", "priority": "P2",
                "risk": "🟡 medium — scoped", "user_story": "As a user, I can " + task,
                "acceptance_criteria": ["First observable result", "Second observable result"],
                "blocked_by": dependencies or [], "repos": ["control"], "notes": "preview note"}

    def state_snapshot(self):
        with board.connect(self.path) as connection:
            return (
                connection.execute("SELECT markdown, revision FROM board").fetchone(),
                connection.execute("SELECT * FROM planned_items ORDER BY id").fetchall(),
                connection.execute("SELECT * FROM acceptance_criteria ORDER BY plan_item_id, position")
                .fetchall(),
                connection.execute("SELECT * FROM active_work ORDER BY plan_item_id").fetchall(),
            )

    def run_cli(self, args, stdin=""):
        output = io.StringIO()
        with patch.object(board, "initialize_board",
                          return_value=str(Path(self.temp.name) / board.BOARD_PATH)), \
                patch.object(board, "live_database", return_value=self.path), \
                patch("sys.stdin", io.StringIO(stdin)), redirect_stdout(output), \
                redirect_stderr(io.StringIO()):
            return board.main(args), output.getvalue()

    def test_accept_is_atomic_resolves_batch_dependencies_and_preserves_order(self):
        before = self.state_snapshot()
        invalid = [self.draft("valid", "Valid"), self.draft("invalid", "Invalid")]
        invalid[1]["acceptance_criteria"] = ["Only one"]
        with self.assertRaises(board.PlanValidationError):
            board.accept_plan_batch(self.path, invalid)
        self.assertEqual(self.state_snapshot(), before)

        batch = [
            self.draft("core", "Core", ["BOARD-143"]),
            self.draft("client", "Client", ["core"]),
        ]
        batch[1].pop("notes")
        status, output = self.run_cli(["plan", "accept"], json.dumps(batch))
        self.assertEqual(status, board.OK)
        accepted = [{"key": line.split()[1], "id": line.split()[-1]}
                    for line in output.splitlines()]
        self.assertEqual(accepted, [{"key": "core", "id": "BOARD-152"},
                                    {"key": "client", "id": "BOARD-153"}])
        queued = board.plan_rows(self.path, "queue")
        self.assertEqual([item["id"] for item in queued[-2:]], ["BOARD-152", "BOARD-153"])
        self.assertEqual([item["queue_position"] for item in queued[-2:]], [13, 14])
        with board.connect(self.path) as connection:
            self.assertEqual(connection.execute(
                "SELECT blocked_by, user_story, notes FROM planned_items WHERE id='BOARD-152'").fetchone(),
                ("BOARD-143", "As a user, I can Core", "preview note"))
            self.assertEqual(connection.execute(
                "SELECT blocked_by FROM planned_items WHERE id='BOARD-153'").fetchone(),
                ("BOARD-152",))
            self.assertEqual(connection.execute(
                "SELECT notes FROM planned_items WHERE id='BOARD-153'").fetchone(), ("",))
            self.assertEqual(connection.execute(
                "SELECT verified, proof FROM acceptance_criteria WHERE plan_item_id='BOARD-152' "
                "ORDER BY position").fetchall(), [(0, None), (0, None)])

        with board.connect(self.path) as connection:
            markdown = connection.execute("SELECT markdown FROM board WHERE id=1").fetchone()[0]
            projection = board.normalized_markdown(connection, markdown)
        projected, error = board.parse_table(projection)
        self.assertIsNone(error)
        row = board.row_by_id(projected, "BOARD-153")
        self.assertEqual(board.cell_texts(projected["lines"], row)[
            board.field_index(projected, "notes")], "-")
        with patch.object(board, "live_database", return_value=self.path), \
                patch.object(board, "database_path", return_value=self.path), \
                patch.object(board, "note_uncommitted"):
            self.assertEqual(board.cmd_set_field(SimpleNamespace(id="BOARD-153", field="risk",
                                                                  value="🟢 low — reviewed"),
                                                 "fixture.md"), board.OK)
        with board.connect(self.path) as connection:
            self.assertEqual(connection.execute(
                "SELECT notes FROM planned_items WHERE id='BOARD-153'").fetchone(), ("",))

    def test_transition_commands_refuse_duplicates_and_never_reuse_ids(self):
        before = self.state_snapshot()
        self.assertEqual(self.run_cli(["plan", "complete", "BOARD-146"])[0], board.REFUSED)
        self.assertEqual(self.run_cli(["plan", "complete", "BOARD-150"])[0], board.REFUSED)
        self.assertEqual(self.state_snapshot(), before)
        first = board.accept_plan_batch(self.path, [self.draft("first", "First")])[0]
        self.assertEqual(first["id"], "BOARD-152")
        self.assertEqual(self.run_cli(["plan", "cancel", first["id"]])[0], board.OK)
        second = board.accept_plan_batch(self.path, [self.draft("second", "Second")])[0]
        self.assertEqual(second["id"], "BOARD-153")
        self.assertEqual(self.run_cli(["plan", "promote", second["id"]])[0], board.OK)
        self.assertEqual(self.run_cli(["plan", "promote", second["id"]])[0], board.REFUSED)
        with board.connect(self.path) as connection:
            self.assertEqual(connection.execute(
                "SELECT queue_position, terminal_outcome FROM planned_items WHERE id='BOARD-153'").fetchone(),
                (None, None))
            self.assertEqual(connection.execute(
                "SELECT status FROM active_work WHERE plan_item_id='BOARD-153'").fetchone(), ("Ready",))
        self.assertEqual(self.run_cli(["plan", "complete", second["id"]])[0], board.OK)
        history = board.plan_rows(self.path, "history")
        self.assertEqual([item["id"] for item in history[-2:]], ["BOARD-152", "BOARD-153"])
        self.assertEqual([item["terminal_outcome"] for item in history[-2:]],
                         ["cancelled", "completed"])
        self.assertEqual(len(history[-1]["acceptance_criteria"]), 2)
        with board.connect(self.path) as connection:
            self.assertIsNone(connection.execute(
                "SELECT 1 FROM active_work WHERE plan_item_id='BOARD-153'").fetchone())

    def test_compatibility_edits_preserve_queue_history_and_structured_criteria(self):
        with patch.object(board, "live_database", return_value=self.path), \
                patch.object(board, "database_path", return_value=self.path), \
                patch.object(board, "note_uncommitted"):
            self.assertEqual(board.cmd_set_status(SimpleNamespace(id="BOARD-146", status="Blocked"),
                                                  "fixture.md"), board.OK)
            self.assertEqual(board.cmd_set_field(SimpleNamespace(id="BOARD-146", field="notes",
                                                                  value="edited note"),
                                                 "fixture.md"), board.OK)
            self.assertEqual(board.cmd_set_field(SimpleNamespace(id="BOARD-143", field="notes",
                                                                  value="queued edit"),
                                                 "fixture.md"), board.OK)
            self.assertEqual(board.cmd_set_field(SimpleNamespace(id="BOARD-131", field="risk",
                                                                  value="updated risk"),
                                                 "fixture.md"), board.OK)
            self.assertEqual(board.cmd_set_status(SimpleNamespace(id="BOARD-143", status="Ready"),
                                                  "fixture.md"), board.REFUSED)
            self.assertEqual(board.cmd_set_status(SimpleNamespace(id="BOARD-131", status="In Progress"),
                                                  "fixture.md"), board.REFUSED)
        with board.connect(self.path) as connection:
            self.assertEqual(connection.execute(
                "SELECT text, verified, proof FROM acceptance_criteria WHERE plan_item_id='BOARD-146' "
                "ORDER BY position").fetchall(),
                [("Active criterion", 1, "explicit"), ("Secondary criterion", 0, "second")])
            self.assertEqual(connection.execute(
                "SELECT notes FROM planned_items WHERE id='BOARD-146'").fetchone(), ("edited note",))
            self.assertIsNotNone(connection.execute(
                "SELECT queue_position FROM planned_items WHERE id='BOARD-143' "
                "AND queue_position IS NOT NULL").fetchone())
            self.assertEqual(connection.execute(
                "SELECT terminal_outcome, risk FROM planned_items WHERE id='BOARD-131'").fetchone(),
                ("completed", "updated risk"))

    def test_active_views_exclude_queued_and_terminal_rows(self):
        with patch.object(board, "live_database", return_value=self.path), \
                patch.object(board, "database_path", return_value=self.path):
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(board.cmd_show(SimpleNamespace(id=None), "fixture.md"), board.OK)
            shown_ids = {line.split(" | ", 1)[0] for line in output.getvalue().splitlines()}
            self.assertIn("BOARD-146", shown_ids)
            self.assertNotIn("BOARD-143", shown_ids)
            self.assertNotIn("BOARD-131", shown_ids)

            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(board.cmd_lanes(SimpleNamespace(), "fixture.md"), board.OK)
            lanes = output.getvalue()
            self.assertIn("Backlog: 0", lanes)
            self.assertIn("Merged: 0", lanes)
            self.assertIn("total: 5", lanes)

            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(board.cmd_export("fixture.md"), board.OK)
            exported_path = Path(output.getvalue().strip())
            exported, error = board.parse_table(exported_path.read_text())
            self.assertIsNone(error)
            exported_ids = {board.cell_texts(exported["lines"], index)[0]
                            for index in exported["rows"]}
            self.assertEqual(exported_ids, shown_ids)

    def test_worktree_finalize_writer_completes_normalized_item_atomically(self):
        script = Path(board.__file__).parents[2] / "git-worktree" / "scripts" / "worktree.py"
        spec = importlib.util.spec_from_file_location("board_lifecycle_worktree", script)
        worktree = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(worktree)
        with board.connect(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            markdown, revision = connection.execute(
                "SELECT markdown, revision FROM board WHERE id=1").fetchone()
            parsed, error = board.parse_table(markdown)
            self.assertIsNone(error)
            index = board.row_by_id(parsed, "BOARD-146")
            success, message = worktree.clear_row_worktree(
                board, "fixture.md", parsed, index, self.temp.name,
                str(Path(self.temp.name) / "branch" / "path"), status="Merged",
                connection=connection, revision=revision)
            self.assertTrue(success, message)
        with board.connect(self.path) as connection:
            self.assertEqual(connection.execute(
                "SELECT terminal_outcome FROM planned_items WHERE id='BOARD-146'").fetchone(),
                ("completed",))
            self.assertIsNone(connection.execute(
                "SELECT 1 FROM active_work WHERE plan_item_id='BOARD-146'").fetchone())
            self.assertEqual(connection.execute(
                "SELECT COUNT(*) FROM acceptance_criteria WHERE plan_item_id='BOARD-146'").fetchone(),
                (2,))


class PlannedCliDatabaseTests(unittest.TestCase):
    def make_repo(self, legacy=False):
        temporary = tempfile.TemporaryDirectory(prefix="board-plan-cli-")
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
        (root / ".opencode").mkdir()
        (root / ".opencode" / "repos.json").write_text(json.dumps({"control": "."}))
        (root / "docs").mkdir()
        source = NormalizedBoardMigrationTests.make_markdown().encode() if legacy else None
        if source is not None:
            (root / board.BOARD_PATH).write_bytes(source)
        board.initialize_board(str(root))
        database = board.database_path(str(root))
        board.migrate_normalized(database, apply=True)
        return root, database, source

    def run_cli(self, root, arguments, stdin="", expected=board.OK):
        result = subprocess.run([sys.executable, str(Path(board.__file__).resolve()), *arguments],
                                cwd=root, input=stdin, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def database_snapshot(self, database):
        with sqlite3.connect(database) as connection:
            return tuple(connection.iterdump())

    def assert_legacy_untouched(self, root, database, source):
        legacy = root / board.BOARD_PATH
        if source is None:
            self.assertFalse(legacy.exists())
        else:
            self.assertEqual(legacy.read_bytes(), source)
        for suffix in ("-wal", "-shm", "-journal"):
            self.assertFalse(Path(str(legacy) + suffix).exists())
        with sqlite3.connect(database) as connection:
            self.assertEqual(connection.execute(
                "SELECT source_bytes FROM board WHERE id=1").fetchone(), (source,))

    def test_all_plan_commands_use_canonical_database_with_or_without_legacy_source(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                root, database, source = self.make_repo(legacy)
                before = self.database_snapshot(database)
                queue = board.plan_rows(database, "queue")
                history = board.plan_rows(database, "history")
                self.run_cli(root, ["plan", "queue"])
                self.run_cli(root, ["plan", "history"])
                self.assertEqual(self.database_snapshot(database), before)
                self.assert_legacy_untouched(root, database, source)

                drafts = [PlannedLifecycleTests.draft("finish", "Finish CLI work"),
                          PlannedLifecycleTests.draft("cancel", "Cancel CLI work")]
                result = self.run_cli(root, ["plan", "accept"], json.dumps(drafts))
                ids = [line.split()[-1] for line in result.stdout.splitlines()]
                self.assertEqual(len(ids), 2)
                self.assertEqual([item["id"] for item in board.plan_rows(database, "queue")],
                                 [item["id"] for item in queue] + ids)
                self.assert_legacy_untouched(root, database, source)
                self.run_cli(root, ["plan", "promote", ids[0]])
                with sqlite3.connect(database) as connection:
                    self.assertEqual(connection.execute(
                        "SELECT status FROM active_work WHERE plan_item_id=?", (ids[0],))
                        .fetchone(), ("Ready",))
                    self.assertEqual(connection.execute(
                        "SELECT COUNT(*) FROM acceptance_criteria WHERE plan_item_id IN (?, ?)", ids)
                        .fetchone(), (4,))
                self.assert_legacy_untouched(root, database, source)
                self.run_cli(root, ["plan", "complete", ids[0]])
                self.assert_legacy_untouched(root, database, source)
                self.run_cli(root, ["plan", "cancel", ids[1]])
                self.assert_legacy_untouched(root, database, source)
                self.assertEqual(board.plan_rows(database, "queue"), queue)
                terminal = board.plan_rows(database, "history")
                self.assertEqual(len(terminal), len(history) + 2)
                self.assertEqual({item["id"]: item["terminal_outcome"] for item in terminal
                                  if item["id"] in ids},
                                 {ids[0]: "completed", ids[1]: "cancelled"})
                before = self.database_snapshot(database)
                displayed = self.run_cli(root, ["plan", "history"]).stdout
                for item_id in ids:
                    self.assertIn(item_id, displayed)
                self.run_cli(root, ["plan", "queue"])
                self.assertEqual(self.database_snapshot(database), before)
                self.assert_legacy_untouched(root, database, source)

    def test_file_plan_commands_are_refused_without_mutating_fixture_or_database(self):
        root, database, source = self.make_repo()
        fixture = root / "fixture.md"
        fixture_bytes = NormalizedBoardMigrationTests.make_markdown().encode()
        fixture.write_bytes(fixture_bytes)
        before = self.database_snapshot(database)
        for arguments in (["queue"], ["history"], ["accept"], ["promote", "BOARD-001"],
                          ["complete", "BOARD-001"], ["cancel", "BOARD-001"]):
            with self.subTest(command=arguments[0]):
                result = self.run_cli(root, ["--file", str(fixture), "plan", *arguments],
                                      json.dumps([PlannedLifecycleTests.draft("new", "New work")]),
                                      expected=board.REFUSED)
                self.assertIn("--file is read-only", result.stderr)
                self.assertEqual(fixture.read_bytes(), fixture_bytes)
                self.assertEqual(self.database_snapshot(database), before)
                self.assert_legacy_untouched(root, database, source)
        self.run_cli(root, ["--file", str(fixture), "show"])
        self.assertEqual(fixture.read_bytes(), fixture_bytes)
        self.assertEqual(self.database_snapshot(database), before)


class PlannedProjectionValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="board-plan-validation-")
        self.addCleanup(self.temp.cleanup)
        self.path = str(Path(self.temp.name) / "factory-board.sqlite3")
        markdown = NormalizedBoardMigrationTests.make_markdown()
        with sqlite3.connect(self.path) as connection:
            connection.execute("CREATE TABLE board (id INTEGER PRIMARY KEY, markdown TEXT NOT NULL, "
                               "source_bytes BLOB, revision INTEGER NOT NULL)")
            connection.execute("INSERT INTO board VALUES (1, ?, NULL, 0)", (markdown,))
        board.migrate_normalized(self.path, apply=True)

    def draft(self, key, task):
        return PlannedLifecycleTests.draft(key, task)

    def state_snapshot(self):
        with board.connect(self.path) as connection:
            return (
                connection.execute("SELECT markdown, revision FROM board").fetchall(),
                connection.execute("SELECT * FROM planned_items ORDER BY id").fetchall(),
                connection.execute("SELECT * FROM acceptance_criteria "
                                   "ORDER BY plan_item_id, position").fetchall(),
                connection.execute("SELECT * FROM active_work ORDER BY plan_item_id").fetchall(),
            )

    def test_cr_and_lf_repository_ids_refuse_atomically(self):
        for line_break in ("\r", "\n"):
            with self.subTest(line_break=repr(line_break)):
                item = self.draft("repo", "Repository validation")
                item["repos"] = ["control" + line_break + "api"]
                before = self.state_snapshot()
                with self.assertRaises(board.PlanValidationError):
                    board.accept_plan_batch(self.path, [item])
                self.assertEqual(self.state_snapshot(), before)

    def test_valid_projection_parses_and_malformed_projection_is_not_persisted(self):
        item = self.draft("valid", "Valid repository projection")
        item["repos"] = ["control", "api"]
        accepted = board.accept_plan_batch(self.path, [item])[0]
        with board.connect(self.path) as connection:
            markdown, revision = connection.execute(
                "SELECT markdown, revision FROM board WHERE id=1").fetchone()
            parsed, error = board.parse_table(markdown)
            self.assertIsNone(error)
            row_index = board.row_by_id(parsed, accepted["id"])
            self.assertEqual(board.cell_texts(parsed["lines"], row_index)[
                board.field_index(parsed, "repos")], "control,api")

            connection.execute("BEGIN IMMEDIATE")
            connection.execute("UPDATE planned_items SET repos=? WHERE id=?",
                               ("control\nbroken", accepted["id"]))

        before = self.state_snapshot()
        with self.assertRaisesRegex(ValueError, "generated normalized board projection is invalid"):
            with board.connect(self.path) as connection:
                connection.execute("BEGIN IMMEDIATE")
                board.persist_normalized_projection(connection)
        self.assertEqual(self.state_snapshot(), before)


if __name__ == "__main__":
    unittest.main()
