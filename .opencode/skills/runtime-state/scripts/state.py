#!/usr/bin/env python3
"""Resolve and explicitly migrate clone-local factory runtime state."""
import argparse
import hashlib
import os
import shutil
import stat
import subprocess
import sys

STATE_DIR = ".factory-state"
BOARD_FILES = ("factory-board.sqlite3", "factory-board.sqlite3-wal",
               "factory-board.sqlite3-shm", "factory-board-export.md",
               "factory-board-legacy-backup.md")


def primary_checkout(cwd):
    result = subprocess.run(
        ["git", "-C", cwd, "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True, text=True, timeout=10)
    common = result.stdout.strip()
    if result.returncode or not common or not os.path.isabs(common):
        raise OSError("cannot resolve the absolute Git common directory")
    common = os.path.realpath(common)
    if not os.path.isdir(common):
        raise OSError("Git common directory is not an accessible directory")
    root = os.path.dirname(common)
    if os.path.basename(common) != ".git":
        raise OSError("Git common directory does not identify a primary checkout")
    check = subprocess.run(
        ["git", "-C", root, "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True, text=True, timeout=10)
    if check.returncode or os.path.realpath(check.stdout.strip()) != common:
        raise OSError("cannot verify primary checkout from Git common directory")
    return os.path.realpath(root)


def state_root(cwd):
    return os.path.join(primary_checkout(cwd), STATE_DIR)


def migration_entries(common):
    entries = [(name, name) for name in BOARD_FILES]
    reviews = os.path.join(common, "reviews")
    if os.path.isdir(reviews):
        entries.append(("reviews", "reviews"))
    cleanup = os.path.join(common, "cleanup-wt")
    if os.path.lexists(cleanup):
        entries.append(("cleanup-wt", os.path.join("cleanup-wt", "control")))
    return [(source, destination) for source, destination in entries
            if os.path.lexists(os.path.join(common, source))]


def digest(path):
    value = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def identical(source, destination):
    if os.path.islink(source) or os.path.islink(destination):
        return False
    if os.path.isdir(source):
        if not os.path.isdir(destination):
            return False
        if stat.S_IMODE(os.stat(source).st_mode) != stat.S_IMODE(os.stat(destination).st_mode):
            return False
        source_names = sorted(os.listdir(source))
        dest_names = sorted(os.listdir(destination))
        return source_names == dest_names and all(
            identical(os.path.join(source, name), os.path.join(destination, name))
            for name in source_names)
    return (os.path.isfile(source) and os.path.isfile(destination)
            and stat.S_IMODE(os.stat(source).st_mode) == stat.S_IMODE(os.stat(destination).st_mode)
            and os.path.getsize(source) == os.path.getsize(destination)
            and digest(source) == digest(destination))


def reject_symlinks(path):
    if os.path.islink(path):
        raise OSError("refusing symbolic link in runtime state: %s" % path)
    if os.path.isdir(path):
        for name in os.listdir(path):
            reject_symlinks(os.path.join(path, name))


def migration_plan(common, destination):
    plan = []
    conflicts = []
    for relative_source, relative_destination in migration_entries(common):
        source = os.path.join(common, relative_source)
        target = os.path.join(destination, relative_destination)
        if os.path.islink(destination):
            raise OSError("refusing symbolic link for runtime state directory: %s" % destination)
        parent = os.path.dirname(target)
        while parent.startswith(destination + os.sep):
            if os.path.islink(parent):
                raise OSError("refusing symbolic link in runtime state destination: %s" % parent)
            parent = os.path.dirname(parent)
        if os.path.islink(source) or not (os.path.isfile(source) or os.path.isdir(source)):
            raise OSError("refusing non-regular runtime state: %s" % source)
        reject_symlinks(source)
        if os.path.lexists(target) and not identical(source, target):
            conflicts.append(target)
        plan.append((source, target))
    return plan, conflicts


def migrate(cwd, apply=False):
    root = primary_checkout(cwd)
    common = os.path.realpath(os.path.join(root, ".git"))
    destination = os.path.join(root, STATE_DIR)
    plan, conflicts = migration_plan(common, destination)
    if conflicts:
        raise OSError("refusing non-identical destination: %s" % ", ".join(conflicts))
    for source, target in plan:
        print(("verified identical" if os.path.lexists(target) else
               "would copy" if not apply else "copied") + ": %s -> %s" % (source, target))
    if not apply:
        print("dry run only; rerun with --apply to copy. Source remains untouched.")
        return
    for source, target in plan:
        if os.path.lexists(target):
            continue
        os.makedirs(os.path.dirname(target), exist_ok=True)
        if os.path.isdir(source):
            shutil.copytree(source, target, symlinks=False)
        else:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            descriptor = os.open(target, flags, 0o600)
            try:
                with os.fdopen(descriptor, "wb") as output, open(source, "rb") as input_file:
                    shutil.copyfileobj(input_file, output)
                shutil.copystat(source, target)
            except Exception:
                os.unlink(target)
                raise
        if not identical(source, target):
            raise OSError("copy verification failed: %s" % target)
    print("migration verified; source remains untouched")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Resolve or explicitly migrate factory runtime state")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("path", help="print the clone-local state directory")
    migration = sub.add_parser("migrate", help="dry-run migration from Git metadata")
    migration.add_argument("--apply", action="store_true", help="copy and verify; never delete source")
    args = parser.parse_args(argv)
    try:
        if args.command == "path":
            print(state_root(os.getcwd()))
        else:
            migrate(os.getcwd(), args.apply)
    except (OSError, subprocess.SubprocessError) as exc:
        print("runtime state refused: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
