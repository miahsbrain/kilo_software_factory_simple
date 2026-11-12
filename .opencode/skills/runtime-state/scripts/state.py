#!/usr/bin/env python3
"""Resolve and explicitly migrate clone-local factory runtime state."""
import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

STATE_DIR = ".factory-state"
BOARD_DATABASE = "factory-board.sqlite3"
COMPLETION_MARKER = ".migration-complete.json"
COMPLETION_FORMAT = "factory-runtime-state-v1"
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


def _file_metadata(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size,
            info.st_atime_ns, info.st_mtime_ns, info.st_ctime_ns)


def _readonly_snapshot_flags():
    return (os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NOATIME", 0))


def _source_file_snapshot(path):
    descriptor = os.open(path, _readonly_snapshot_flags())
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        path_before = os.lstat(path)
        if (not stat.S_ISREG(before.st_mode) or os.path.islink(path)
                or _file_metadata(before) != _file_metadata(path_before)):
            raise OSError("SQLite source changed while opening snapshot file: %s" % path)
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
        after = os.fstat(stream.fileno())
        path_after = os.lstat(path)
    if (_file_metadata(before) != _file_metadata(after)
            or _file_metadata(after) != _file_metadata(path_after)):
        raise OSError("SQLite source changed while reading snapshot file: %s" % path)
    return _file_metadata(after), digest.hexdigest()


def _copy_snapshot_file(source, destination):
    source_descriptor = os.open(source, _readonly_snapshot_flags())
    destination_descriptor = None
    try:
        source_file = os.fdopen(source_descriptor, "rb")
        source_descriptor = None
        with source_file:
            before = os.fstat(source_file.fileno())
            path_before = os.lstat(source)
            if (not stat.S_ISREG(before.st_mode) or os.path.islink(source)
                    or _file_metadata(before) != _file_metadata(path_before)):
                raise OSError("SQLite source changed while copying snapshot file: %s" % source)
            destination_descriptor = os.open(
                destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            digest = hashlib.sha256()
            with os.fdopen(destination_descriptor, "wb") as output:
                destination_descriptor = None
                for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
                    output.write(chunk)
                    digest.update(chunk)
                output.flush()
                os.fsync(output.fileno())
            after = os.fstat(source_file.fileno())
            path_after = os.lstat(source)
        if (_file_metadata(before) != _file_metadata(after)
                or _file_metadata(after) != _file_metadata(path_after)):
            raise OSError("SQLite source changed while copying snapshot file: %s" % source)
        return _file_metadata(after), digest.hexdigest()
    except BaseException:
        if destination_descriptor is not None:
            os.close(destination_descriptor)
        if os.path.lexists(destination):
            os.unlink(destination)
        raise
    finally:
        if source_descriptor is not None:
            os.close(source_descriptor)


def _snapshot_sqlite_database(source, private_directory):
    """Copy SQLite files read-only; all source writers must be stopped first."""
    os.mkdir(private_directory)
    sources = [source]
    sources.extend(source + suffix for suffix in ("-wal", "-shm")
                   if os.path.lexists(source + suffix))
    before = {path: _source_file_snapshot(path) for path in sources}
    copied = {}
    for path in sources:
        target = os.path.join(private_directory, os.path.basename(path))
        copied[path] = _copy_snapshot_file(path, target)
    current_sources = [source]
    current_sources.extend(source + suffix for suffix in ("-wal", "-shm")
                           if os.path.lexists(source + suffix))
    after = {path: _source_file_snapshot(path) for path in current_sources}
    if (sources != current_sources or before != after
            or any(before[path] != copied[path] for path in sources)):
        raise OSError("SQLite source changed during snapshot; stop all writers and retry")
    source_mode = stat.S_IMODE(before[source][0][2])
    return os.path.join(private_directory, os.path.basename(source)), source_mode


def _backup_database(source, destination, source_mode):
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
    os.chmod(destination, source_mode)
    _verify_database(destination)
    if os.path.lexists(destination + "-wal") or os.path.lexists(destination + "-shm"):
        raise OSError("SQLite snapshot unexpectedly retained destination sidecars")


def _copy_tree(source, destination):
    shutil.copytree(source, destination, symlinks=True)
    _regular_or_directory(destination)


def _build_snapshot(entries, payload, staging):
    os.mkdir(payload)
    for source, relative, kind in entries:
        destination = os.path.join(payload, relative)
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        if kind == "sqlite":
            sqlite_source, source_mode = _snapshot_sqlite_database(
                source, os.path.join(staging, "sqlite-source"))
            _backup_database(sqlite_source, destination, source_mode)
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
    _write_completion_marker(payload, entries)


def _snapshot_manifest(root):
    manifest = []
    for current, directories, files in os.walk(root):
        directories.sort()
        files.sort()
        for name in directories + files:
            path = os.path.join(current, name)
            relative = os.path.relpath(path, root)
            info = os.lstat(path)
            if stat.S_ISDIR(info.st_mode):
                item = {"path": relative, "kind": "directory"}
            elif stat.S_ISREG(info.st_mode):
                digest = hashlib.sha256()
                with open(path, "rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                item = {"path": relative, "kind": "file", "sha256": digest.hexdigest()}
            else:
                raise OSError("refusing non-regular staged state: %s" % path)
            manifest.append(item)
    return manifest


def _write_completion_marker(payload, entries):
    manifest = _snapshot_manifest(payload)
    encoded_manifest = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    value = {
        "format": COMPLETION_FORMAT,
        "snapshot_sha256": hashlib.sha256(encoded_manifest).hexdigest(),
        "database": any(relative == BOARD_DATABASE and kind == "sqlite"
                        for _, relative, kind in entries),
        "entries": manifest,
    }
    marker = os.path.join(payload, COMPLETION_MARKER)
    with open(marker, "x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def _read_completion_marker(root):
    marker = os.path.join(root, COMPLETION_MARKER)
    try:
        if os.path.islink(marker) or not stat.S_ISREG(os.lstat(marker).st_mode):
            return None
        with open(marker, encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, ValueError):
        return None
    if (not isinstance(value, dict) or value.get("format") != COMPLETION_FORMAT
            or not isinstance(value.get("database"), bool)
            or not isinstance(value.get("snapshot_sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", value["snapshot_sha256"])
            or not isinstance(value.get("entries"), list)):
        return None
    encoded_manifest = json.dumps(value["entries"], sort_keys=True,
                                  separators=(",", ":")).encode("utf-8")
    if hashlib.sha256(encoded_manifest).hexdigest() != value["snapshot_sha256"]:
        return None
    seen = set()
    for item in value["entries"]:
        if not isinstance(item, dict):
            return None
        relative = item.get("path")
        kind = item.get("kind")
        if (not isinstance(relative, str) or not relative or os.path.isabs(relative)
                or os.path.normpath(relative) != relative
                or ".." in relative.split(os.sep) or relative in seen
                or not isinstance(kind, str) or kind not in {"file", "directory"}):
            return None
        if (kind == "file" and (not isinstance(item.get("sha256"), str)
                                 or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]))):
            return None
        seen.add(relative)
        path = os.path.join(root, relative)
        if os.path.islink(path):
            return None
        try:
            info = os.lstat(path)
        except OSError:
            return None
        if ((kind == "file" and not stat.S_ISREG(info.st_mode))
                or (kind == "directory" and not stat.S_ISDIR(info.st_mode))):
            return None
    database_entry = next((item for item in value["entries"]
                           if item.get("path") == BOARD_DATABASE), None)
    if value["database"] != (database_entry is not None and database_entry.get("kind") == "file"):
        return None
    return value


def _source_snapshot_paths(entries):
    paths = set()
    for source, relative, kind in entries:
        if kind != "tree":
            paths.add(relative)
            continue
        for current, directories, files in os.walk(source):
            base = os.path.relpath(current, source)
            mapped = relative if base == "." else os.path.join(relative, base)
            paths.add(mapped)
            for name in directories + files:
                paths.add(os.path.join(mapped, name))
    return paths


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
    state_directory = state_root(cwd)
    if os.path.lexists(state_directory) and os.path.islink(state_directory):
        raise OSError("refusing symbolic link for runtime state directory: %s" % state_directory)
    destination = os.path.join(state_directory, BOARD_DATABASE)
    if os.path.lexists(destination) and os.path.islink(destination):
        raise OSError("refusing symbolic link for runtime database: %s" % destination)
    entries = migration_entries(common)
    if entries:
        marker = _read_completion_marker(state_directory)
        marker_paths = ({item["path"] for item in marker["entries"]}
                        if marker is not None else set())
        expected_paths = _source_snapshot_paths(entries)
        has_database = any(relative == BOARD_DATABASE and kind == "sqlite"
                           for _, relative, kind in entries)
        if (marker is None or not expected_paths.issubset(marker_paths)
                or marker["database"] != has_database
                or (has_database and not os.path.isfile(destination))):
            raise OSError("legacy runtime state exists without a complete verified destination; "
                          "run .opencode/skills/runtime-state/scripts/state.py migrate first")


def migrate(cwd, apply=False):
    root = primary_checkout(cwd)
    common = _common_dir(root)
    entries = migration_entries(common)
    if not entries:
        print("no legacy runtime state; nothing to migrate")
        return

    destination = os.path.join(root, STATE_DIR)
    if os.path.lexists(destination) and os.path.islink(destination):
        raise OSError("refusing symbolic link for runtime state destination: %s" % destination)
    with tempfile.TemporaryDirectory(prefix=".factory-state-migration-", dir=root) as staging:
        payload = os.path.join(staging, "payload")
        _build_snapshot(entries, payload, staging)
        if os.path.lexists(destination):
            _regular_or_directory(destination)
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
    migration = sub.add_parser(
        "migrate", help="migrate Git-metadata state after stopping all legacy DB writers")
    migration.add_argument("--apply", action="store_true",
                           help="install verified snapshot; never delete source")
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
