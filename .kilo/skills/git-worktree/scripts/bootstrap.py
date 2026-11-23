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


def app(source, root, name, git_mode, role):
    if (not isinstance(role, str) or not NAME.fullmatch(role)
            or not isinstance(name, str) or not name.endswith("-" + role)
            or not NAME.fullmatch(name[:-(len(role) + 1)])):
        raise ValueError("service name must be <product>-<role> with a valid nonempty lowercase "
                         "kebab-case product prefix and explicit lowercase kebab-case role")
    if git_mode not in ("separate", "project"):
        raise ValueError("choose separate/project Git ownership")
    root = real_path(root)
    if root != real_path(Path.cwd()):
        raise ValueError("run app registration from the assigned control source worktree root")
    real_path(root / ".git")
    if (root / "templates/project").exists():
        raise ValueError("run app mode from the project control root, not the factory")
    import worktree
    if git("rev-parse", "--show-toplevel", cwd=root) != str(root):
        raise ValueError("app registration requires the assigned control worktree root")
    primary = real_path(Path(worktree.main_checkout_root(str(root))))
    if root == primary or not (root / ".git").is_file():
        raise ValueError("app registration requires an assigned linked control source worktree; "
                         "create/resume the assigned control worktree first; nothing created")
    real_path(primary / ".git")
    if ((primary / "templates/project").exists() or not (primary / ".git").is_dir()
            or worktree.common_dir(str(root)) != worktree.common_dir(str(primary))):
        raise ValueError("source is not a linked project control worktree")
    board = worktree.load_board_module(str(primary))
    table, error = board.read_table(str(real_path(primary / "docs/BOARD.md")))
    if table is None:
        raise ValueError(error)
    column = board.field_index(table, "branch-worktree")
    if column is None:
        raise ValueError("control board has no workspace assignments")
    assigned = False
    for index in table["rows"]:
        cells = board.cell_texts(table["lines"], index)
        if cells[worktree.STATUS_INDEX] in ("Merged", "Dropped"):
            continue
        items = worktree.task_workspaces(str(primary), str(primary), "control", cells[0],
                                        cells[column], selected=str(root))
        if any(item["path"] == str(root) and item["linked"] for item in items):
            assigned = True
    record = worktree.local_state(str(primary))["workspaces"].get(str(root), {})
    if (not assigned or record.get("error") or record.get("control") != str(primary)
            or record.get("repo") != str(primary) or record.get("repo_id") != "control"):
        raise ValueError("create/resume the assigned linked control worktree first; nothing created")
    for checkout in (root, primary):
        git("ls-files", "--error-unmatch", "--", "services.json", ".gitignore", cwd=checkout)
    data = read_services(root)
    primary_data = read_services(primary)
    relative = "apps/" + name
    known = {}
    for service in primary_data["services"] + data["services"]:
        previous = known.setdefault(service["name"], service)
        if previous != service:
            raise ValueError("conflicting service manifest name/path/ownership; nothing created")
    if name in known:
        raise ValueError("service name/path collision")
    destination = real_path((primary if git_mode == "separate" else root) / relative)
    print("Control source: {}\nCanonical control: {}\nSelected role: {}\nFull service target: {}".format(
        root, primary, role, destination), file=sys.stderr)
    for checkout in (root, primary):
        target = real_path(checkout / relative)
        if os.path.lexists(target):
            raise ValueError("app destination already exists; never overwrite or reinitialize")
        tracked = set(git("ls-files", "-z", cwd=checkout).split("\0"))
        protected = {relative, "apps", ".kilo", ".kilo/repos.json"}
        if (tracked & protected or any(path.startswith(relative + "/")
                                       or path.startswith(".kilo/repos.json/") for path in tracked)):
            raise ValueError("app target or operational map has tracked paths/ancestors; nothing created")
        git("check-ignore", "-q", "--", ".kilo/repos.json", cwd=checkout)
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
    map_path = real_path(primary / ".kilo/repos.json")
    source_map = real_path(root / ".kilo/repos.json")
    merged = {"control": "."}
    for path in (map_path, source_map):
        if not path.exists() and path == source_map:
            continue
        if not path.is_file():
            raise ValueError("missing regular local repo map; restore project tooling first")
        mapping = json.loads(path.read_text(), object_pairs_hook=unique_object)
        if not isinstance(mapping, dict) or mapping.get("control") != ".":
            raise ValueError("invalid control repo map; nothing created")
        for key, value in mapping.items():
            if key == "control":
                continue
            if (not NAME.fullmatch(key) or value != "apps/" + key
                    or (key in known and known[key]["git"] != "separate")):
                raise ValueError("conflicting repo map name/path/ownership; nothing created")
            target = real_path(primary / value)
            if (not (real_path(target / ".git")).is_dir()
                    or git("rev-parse", "--show-toplevel", cwd=target) != str(target)
                    or Path(worktree.main_checkout_root(str(target))) != target):
                raise ValueError("stale or foreign repo map target; nothing created")
            merged[key] = value
    for service in known.values():
        if service["git"] == "separate" and service["name"] not in merged:
            raise ValueError("local repo map differs from manifest; restore project tooling first")
    if name in merged:
        raise ValueError("service name/path collision with another source registration")
    real_path(source_map.parent)
    if source_map.parent.exists() and not source_map.parent.is_dir():
        raise ValueError("source .kilo must be a real directory")
    if git_mode == "separate":
        bootstrap_policy(source, [".gitignore"])
        if primary != source:
            bootstrap_policy(primary, [".gitignore"])
        if root != source and (root / ".kilo/policies/git-policy.json").exists():
            bootstrap_policy(root, [".gitignore"])
        identity(primary)
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
        if git_mode == "separate":
            merged[name] = relative
        map_path.write_bytes(encoded(merged))
        source_map.parent.mkdir(exist_ok=True)
        source_map.write_bytes(encoded(merged))
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
    application = modes.add_parser("app", help="create apps/<product-role> from approved service intent")
    application.add_argument("name")
    application.add_argument("--role", required=True, help="explicit lowercase kebab-case role; name must end in -<role>")
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
            result = app(source, root, args.name, args.git, args.role)
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
