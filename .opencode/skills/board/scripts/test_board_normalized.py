#!/usr/bin/env python3
"""Normalized board migration tests use only isolated SQLite databases."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
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
                     ("BOARD-146", "In Progress", "BOARD-145", "- [ ] Active criterion; Proof: explicit"),
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
        self.assertEqual(result["items"], 19)
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
                [(0, "Active criterion", 0, "explicit")])
            self.assertEqual(connection.execute(
                "SELECT COUNT(*) FROM acceptance_criteria").fetchone(), (2,))
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
            self.assertEqual(rendered_rows[-3][8], "branch/path")
            self.assertEqual(connection.execute(
                "SELECT notes FROM planned_items WHERE id='BOARD-130'").fetchone()[0],
                "- [x] Keep blocker; Proof: captured")
        with sqlite3.connect(result["backup"]) as backup:
            self.assertEqual(backup.execute("SELECT markdown FROM board").fetchone()[0], self.markdown)
            self.assertEqual(backup.execute("SELECT revision FROM board WHERE id=1").fetchone(), (0,))
        with board.connect(self.path) as connection:
            self.assertEqual(connection.execute("SELECT revision FROM board WHERE id=1").fetchone(), (1,))

    def test_compatibility_write_updates_active_status_worktree_and_criteria(self):
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
                [("Changed criterion", 1, "revised")])

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


if __name__ == "__main__":
    unittest.main()
