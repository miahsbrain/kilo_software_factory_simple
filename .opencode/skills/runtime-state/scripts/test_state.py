import os
import subprocess
import tempfile
import unittest

import state


class RuntimeStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.temp.name, "checkout")
        os.makedirs(self.root)
        subprocess.run(["git", "-C", self.root, "init"], check=True,
                       capture_output=True, text=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_primary_checkout_and_state_root_from_repo(self):
        self.assertEqual(state.primary_checkout(self.root), self.root)
        self.assertEqual(state.state_root(self.root), os.path.join(self.root, ".factory-state"))

    def test_primary_checkout_refuses_path_outside_a_repository(self):
        with self.assertRaisesRegex(OSError, "cannot resolve"):
            state.primary_checkout(self.temp.name)

    def test_migration_dry_run_does_not_write_and_apply_verifies(self):
        source = os.path.join(self.root, ".git", "factory-board.sqlite3")
        os.makedirs(os.path.dirname(source), exist_ok=True)
        with open(source, "wb") as stream:
            stream.write(b"fixture state")
        state.migrate(self.root)
        destination = os.path.join(self.root, ".factory-state", "factory-board.sqlite3")
        self.assertFalse(os.path.exists(destination))
        state.migrate(self.root, apply=True)
        with open(destination, "rb") as stream:
            self.assertEqual(stream.read(), b"fixture state")
        self.assertTrue(os.path.exists(source))
        state.migrate(self.root, apply=True)

    def test_migration_copies_database_sidecars_and_review_tree(self):
        common = os.path.join(self.root, ".git")
        sources = {
            "factory-board.sqlite3-wal": b"wal fixture",
            os.path.join("reviews", "BOARD-1-ledger.md"): b"ledger fixture",
        }
        for relative, content in sources.items():
            path = os.path.join(common, relative)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as stream:
                stream.write(content)
        state.migrate(self.root, apply=True)
        for relative, content in sources.items():
            path = os.path.join(self.root, ".factory-state", relative)
            with open(path, "rb") as stream:
                self.assertEqual(stream.read(), content)

    def test_nonidentical_destination_refuses_without_overwrite(self):
        source = os.path.join(self.root, ".git", "factory-board.sqlite3")
        destination = os.path.join(self.root, ".factory-state", "factory-board.sqlite3")
        os.makedirs(os.path.dirname(source), exist_ok=True)
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        for path, content in ((source, b"source"), (destination, b"different")):
            with open(path, "wb") as stream:
                stream.write(content)
        with self.assertRaisesRegex(OSError, "non-identical destination"):
            state.migrate(self.root, apply=True)
        with open(destination, "rb") as stream:
            self.assertEqual(stream.read(), b"different")

    def test_migration_preserves_cleanup_tree_under_control_repo_identity(self):
        source = os.path.join(self.root, ".git", "cleanup-wt", "recovery.patch")
        os.makedirs(os.path.dirname(source))
        with open(source, "wb") as stream:
            stream.write(b"recovery")
        state.migrate(self.root, apply=True)
        destination = os.path.join(self.root, ".factory-state", "cleanup-wt",
                                   "control", "recovery.patch")
        with open(destination, "rb") as stream:
            self.assertEqual(stream.read(), b"recovery")
        self.assertTrue(os.path.exists(source))

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks are unavailable")
    def test_migration_refuses_destination_symlink(self):
        destination = os.path.join(self.root, ".factory-state")
        external = os.path.join(self.temp.name, "external")
        os.mkdir(external)
        os.symlink(external, destination)
        with self.assertRaisesRegex(OSError, "symbolic link"):
            state.migrate(self.root, apply=True)
        self.assertEqual(os.listdir(external), [])


if __name__ == "__main__":
    unittest.main()
