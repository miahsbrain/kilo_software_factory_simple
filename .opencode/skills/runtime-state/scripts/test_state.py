import os
import sqlite3
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import state


class RuntimeStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.temp.name, "checkout")
        os.makedirs(self.root)
        subprocess.run(["git", "-C", self.root, "init"], check=True,
                       capture_output=True, text=True)
        self.common = os.path.join(self.root, ".git")
        self.destination = os.path.join(self.root, ".factory-state")

    def tearDown(self):
        self.temp.cleanup()

    def write(self, root, relative, content):
        path = os.path.join(root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as stream:
            stream.write(content)
        return path

    def tree_snapshot(self, root):
        snapshot = {}
        for current, directories, files in os.walk(root):
            for name in directories + files:
                path = os.path.join(current, name)
                relative = os.path.relpath(path, root)
                info = os.lstat(path)
                content = None
                if not os.path.isdir(path):
                    with open(path, "rb") as stream:
                        content = stream.read()
                snapshot[relative] = (info.st_mode, content)
        return snapshot

    def wal_database(self):
        path = os.path.join(self.common, state.BOARD_DATABASE)
        connection = sqlite3.connect(path)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA wal_autocheckpoint=0")
        connection.execute("CREATE TABLE entries (value TEXT NOT NULL)")
        connection.execute("INSERT INTO entries VALUES ('committed only to WAL')")
        connection.commit()
        wal = path + "-wal"
        self.assertTrue(os.path.isfile(wal))
        self.assertGreater(os.path.getsize(wal), 0)
        return path, connection

    def test_primary_checkout_and_state_root_from_repo(self):
        self.assertEqual(state.primary_checkout(self.root), self.root)
        self.assertEqual(state.state_root(self.root), self.destination)

    def test_primary_checkout_refuses_path_outside_a_repository(self):
        with self.assertRaisesRegex(OSError, "cannot resolve"):
            state.primary_checkout(self.temp.name)

    def test_readiness_blocks_legacy_state_but_allows_fresh_clone(self):
        state.ensure_runtime_ready(self.root)
        self.assertFalse(os.path.exists(self.destination))
        self.write(self.common, "factory-board-export.md", b"old export")
        with self.assertRaisesRegex(OSError, "run .*state.py migrate"):
            state.ensure_runtime_ready(self.root)
        self.assertFalse(os.path.exists(self.destination))

    def test_migration_snapshots_uncheckpointed_wal_without_changing_source(self):
        database, connection = self.wal_database()
        self.write(self.common, "factory-board-export.md", b"board export")
        self.write(self.common, "reviews/BOARD-1-ledger.md", b"ledger")
        self.write(self.common, "cleanup-wt/finalize-BOARD-1-control.json", b"journal")
        before = self.tree_snapshot(self.common)

        state.migrate(self.root, apply=True)

        after = self.tree_snapshot(self.common)
        self.assertEqual(after, before)
        destination_db = os.path.join(self.destination, state.BOARD_DATABASE)
        self.assertFalse(os.path.exists(destination_db + "-wal"))
        self.assertFalse(os.path.exists(destination_db + "-shm"))
        state._verify_database(destination_db)
        with sqlite3.connect(destination_db) as migrated:
            self.assertEqual(migrated.execute("SELECT value FROM entries").fetchone()[0],
                             "committed only to WAL")
        self.assertTrue(os.path.isfile(os.path.join(
            self.destination, "cleanup-wt", "control", "finalize-BOARD-1-control.json")))
        connection.close()

    def test_migration_failure_after_staging_leaves_no_destination_or_stage(self):
        database, connection = self.wal_database()
        self.write(self.common, "factory-board-export.md", b"export")
        with patch.object(state, "_copy_file", side_effect=OSError("injected copy failure")):
            with self.assertRaisesRegex(OSError, "injected copy failure"):
                state.migrate(self.root, apply=True)
        self.assertFalse(os.path.lexists(self.destination))
        self.assertEqual([name for name in os.listdir(self.root)
                          if name.startswith(".factory-state-migration-")], [])
        connection.close()

    def test_exact_existing_snapshot_is_idempotent(self):
        _, connection = self.wal_database()
        self.write(self.common, "reviews/BOARD-1-qa.md", b"report")
        state.migrate(self.root, apply=True)
        state.migrate(self.root, apply=True)
        connection.close()

    def test_partial_destination_refuses_without_mutation(self):
        self.write(self.common, "reviews/BOARD-1-qa.md", b"report")
        os.makedirs(self.destination)
        self.write(self.destination, "reviews", b"partial")
        before = self.tree_snapshot(self.destination)
        with self.assertRaisesRegex(OSError, "partial, extra, or non-identical"):
            state.migrate(self.root, apply=True)
        self.assertEqual(self.tree_snapshot(self.destination), before)

    def test_extra_destination_file_refuses_without_mutation(self):
        self.write(self.common, "factory-board-export.md", b"export")
        state.migrate(self.root, apply=True)
        self.write(self.destination, "unexpected.txt", b"extra")
        before = self.tree_snapshot(self.destination)
        with self.assertRaisesRegex(OSError, "partial, extra, or non-identical"):
            state.migrate(self.root, apply=True)
        self.assertEqual(self.tree_snapshot(self.destination), before)

    def test_conflicting_destination_file_refuses_without_mutation(self):
        self.write(self.common, "factory-board-export.md", b"source")
        os.makedirs(self.destination)
        self.write(self.destination, "factory-board-export.md", b"different")
        before = self.tree_snapshot(self.destination)
        with self.assertRaisesRegex(OSError, "partial, extra, or non-identical"):
            state.migrate(self.root, apply=True)
        self.assertEqual(self.tree_snapshot(self.destination), before)

    def test_no_legacy_state_does_not_create_destination(self):
        state.migrate(self.root, apply=True)
        self.assertFalse(os.path.lexists(self.destination))

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks are unavailable")
    def test_migration_refuses_source_and_destination_symlinks(self):
        external = os.path.join(self.temp.name, "external")
        os.mkdir(external)
        os.symlink(external, os.path.join(self.common, "reviews"))
        with self.assertRaisesRegex(OSError, "symbolic link"):
            state.migrate(self.root, apply=True)
        os.unlink(os.path.join(self.common, "reviews"))
        self.write(self.common, "factory-board-export.md", b"export")
        os.symlink(external, self.destination)
        with self.assertRaisesRegex(OSError, "symbolic link"):
            state.migrate(self.root, apply=True)
        self.assertEqual(os.listdir(external), [])


if __name__ == "__main__":
    unittest.main()
