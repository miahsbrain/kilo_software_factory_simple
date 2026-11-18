#!/usr/bin/env python3
"""Bootstrap source repositories or restore their ignored local factory tooling."""

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

from guard import bash_verdict, load_policy, pattern_matches, script_project_root


NAME = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
HARNESS = ("agent", "command", "skills", "policies")
LOCAL = ("/.kilo/", "/.devcontainer/", "/kilo.jsonc", "/AGENTS.md", "/docs/BOARD.md")
OUTPUTS = {".git", "__pycache__", "node_modules", "artifacts", ".tmp",
           ".playwright-mcp", ".playwright", "playwright-report", "test-results",
           "blob-report", ".vscode", ".DS_Store"}


def git(*args, cwd):
    result = subprocess.run(["git", *args], cwd=cwd, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        # Git hooks/config output can contain secrets; never print it.
        raise ValueError("Git {} failed (exit {})".format(args[0], result.returncode))
    return result.stdout.strip()


def real_path(path):
    if ".." in path.parts:
        raise ValueError("traversal is not supported")
    path = Path(os.path.abspath(path))
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("symlinks are not supported: " + str(path))
    return path


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate manifest key")
        result[key] = value
    return result


def read_services(root):
    path = real_path(root / "services.json")
    if not path.is_file():
        raise ValueError("missing regular tracked services.json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    except (json.JSONDecodeError, UnicodeError):
        raise ValueError("malformed services manifest") from None
    if not isinstance(data, dict) or set(data) != {"services"} or not isinstance(data["services"], list):
        raise ValueError("manifest must contain a services array")
    names, paths = set(), set()
    for service in data["services"]:
        if not isinstance(service, dict) or set(service) != {"name", "path", "git"}:
            raise ValueError("service needs only name, path and git ownership")
        name, path = service["name"], service["path"]
        if (not isinstance(name, str) or not NAME.fullmatch(name) or name == "control"
                or path != "apps/" + name or service["git"] not in ("separate", "project")
                or name in names or path in paths):
            raise ValueError("invalid or colliding service name/path/ownership")
        real_path(root / path)
        names.add(name)
        paths.add(path)
    return data


def encoded(data):
    return (json.dumps(data, indent=2) + "\n").encode("utf-8")


def repo_map(data):
    return {"control": ".", **{s["name"]: s["path"] for s in data["services"]
                             if s["git"] == "separate"}}


def excluded(relative):
    parts, name = relative.parts, relative.name
    return (any(part in OUTPUTS for part in parts)
            or any(parts[i] == ".kilo" and parts[i + 1] in
                   {"local", "qa-local", "worktrees"} for i in range(len(parts) - 1))
            or name == "agent-manager.json"
            or (name.startswith(".env") and name != ".env.example")
            or name in {".npmrc", ".git-credentials"}
            or name.endswith((".pyc", ".pem", ".key", ".p12"))
            or name.startswith("id_rsa"))


def collect(root, target, plan):
    real_path(root)
    if not root.is_dir():
        raise ValueError("missing source root: " + str(root))
    for directory, dirs, names in os.walk(root, followlinks=False):
        relative = Path(directory).relative_to(root)
        for name in list(dirs):
            output = target / relative / name
            if excluded(output):
                dirs.remove(name)
            else:
                real_path(Path(directory) / name)
        for name in names:
            output = target / relative / name
            if excluded(output):
                continue
            path = real_path(Path(directory) / name)
            if not path.is_file():
                raise ValueError("source must contain only regular files")
            if output in plan:
                raise ValueError("source output collision: " + str(output))
            plan[output] = path.read_bytes()


def local_plan(source):
    plan = {}
    for name in HARNESS:
        collect(source / ".kilo" / name, Path(".kilo") / name, plan)
    for relative in (".kilo/.gitignore", "kilo.jsonc"):
        path = real_path(source / relative)
        if not path.is_file():
            raise ValueError("missing regular source: " + relative)
        plan[Path(relative)] = path.read_bytes()
    collect(source / ".devcontainer", Path(".devcontainer"), plan)
    config_path = Path(".devcontainer/devcontainer.json")
    if any(Path(p) not in plan for p in (".devcontainer/devcontainer.json", ".devcontainer/Dockerfile", ".devcontainer/kilo-redact.sh")):
        raise ValueError("incomplete devcontainer source")
    config = json.loads(plan[config_path])
    # Workspace-relative tools/config, without the factory's global Git mutation or doctor.
    config["name"] = "Project Development"
    config["postCreateCommand"] = "install -m 0644 .devcontainer/kilo-redact.sh /home/node/.kilo-redact.sh"
    config["remoteEnv"]["KILO_CONFIG"] = "${containerWorkspaceFolder}/kilo.jsonc"
    plan[config_path] = encoded(config)
    return plan


def factory_template(source):
    template = real_path(source / "templates/project")
    if not template.is_dir():
        raise ValueError("restore/project source must be the factory checkout containing templates/project")
    if read_services(template) != {"services": []}:
        raise ValueError("template manifest must be blank")
    return template


def preflight(destination, plan):
    for relative, content in plan.items():
        output = real_path(destination / relative)
        if os.path.lexists(output) and (not output.is_file() or output.read_bytes() != content):
            raise ValueError("restore conflict; no files written: " + str(output))
        for parent in output.parents:
            if parent == destination.parent:
                break
            if parent.exists() and not parent.is_dir():
                raise ValueError("non-directory destination parent: " + str(parent))


def write_plan(destination, plan):
    for relative, content in plan.items():
        output = destination / relative
        if output.exists():
            continue
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("xb") as handle:
            handle.write(content)


def bootstrap_policy(source, files):
    policy = load_policy(str(real_path(source / ".kilo/policies/git-policy.json")))
    commands = (["git", "init"], ["git", "add", "--", *sorted(files)],
                ["git", "commit", "-m", "chore: initialize source repository"])
    for args in commands:
        command = shlex.join(args)
        if bash_verdict(policy, command)[0] not in ("allow", "ask"):
            raise ValueError("guard refused " + command.split(" --")[0] + "; nothing created")
        # Only these two context checks have the approved new-repo exception.
        for rule in policy.get("context", []):
            if (any(pattern_matches(command, p) for p in rule.get("applies_to", []))
                    and rule.get("check") not in ("protected_branch", "in_worktree")
                    and rule.get("action", "deny") == "deny"):
                raise ValueError("guard refused bootstrap context rule; nothing created")


def identity(cwd):
    try:
        git("var", "GIT_AUTHOR_IDENT", cwd=cwd)
        git("var", "GIT_COMMITTER_IDENT", cwd=cwd)
    except ValueError:
        raise ValueError("Git identity unavailable; configure your identity, then retry; nothing created") from None


def initial_commit(destination, files):
    # Called only immediately after this invocation creates a previously absent repo.
    if not (destination / ".git").is_dir() or git("ls-files", cwd=destination):
        raise ValueError("initial commit requires a fresh empty index")
    result = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=destination,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        raise ValueError("initial commit requires unborn HEAD")
    git("add", "--", *sorted(files), cwd=destination)
    git("commit", "-m", "chore: initialize source repository", cwd=destination)
    if git("rev-list", "--count", "HEAD", cwd=destination) != "1":
        raise ValueError("unexpected initial history; inspect retained state")


def project(source, destination, allow_outside=False):
    root = real_path(Path.cwd())
    source = real_path(source)
    if root != source:
        raise ValueError("run project mode from the factory checkout root")
    resolved = destination.resolve()
    print("Current working directory: {}\nFactory source: {}\nResolved destination: {}".format(
        root, source, resolved), file=sys.stderr)
    if root not in resolved.parents and resolved != root and not allow_outside:
        raise ValueError("outside destination: {}; ASK for explicit user approval first, then use "
                         "--allow-outside; never infer a path from a product or service name; "
                         "nothing created".format(resolved))
    destination = real_path(destination)
    if os.path.lexists(destination):
        raise ValueError("destination already exists; never overwrite or reinitialize")
    if not destination.parent.is_dir():
        raise ValueError("destination parent must be an existing real directory")
    template = factory_template(source)
    plan = {}
    collect(template, Path("."), plan)
    plan.update(local_plan(source))
    plan[Path(".kilo/repos.json")] = encoded({"control": "."})
    files = [str(p) for p in plan if p.parts[0] not in (".kilo", ".devcontainer")
             and str(p) not in ("AGENTS.md", "kilo.jsonc", "docs/BOARD.md")]
    bootstrap_policy(source, files)
    identity(destination.parent)
    preflight(destination, plan)
    destination.mkdir()
    try:
        write_plan(destination, plan)
        (destination / "apps").mkdir()
        git("init", cwd=destination)
        initial_commit(destination, files)
    except (OSError, ValueError) as error:
        raise ValueError(str(error) + "; partial state retained at " + str(destination)) from None
    return destination


def app(source, root, name, git_mode):
    root = real_path(root)
    real_path(root / ".git")
    if git_mode not in ("separate", "project") or not NAME.fullmatch(name) or name == "control":
        raise ValueError("choose separate/project Git and a meaningful lowercase kebab-case service name; not control")
    if (root / "templates/project").exists():
        raise ValueError("run app mode from the project control root, not the factory")
    if git("rev-parse", "--show-toplevel", cwd=root) != str(root) or not (root / ".git").is_dir():
        raise ValueError("app creation requires the primary project control checkout")
    data = read_services(root)
    relative = "apps/" + name
    if any(s["name"] == name or s["path"] == relative for s in data["services"]):
        raise ValueError("service name/path collision")
    destination = real_path(root / relative)
    if os.path.lexists(destination):
        raise ValueError("app destination already exists; never overwrite or reinitialize")
    apps = destination.parent
    if apps.exists() and not apps.is_dir():
        raise ValueError("apps must be a real directory")
    ignore_path = real_path(root / ".gitignore")
    if not ignore_path.is_file():
        raise ValueError("project .gitignore must be a regular file; nothing created")
    project_ignores = ignore_path.read_text(encoding="utf-8")
    ignore_rules = "".join(line for line in project_ignores.splitlines(keepends=True)
                           if line.strip() != "apps/*/" and not line.startswith("!/apps/"))
    ignore_rules += "\n" + "\n".join(LOCAL) + "\n"
    map_path = real_path(root / ".kilo/repos.json")
    if not map_path.is_file() or json.loads(map_path.read_text()) != repo_map(data):
        raise ValueError("local repo map differs from manifest; restore project tooling first")
    if git_mode == "separate":
        bootstrap_policy(source, [".gitignore"])
        if root != source:
            bootstrap_policy(root, [".gitignore"])
        identity(root)
    apps.mkdir(exist_ok=True)
    destination.mkdir()
    try:
        (destination / ".gitignore").write_text(ignore_rules, encoding="utf-8")
        if git_mode == "separate":
            git("init", cwd=destination)
            initial_commit(destination, [".gitignore"])
        else:
            ignore_path.write_text(project_ignores + "\n!/" + relative + "/\n", encoding="utf-8")
        data["services"].append({"name": name, "path": relative, "git": git_mode})
        (root / "services.json").write_bytes(encoded(data))
        map_path.write_bytes(encoded(repo_map(data)))
    except (OSError, ValueError) as error:
        raise ValueError(str(error) + "; partial state retained at " + str(destination)
                         + "; inspect services.json and local repo map before retrying") from None
    return destination


def restore(source, destination, control=None):
    template = factory_template(source)
    # Validate complete factory sources even when an app inherits its project's harness.
    factory_local = local_plan(source)
    destination = real_path(destination)
    real_path(destination / ".git")
    if (destination == source or (destination / "templates/project").exists()):
        raise ValueError("restore destination must not be a factory checkout or its worktrees")
    if (not destination.is_dir() or not (destination / ".git").is_dir()
            or git("rev-parse", "--show-toplevel", cwd=destination) != str(destination)):
        raise ValueError("restore requires an existing primary repository checkout, not a linked worktree")
    if control is None and (destination / "services.json").is_file():
        data = read_services(destination)
        plan = factory_local
        for relative in ("AGENTS.md", "docs/BOARD.md"):
            plan[Path(relative)] = real_path(template / relative).read_bytes()
        plan[Path(".kilo/repos.json")] = encoded(repo_map(data))
        for service in data["services"]:
            checkout = destination / service["path"]
            if not checkout.is_dir() or (service["git"] == "separate" and not (checkout / ".git").is_dir()):
                print("Missing service checkout: " + service["path"] + " (" + service["git"] + ")")
    else:
        if control is None:
            candidate = destination.parent.parent
            if destination.parent.name != "apps" or not (candidate / "services.json").is_file():
                raise ValueError("separate-app restore requires --project <control-path>")
            control = candidate
        control = real_path(control)
        real_path(control / ".git")
        if (not (control / ".git").is_dir() or (control / "templates/project").exists()
                or git("rev-parse", "--show-toplevel", cwd=control) != str(control)):
            raise ValueError("--project must name the primary project control checkout")
        data = read_services(control)
        if not any(s["git"] == "separate" and control / s["path"] == destination for s in data["services"]):
            raise ValueError("app checkout must occupy its separate services.json path under --project; clone it there first")
        if json.loads(real_path(control / ".kilo/repos.json").read_text()) != repo_map(data):
            raise ValueError("restore the control project first; local repo map is missing or stale")
        # Open the control-level container: an app-only mount hides its parent context.
        plan = {p: content for p, content in local_plan(control).items()
                if p.parts[0] != ".devcontainer"}
        plan[Path("AGENTS.md")] = ("# Local Service Tooling\n\n"
            "Inherit the working agreement, board and lifecycle tools from `../../` "
            "relative to this service root. Open the control project's `../../.devcontainer/` "
            "in the editor, then work in `apps/" + destination.name + "` inside that container. "
            "The control container sets KILO_CONFIG to its mounted workspace config; "
            "lifecycle tools discover control by walking ancestors to its board and repo map. "
            "No app-only devcontainer or host-absolute control pointer is generated. "
            "This generated local file is ignored; service source and product docs remain tracked.\n").encode()
    tracked = set(git("ls-files", "-z", cwd=destination).split("\0"))
    if any(str(path) in tracked for relative in plan for path in (relative, *relative.parents)):
        raise ValueError("restore outputs are tracked source; migrate explicitly first; no files written")
    # Excludes are clone-local. Never rewrite source .gitignore, index, HEAD or config.
    exclude = real_path(destination / ".git/info/exclude")
    if exclude.exists() and not exclude.is_file():
        raise ValueError("local exclude must be a regular file; no files written")
    existing = exclude.read_bytes() if exclude.is_file() else b""
    patterns = existing.decode("utf-8").splitlines()
    missing = [p for p in LOCAL if p not in patterns]
    updated = existing + (b"\n# Local factory tooling\n" + ("\n".join(missing) + "\n").encode() if missing else b"")
    preflight(destination, plan)
    write_plan(destination, plan)
    if updated != existing:
        exclude.parent.mkdir(parents=True, exist_ok=True)
        exclude.write_bytes(updated)
    if control is not None:
        print("Service tooling restored without an app devcontainer; open the control project's "
              "../../.devcontainer/ and work in apps/" + destination.name +
              " inside its container (paths relative to the service root).")
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    project_parser = modes.add_parser("project", help="create a new project and one initial source commit")
    project_parser.add_argument("--destination", type=Path)
    project_parser.add_argument("--allow-outside", action="store_true",
                                help="permit an external destination only after explicit user approval")
    application = modes.add_parser("app", help="create apps/<meaningful-service-name>")
    application.add_argument("name")
    application.add_argument("--git", choices=("separate", "project"), required=True)
    restoration = modes.add_parser("restore", help="rehydrate ignored tooling from this factory checkout")
    restoration.add_argument("--destination", type=Path, required=True)
    restoration.add_argument("--project", type=Path, help="control checkout for a separate service")
    args = parser.parse_args(argv)
    try:
        if not shutil.which("git"):
            raise ValueError("Git is required; nothing created")
        if any(key.startswith("GIT_") for key in os.environ):
            raise ValueError("unset GIT_* environment overrides before bootstrap")
        source = real_path(Path(script_project_root()))
        root = real_path(Path.cwd())
        if args.mode == "project":
            if root != source:
                raise ValueError("run project mode from the factory checkout root")
            result = project(source, args.destination or root / "project", args.allow_outside)
        elif args.mode == "app":
            result = app(source, root, args.name, args.git)
        else:
            result = restore(source, args.destination, args.project)
        suffix = "tooling restored; source/index/HEAD unchanged" if args.mode == "restore" else (
            "one initial source commit created" if args.mode == "project" or args.git == "separate"
            else "source belongs to control Git; no staging or commit")
        print("{}: {} at {}".format(args.mode, suffix, result))
        return 0
    except (OSError, ValueError) as error:
        print("bootstrap: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
