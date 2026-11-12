#!/usr/bin/env python3
"""Resolve and explicitly migrate clone-local factory runtime state."""
import argparse
import os
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

STATE_DIR = ".factory-state"
BOARD_DATABASE = "factory-board.sqlite3"
BOARD_FILES = ("factory-board-export.md", "factory-board-legacy-backup.md")
SIDECARS = tuple(BOARD_DATABASE + suffix for suffix in ("-wal", "-shm", "-journal"))


def primary_checkout(cwd):
    result = subprocess.run(
        ["git", "-C", cwd, "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True, text=True, timeout=10)
    common = result.stdout.strip()
    if result.returncode or not common or not os.path.isabs(common):
        raise OSError("cannot resolve the absolute Git common directory")
    common = os.path.realpath(common)
    if not os.path.isdir(common) or os.path.basename(common) != ".git":
        raise OSError("Git common directory does not identify an accessible primary checkout")
    root = os.path.dirname(common)
    check = subprocess.run(
        ["git", "-C", root, "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True, text=True, timeout=10)
    if check.returncode or os.path.realpath(check.stdout.strip()) != common:
        raise OSError("cannot verify primary checkout from Git common directory")
    return os.path.realpath(root)


def state_root(cwd):
    return os.path.join(primary_checkout(cwd), STATE_DIR)


def _regular_or_directory(path):
    if os.path.islink(path):
        raise OSError("refusing symbolic link in runtime state: %s" % path)
    info = os.lstat(path)
    if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
        raise OSError("refusing non-regular runtime state: %s" % path)
    if stat.S_ISDIR(info.st_mode):
        for name in os.listdir(path):
            _regular_or_directory(os.path.join(path, name))


def migration_entries(common):
    database = os.path.join(common, BOARD_DATABASE)
    present_sidecars = [os.path.join(common, name) for name in SIDECARS
                        if os.path.lexists(os.path.join(common, name))]
    for sidecar in present_sidecars:
        _regular_or_directory(sidecar)
    if present_sidecars and not os.path.lexists(database):
        raise OSError("orphaned SQLite sidecar; resolve legacy database state before migration")
    if os.path.lexists(os.path.join(common, BOARD_DATABASE + "-journal")):
        raise OSError("legacy SQLite rollback journal exists; stop writers and resolve it before migration")

    entries = []
    if os.path.lexists(database):
        _regular_or_directory(database)
        if not stat.S_ISREG(os.lstat(database).st_mode):
            raise OSError("refusing non-regular runtime database: %s" % database)
        entries.append((database, BOARD_DATABASE, "sqlite"))
    for name in BOARD_FILES:
        source = os.path.join(common, name)
        if os.path.lexists(source):
            _regular_or_directory(source)
            entries.append((source, name, "file"))
    for name, destination in (("reviews", "reviews"),
                              ("cleanup-wt", os.path.join("cleanup-wt", "control"))):
        source = os.path.join(common, name)
        if os.path.lexists(source):
            _regular_or_directory(source)
            if not stat.S_ISDIR(os.lstat(source).st_mode):
                raise OSError("refusing non-directory runtime state: %s" % source)
            entries.append((source, destination, "tree"))
    return entries


def _copy_file(source, destination):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(destination, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as output, open(source, "rb") as input_file:
            shutil.copyfileobj(input_file, output)
        shutil.copystat(source, destination, follow_symlinks=False)
    except BaseException:
        if os.path.lexists(destination):
            os.unlink(destination)
        raise


def _verify_database(path):
    uri = Path(path).resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        result = connection.execute("PRAGMA integrity_check").fetchone()
    finally:
        connection.close()
    if result != ("ok",):
        raise OSError("SQLite integrity check failed: %s" % (result,))


def _backup_database(source, destination):
    source_uri = Path(source).resolve().as_uri() + "?mode=ro"
    source_connection = sqlite3.connect(source_uri, uri=True, timeout=10)
    destination_connection = sqlite3.connect(destination, timeout=10)
    try:
        source_connection.execute("PRAGMA query_only=ON")
        source_connection.backup(destination_connection)
        mode = destination_connection.execute("PRAGMA journal_mode=DELETE").fetchone()[0]
        if mode.lower() != "delete":
            raise OSError("cannot finalize SQLite snapshot in rollback-journal mode")
    finally:
        destination_connection.close()
        source_connection.close()
    os.chmod(destination, stat.S_IMODE(os.stat(source).st_mode))
    _verify_database(destination)
    if os.path.lexists(destination + "-wal") or os.path.lexists(destination + "-shm"):
        raise OSError("SQLite snapshot unexpectedly retained destination sidecars")


def _copy_tree(source, destination):
    shutil.copytree(source, destination, symlinks=False)
    _regular_or_directory(destination)


def _build_snapshot(entries, payload):
    os.mkdir(payload)
    for source, relative, kind in entries:
        destination = os.path.join(payload, relative)
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        if kind == "sqlite":
            _backup_database(source, destination)
        elif kind == "tree":
            _copy_tree(source, destination)
            if not _identical(source, destination):
                raise OSError("runtime tree verification failed: %s" % destination)
        else:
            _copy_file(source, destination)
            if not _identical(source, destination):
                raise OSError("runtime file verification failed: %s" % destination)
    for _, relative, kind in entries:
        if kind == "sqlite":
            _verify_database(os.path.join(payload, relative))


def _identical(left, right):
    if os.path.islink(left) or os.path.islink(right):
        return False
    left_info = os.lstat(left)
    right_info = os.lstat(right)
    if stat.S_IMODE(left_info.st_mode) != stat.S_IMODE(right_info.st_mode):
        return False
    if stat.S_ISDIR(left_info.st_mode) and stat.S_ISDIR(right_info.st_mode):
        left_names, right_names = sorted(os.listdir(left)), sorted(os.listdir(right))
        return left_names == right_names and all(
            _identical(os.path.join(left, name), os.path.join(right, name))
            for name in left_names)
    if not stat.S_ISREG(left_info.st_mode) or not stat.S_ISREG(right_info.st_mode):
        return False
    if left_info.st_size != right_info.st_size:
        return False
    with open(left, "rb") as left_file, open(right, "rb") as right_file:
        while True:
            left_chunk, right_chunk = left_file.read(1024 * 1024), right_file.read(1024 * 1024)
            if left_chunk != right_chunk:
                return False
            if not left_chunk:
                return True


def _common_dir(root):
    return os.path.join(root, ".git")


def ensure_runtime_ready(cwd):
    root = primary_checkout(cwd)
    common = _common_dir(root)
    destination = os.path.join(state_root(cwd), BOARD_DATABASE)
    if os.path.lexists(destination) and os.path.islink(destination):
        raise OSError("refusing symbolic link for runtime database: %s" % destination)
    if migration_entries(common) and not os.path.isfile(destination):
        raise OSError("legacy runtime state exists without its migrated board database; "
                      "run .opencode/skills/runtime-state/scripts/state.py migrate first")


def migrate(cwd, apply=False):
    root = primary_checkout(cwd)
    common = _common_dir(root)
    entries = migration_entries(common)
    if not entries:
        print("no legacy runtime state; nothing to migrate")
        return

    destination = os.path.join(root, STATE_DIR)
    with tempfile.TemporaryDirectory(prefix=".factory-state-migration-", dir=root) as staging:
        payload = os.path.join(staging, "payload")
        _build_snapshot(entries, payload)
        if os.path.lexists(destination):
            if not os.path.isdir(destination) or not _identical(payload, destination):
                raise OSError("refusing partial, extra, or non-identical existing state: %s" % destination)
            print("verified identical complete state: %s" % destination)
            return
        for source, relative, _ in entries:
            print("would copy: %s -> %s" % (source, os.path.join(destination, relative)))
        if not apply:
            print("dry run only; rerun with --apply to install the verified snapshot")
            return
        os.rename(payload, destination)
    print("migration verified and installed atomically; source remains untouched")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Resolve or explicitly migrate factory runtime state")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("path", help="print the clone-local state directory")
    migration = sub.add_parser("migrate", help="dry-run migration from Git metadata")
    migration.add_argument("--apply", action="store_true", help="install verified snapshot; never delete source")
    args = parser.parse_args(argv)
    try:
        if args.command == "path":
            print(state_root(os.getcwd()))
        else:
            migrate(os.getcwd(), args.apply)
    except (OSError, sqlite3.Error, subprocess.SubprocessError) as exc:
        print("runtime state refused: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
