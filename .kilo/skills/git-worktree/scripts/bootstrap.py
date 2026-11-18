#!/usr/bin/env python3
"""Create a project control repository or an app with an explicit Git ownership choice."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from guard import script_project_root


NAME = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
HARNESS = ("agent", "command", "skills", "policies")
OUTPUTS = {".git", "__pycache__", "node_modules", "artifacts", ".tmp",
           ".playwright-mcp", ".playwright", "playwright-report", "test-results",
           "blob-report", ".vscode", ".DS_Store"}


def git(*args, cwd):
    result = subprocess.run(["git", *args], cwd=cwd, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        # Do not echo subprocess output: local Git hooks/config may contain secrets.
        raise ValueError("Git {} failed (exit {})".format(args[0], result.returncode))
    return result.stdout.strip()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate repository ID")
        result[key] = value
    return result


def read_map(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("repository map must be a regular file")
    try:
        repos = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    except (json.JSONDecodeError, UnicodeError):
        raise ValueError("malformed repository map") from None
    if not isinstance(repos, dict) or repos.get("control") != ".":
        raise ValueError("repository map must contain control: .")
    paths = set()
    for name, path in repos.items():
        if not NAME.fullmatch(name) or not isinstance(path, str):
            raise ValueError("invalid repository ID/path")
        if name != "control" and not re.fullmatch(r"apps/[a-z][a-z0-9]*(?:-[a-z0-9]+)*", path):
            raise ValueError("application map paths must be apps/<name>")
        if path in paths:
            raise ValueError("duplicate repository path")
        paths.add(path)
    return repos


def excluded(relative):
    parts = relative.parts
    name = relative.name
    return (any(part in OUTPUTS for part in parts)
            or any(parts[i] == ".kilo" and parts[i + 1] in
                   {"local", "qa-local", "worktrees"} for i in range(len(parts) - 1))
            or name == "agent-manager.json"
            or (name.startswith(".env") and name != ".env.example")
            or name in {".npmrc", ".git-credentials"}
            or name.endswith((".pyc", ".pem", ".key", ".p12"))
            or name.startswith("id_rsa"))


def project(source, destination):
    # lexists also refuses dangling symlinks; resolve only after checking the leaf.
    if os.path.lexists(destination):
        raise ValueError("destination already exists; never overwrite or reinitialize")
    if ".." in destination.parts:
        raise ValueError("destination must not contain traversal")
    if not destination.parent.is_dir() or any(path.is_symlink() for path in destination.parents):
        raise ValueError("destination parent must be an existing real directory")
    destination = destination.parent.resolve() / destination.name
    if destination == source or source in destination.parents and destination != source / "project":
        raise ValueError("inside the factory only its project/ destination is allowed")
    template = source / "templates/project"
    if template.is_symlink() or (source / ".kilo").is_symlink():
        raise ValueError("source roots must not be symlinks")
    if read_map(template / ".kilo/repos.json") != {"control": "."}:
        raise ValueError("template map must be control-only")
    required = [template / "AGENTS.md", template / ".gitignore",
                template / "docs/BOARD.md", source / ".kilo/.gitignore",
                source / "kilo.jsonc"]
    roots = [(template, Path("."))]
    for name in HARNESS:
        directory = source / ".kilo" / name
        if not directory.is_dir() or directory.is_symlink():
            raise ValueError("missing regular harness directory: " + name)
        roots.append((directory, Path(".kilo") / name))
    if any(not path.is_file() or path.is_symlink() for path in required):
        raise ValueError("missing regular template/config prerequisite")
    files = []
    for root, target in roots:
        for directory, dirs, names in os.walk(root, followlinks=False):
            relative = Path(directory).relative_to(root)
            for name in list(dirs):
                path = Path(directory) / name
                if excluded(target / relative / name):
                    dirs.remove(name)
                elif path.is_symlink():
                    raise ValueError("source symlinks are not supported")
            for name in names:
                path = Path(directory) / name
                output = target / relative / name
                if excluded(output):
                    continue
                if path.is_symlink() or not path.is_file():
                    raise ValueError("source must contain only regular files")
                files.append((path, output))
    files.extend((path, Path(path.relative_to(source))) for path in required[-2:])
    # Every source/path check above precedes the first destination write.
    destination.mkdir()
    try:
        for path, relative in files:
            output = destination / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, output)
        (destination / "apps").mkdir()
        git("init", cwd=destination)
    except (OSError, ValueError):
        raise ValueError("project bootstrap failed; partial state retained at " + str(destination)) from None
    return destination


def app(source, root, name, git_mode):
    if git_mode not in ("separate", "project"):
        raise ValueError("choose app Git ownership: separate or project")
    if not NAME.fullmatch(name) or name == "control":
        raise ValueError("app name must be lowercase kebab-case, starting with a letter; not control")
    if root != source or (root / "templates/project").exists():
        raise ValueError("run app mode from the project control root, not the factory or an app")
    if git("rev-parse", "--show-toplevel", cwd=root) != str(root):
        raise ValueError("project control root must be an initialized Git repository")
    map_path = root / ".kilo/repos.json"
    repos = read_map(map_path)
    relative = "apps/" + name
    if name in repos or relative in repos.values():
        raise ValueError("repository ID/path collision")
    apps = root / "apps"
    if apps.is_symlink() or (apps.exists() and not apps.is_dir()):
        raise ValueError("apps must be a real directory")
    destination = apps / name
    if os.path.lexists(destination):
        raise ValueError("app destination already exists; never overwrite or reinitialize")
    temporary = map_path.with_name("repos.json.bootstrap-tmp")
    if os.path.lexists(temporary):
        raise ValueError("repository map temporary path already exists; inspect retained state")
    ignore_path = root / ".gitignore"
    if ignore_path.is_symlink() or not ignore_path.is_file():
        raise ValueError("project .gitignore must be a regular file; nothing created")
    # Reuse current project protections without hiding app source under apps/.
    project_ignores = ignore_path.read_text(encoding="utf-8")
    ignore_rules = "".join(line for line in project_ignores.splitlines(keepends=True)
                           if line.strip() != "apps/*/")
    apps.mkdir(exist_ok=True)
    destination.mkdir()
    try:
        (destination / ".gitignore").write_text(ignore_rules, encoding="utf-8")
        if git_mode == "separate":
            git("init", cwd=destination)
            repos[name] = relative
            # Replace only a fully written map; failed initialization leaves it unchanged.
            with temporary.open("x", encoding="utf-8") as handle:
                handle.write(json.dumps(repos, indent=2) + "\n")
            temporary.replace(map_path)
        else:
            # Unignore only this directory, not its contents' secret/runtime rules.
            ignore_path.write_text(project_ignores + "\n!/" + relative + "/\n", encoding="utf-8")
    except (OSError, ValueError):
        raise ValueError("app bootstrap failed; partial state retained at " + str(destination)
                         + "; inspect repository map before retrying") from None
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    control = modes.add_parser("project", help="copy the factory template and complete harness")
    control.add_argument("--destination", type=Path, help="new path; default: caller root/project")
    application = modes.add_parser("app", help="create apps/<name> with explicit Git ownership")
    application.add_argument("name")
    application.add_argument("--git", choices=("separate", "project"), required=True,
                             help="separate app repository or source tracked by project Git")
    args = parser.parse_args(argv)
    try:
        if not shutil.which("git"):
            raise ValueError("Git is required; nothing created")
        # Git environment overrides could initialize or inspect a different repository.
        if any(key.startswith("GIT_") for key in os.environ):
            raise ValueError("unset GIT_* environment overrides before bootstrap")
        source = Path(script_project_root()).resolve()
        root = Path.cwd().resolve()
        if args.mode == "project" or args.git == "separate":
            policy = subprocess.run(
                [sys.executable, str(source / ".kilo/skills/git-worktree/scripts/guard.py"),
                 "check-git", "--", "git init"], cwd=root,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Scoped init consent accepts ASK (3), never hard denials/errors.
            if policy.returncode not in (0, 3):
                raise ValueError("guard refused git init (exit {}); nothing created".format(policy.returncode))
        if args.mode == "project":
            if root != source:
                raise ValueError("run project mode from the factory checkout root")
            destination = args.destination or root / "project"
            if not destination.is_absolute():
                destination = root / destination
            result = project(source, destination)
        else:
            result = app(source, root, args.name, args.git)
        print("Initialized {} at {}; no files staged or committed".format(args.mode, result))
        return 0
    except (OSError, ValueError) as error:
        print("bootstrap: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
