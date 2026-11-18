"""Bootstrap/restore tests operate only on disposable, identity-isolated repositories."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import bootstrap
import worktree


SOURCE = Path(__file__).resolve().parents[4]


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bootstrap-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.factory = self.base / "factory"
        self.factory.mkdir()
        self.home = self.base / "home"
        self.home.mkdir()
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update(HOME=str(self.home), XDG_CONFIG_HOME=str(self.home / "xdg"),
                        GIT_CONFIG_NOSYSTEM="1", PYTHONDONTWRITEBYTECODE="1")
        shutil.copytree(SOURCE / "templates", self.factory / "templates")
        for name in bootstrap.HARNESS:
            shutil.copytree(SOURCE / ".kilo" / name, self.factory / ".kilo" / name,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copytree(SOURCE / ".devcontainer", self.factory / ".devcontainer")
        for name in (".kilo/.gitignore", "kilo.jsonc"):
            shutil.copy2(SOURCE / name, self.factory / name)
        self.git(self.factory, "init")
        self.git(self.factory, "config", "--global", "user.name", "Bootstrap Fixture")
        self.git(self.factory, "config", "--global", "user.email", "fixture@example.invalid")

    def git(self, root, *args, ok=True):
        result = subprocess.run(["git", *args], cwd=root, env=self.env, text=True, capture_output=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def cli(self, root, *args, ok=True, script_root=None):
        env = {k: v for k, v in self.env.items() if not k.startswith("GIT_")}
        script = (script_root or self.factory) / ".kilo/skills/git-worktree/scripts/bootstrap.py"
        result = subprocess.run([sys.executable, str(script), *args], cwd=root,
                                env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0 if ok else 1, result.stdout + result.stderr)
        return result

    def create(self):
        self.cli(self.factory, "project")
        return self.factory / "project"

    def state(self, root):
        return tuple(self.git(root, *args).stdout for args in (
            ("rev-parse", "HEAD"), ("ls-files", "--stage"),
            ("status", "--porcelain", "--untracked-files=all")))

    def clone(self, root, name="clone"):
        destination = self.base / name
        self.git(self.base, "clone", "--no-local", str(root), str(destination))
        return destination

    def test_project_initial_commit_and_tracked_boundary(self):
        marker = self.factory / ".kilo/command/source-marker.md"
        marker.write_text("factory checkout fixture\n")
        for relative in ("templates/project/.env", ".kilo/skills/.env", ".kilo/local/private"):
            path = self.factory / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("never copy\n")
        root = self.create()
        self.assertEqual(self.git(root, "rev-list", "--count", "HEAD").stdout.strip(), "1")
        tracked = set(self.git(root, "ls-files").stdout.splitlines())
        expected = {str(p.relative_to(self.factory / "templates/project"))
                    for p in (self.factory / "templates/project").rglob("*") if p.is_file()}
        expected -= {"AGENTS.md", "docs/BOARD.md", ".env"}
        self.assertEqual(tracked, expected)
        self.assertIn("services.json", tracked)
        self.assertEqual(self.git(root, "status", "--porcelain").stdout, "")
        self.assertTrue((root / ".kilo/command/source-marker.md").is_file())
        self.assertFalse((root / ".env").exists())
        self.assertFalse((root / ".kilo/local").exists())
        for name in bootstrap.HARNESS:
            self.assertTrue((root / ".kilo" / name).is_dir())
        config = json.loads((root / ".devcontainer/devcontainer.json").read_text())
        self.assertIn("kilo-redact.sh", config["postCreateCommand"])
        self.assertNotIn("safe.directory", config["postCreateCommand"])
        self.assertTrue((root / ".devcontainer/Dockerfile").is_file())
        self.assertEqual(json.loads((root / "services.json").read_text()), {"services": []})

    def lifecycle_fixture(self):
        root = self.create()
        board = worktree.load_board_module(str(root))
        text = "| " + " | ".join(board.COLUMNS) + " |\n"
        text += "| " + " | ".join(["---"] * len(board.COLUMNS)) + " |\n"
        text += "| BOARD-001 | Inherited control | Feature | Ready | P2 | low | None. | control | - | fixture |\n"
        (root / "docs/BOARD.md").write_text(text)
        return root

    def lifecycle(self, root, *args, ok=True, override=None):
        env = dict(self.env)
        env.pop("KILO_CONFIG", None)
        if override:
            env["KILO_CONFIG"] = str(override)
        # The script is ignored in the primary. A new worktree has no local copy.
        script = root / ".kilo/skills/git-worktree/scripts/worktree.py"
        result = subprocess.run([sys.executable, str(script), *args], cwd=root,
                                env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0 if ok else 1, result.stdout + result.stderr)
        return result

    def test_bootstrapped_ignored_control_inherits_unchanged_config_and_mode(self):
        root = self.lifecycle_fixture()
        config = root / "kilo.jsonc"
        original = config.read_bytes()
        self.assertNotIn("kilo.jsonc", self.git(root, "ls-files").stdout)
        self.assertNotIn(".kilo/repos.json", self.git(root, "ls-files").stdout)
        self.lifecycle(root, "create", "--board", "BOARD-001", override=config)
        path = root / ".kilo/worktrees/inherited-control"
        self.assertFalse((path / "kilo.jsonc").exists())
        self.assertFalse((path / ".kilo/skills/git-worktree/scripts/worktree.py").exists())
        self.assertEqual(config.read_bytes(), original)
        self.assertIn(".kilo/worktrees/inherited-control", (root / "docs/BOARD.md").read_text())
        self.assertIn("required", self.lifecycle(root, "mode", "status").stdout)
        for mode in ("optional", "required"):
            self.lifecycle(root, "mode", mode)
            self.assertEqual(worktree.local_state(str(root))["mode"], mode)
            self.assertFalse((path / "kilo.jsonc").exists())
        self.assertEqual(config.read_bytes(), original)
        self.lifecycle(root, "resume", "--board", "BOARD-001")

    def test_bootstrapped_partial_ordered_config_failure_recovers_same_path(self):
        root = self.lifecycle_fixture()
        path = root / ".kilo/worktrees/inherited-control"
        config = root / "kilo.jsonc"
        ordered = config.read_bytes()
        before = (root / "docs/BOARD.md").read_bytes()
        for index, kind in enumerate(("edit", "bash", "read")):
            data = json.loads(ordered)
            mapping = data["permission"][kind]
            first = next(iter(mapping))
            mapping[first] = mapping.pop(first)
            config.write_text(json.dumps(data))
            bad = config.read_bytes()
            command = "create" if index == 0 else "resume"
            result = self.lifecycle(root, command, "--board", "BOARD-001", ok=False)
            self.assertIn("inherited permission map disagrees", result.stderr)
            self.assertEqual(config.read_bytes(), bad)
            self.assertEqual((root / "docs/BOARD.md").read_bytes(), before)
        self.assertFalse((path / "kilo.jsonc").exists())
        (path / "source.txt").write_text("preserve source")
        (path / ".env.local").write_text("preserve ignored")
        (root / ".env.local").write_text("primary value")
        self.lifecycle(root, "create", "--board", "BOARD-001", "--slug", "retry", "--new", ok=False)
        branches = self.git(root, "branch", "--list").stdout
        config.write_bytes(ordered)
        self.lifecycle(root, "resume", "--board", "BOARD-001")
        self.lifecycle(root, "resume", "--board", "BOARD-001")
        self.assertEqual(self.git(root, "branch", "--list").stdout, branches)
        self.assertEqual((path / "source.txt").read_text(), "preserve source")
        self.assertEqual((path / ".env.local").read_text(), "preserve ignored")
        self.assertEqual(config.read_bytes(), ordered)
        state = worktree.local_state(str(root))["workspaces"][str(path)]
        self.assertNotIn("error", state)
        self.assertEqual(state["boards"], ["BOARD-001"])

    def test_bootstrapped_recovery_config_scope_and_saved_mode_fail_closed(self):
        root = self.lifecycle_fixture()
        path = root / ".kilo/worktrees/inherited-control"
        config = root / "kilo.jsonc"
        ordered = config.read_bytes()
        before = (root / "docs/BOARD.md").read_bytes()
        result = self.lifecycle(root, "create", "--board", "BOARD-001", ok=False,
                                override=self.factory / "kilo.jsonc")
        self.assertIn("KILO_CONFIG is outside", result.stderr)
        # A source-factory ancestor is never an effective project configuration.
        config.unlink()
        result = self.lifecycle(root, "resume", "--board", "BOARD-001", ok=False)
        self.assertIn("no effective project configuration", result.stderr)
        self.assertFalse(config.exists())
        config.write_bytes(ordered)
        state = worktree.local_state(str(root))
        state["mode"] = "optional"
        worktree.local_state(str(root), state)
        result = self.lifecycle(root, "resume", "--board", "BOARD-001", ok=False)
        self.assertIn("inherited permission map disagrees with saved mode", result.stderr)
        self.assertEqual(config.read_bytes(), ordered)
        self.assertEqual((root / "docs/BOARD.md").read_bytes(), before)
        self.assertIn("error", worktree.local_state(str(root))["workspaces"][str(path)])

    def test_outside_destinations_refused_before_any_mutation(self):
        before = {p: p.read_bytes() for p in self.factory.rglob("*") if p.is_file()}
        parent_entries = set(self.base.iterdir())
        for destination in ("../sibling", str(self.base / "absolute"),
                            str(self.base / "missing-parent/project")):
            with self.subTest(destination=destination):
                result = self.cli(self.factory, "project", "--destination", destination, ok=False)
                self.assertIn("outside destination:", result.stderr)
                self.assertIn("explicit user approval", result.stderr)
                self.assertIn("--allow-outside", result.stderr)
                self.assertIn("Current working directory: " + str(self.factory), result.stderr)
                self.assertIn("Factory source: " + str(self.factory), result.stderr)
                self.assertIn("Resolved destination:", result.stderr)
                self.assertEqual(set(self.base.iterdir()), parent_entries)
                self.assertEqual({p: p.read_bytes() for p in self.factory.rglob("*") if p.is_file()}, before)

    def test_direct_project_helper_enforces_boundary_and_source_cwd(self):
        with patch.object(Path, "cwd", return_value=self.factory):
            with self.assertRaisesRegex(ValueError, "outside destination:"):
                bootstrap.project(self.factory, self.base / "direct")
        with patch.object(Path, "cwd", return_value=self.base):
            with self.assertRaisesRegex(ValueError, "factory checkout root"):
                bootstrap.project(self.factory, self.base / "direct", allow_outside=True)
        self.assertFalse((self.base / "direct").exists())

    def test_custom_internal_destination_and_explicit_external_destination(self):
        (self.factory / "products").mkdir()
        internal = self.cli(self.factory, "project", "--destination", "products/custom")
        root = self.factory / "products/custom"
        self.assertTrue(internal.stdout.rstrip().endswith("at " + str(root)))
        self.assertEqual(self.git(root, "rev-list", "--count", "HEAD").stdout.strip(), "1")
        external = self.base / "approved-project"
        self.cli(self.factory, "project", "--destination", str(external), "--allow-outside")
        self.assertEqual(self.git(external, "rev-list", "--count", "HEAD").stdout.strip(), "1")

    def test_allow_outside_is_project_only(self):
        root = self.create()
        clone = self.clone(root)
        for cwd, args in ((root, ["app", "billing-worker", "--git", "project"]),
                          (self.factory, ["restore", "--destination", str(clone)])):
            before = self.state(cwd) if cwd == root else self.state(clone)
            result = subprocess.run([sys.executable,
                str(self.factory / ".kilo/skills/git-worktree/scripts/bootstrap.py"),
                *args, "--allow-outside"], cwd=cwd, env=self.env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("unrecognized arguments: --allow-outside", result.stderr)
            self.assertEqual(self.state(root if cwd == root else clone), before)
        self.assertFalse((root / "apps/billing-worker").exists())
        self.assertFalse((clone / ".kilo").exists())
        self.cli(self.factory, "restore", "--destination", str(clone))

    def test_project_cwd_and_path_preflights_with_override(self):
        self.cli(self.base, "project", "--destination", str(self.base / "wrong-cwd"),
                 "--allow-outside", ok=False)
        alias = self.factory / "alias"
        alias.symlink_to(self.base, target_is_directory=True)
        for destination, diagnostic in ((alias / "escaped", "symlinks are not supported"),
                (self.factory / "child/../escaped", "traversal is not supported"),
                (self.base / "missing-parent/project", "destination parent must"),
                (self.factory, "destination already exists")):
            result = self.cli(self.factory, "project", "--destination", str(destination),
                              "--allow-outside", ok=False)
            self.assertIn(diagnostic, result.stderr)
        self.assertFalse((self.base / "escaped").exists())
        self.assertFalse((self.factory / "escaped").exists())
        self.assertFalse((self.base / "wrong-cwd").exists())

    def test_ignored_local_files_and_trackable_product_files(self):
        root = self.create()
        for path in (".kilo/agent/a.md", ".devcontainer/Dockerfile", "kilo.jsonc", "AGENTS.md",
                     "docs/BOARD.md", ".env", "nested/.env.local", "secret.key", "cert.pem",
                     "cert.p12", "id_rsa_test", "artifacts/report", ".tmp/file", "node_modules/a",
                     ".playwright/a", ".playwright-mcp/a", "playwright-report/a", "test-results/a", "blob-report/a"):
            self.assertEqual(self.git(root, "check-ignore", "--no-index", path, ok=False).returncode, 0, path)
        for path in ("services.json", "src/main.py", "docs/spec.md", ".env.example"):
            self.assertEqual(self.git(root, "check-ignore", "--no-index", path, ok=False).returncode, 1, path)
        self.assertEqual(self.git(SOURCE, "ls-files", "--", "templates/project/docs/BOARD.md").stdout.strip(),
                         "templates/project/docs/BOARD.md")

    def test_service_roles_and_both_git_ownerships(self):
        root = self.create()
        before = self.state(root)[:2]
        for name, mode in (("shop-frontend", "separate"), ("shop-backend", "project"),
                           ("shop-backend-experimental", "separate"), ("billing-worker", "project"),
                           ("inventory-cron", "project"), ("shop-public-frontdoor", "project")):
            self.cli(root, "app", name, "--git", mode, script_root=root)
            app = root / "apps" / name
            self.assertEqual((app / ".git").is_dir(), mode == "separate")
            if mode == "separate":
                self.assertEqual(self.git(app, "rev-list", "--count", "HEAD").stdout.strip(), "1")
                self.assertEqual(self.git(app, "ls-files").stdout, ".gitignore\n")
            else:
                (app / "source.py").write_text("pass\n")
                self.assertIn("apps/" + name + "/source.py", self.git(root, "ls-files", "--others", "--exclude-standard").stdout)
            for path in ("AGENTS.md", ".devcontainer/Dockerfile", "kilo.jsonc", ".kilo/local/a", ".env", "secret.key"):
                self.assertEqual(self.git(app, "check-ignore", "--no-index", path, ok=False).returncode, 0, name + path)
        self.assertEqual(self.state(root)[:2], before)
        data = json.loads((root / "services.json").read_text())
        self.assertEqual(len(data["services"]), 6)
        self.assertEqual(json.loads((root / ".kilo/repos.json").read_text()), {
            "control": ".", "shop-frontend": "apps/shop-frontend",
            "shop-backend-experimental": "apps/shop-backend-experimental"})

    def test_project_clone_restore_twice_preserves_source_index_head(self):
        root = self.create()
        self.cli(root, "app", "shop-frontend", "--git", "separate")
        self.cli(root, "app", "billing-worker", "--git", "project")
        self.git(root, "add", "services.json", ".gitignore", "apps/billing-worker/.gitignore")
        self.git(root, "commit", "-m", "fixture service registration")
        clone = self.clone(root)
        self.assertFalse((clone / ".kilo").exists())
        (clone / "docs/local-note.txt").write_text("handwritten source\n")
        self.git(clone, "add", "docs/local-note.txt")
        before = self.state(clone)
        tracked = {p: (clone / p).read_bytes() for p in self.git(clone, "ls-files").stdout.splitlines()}
        first = self.cli(self.factory, "restore", "--destination", str(clone))
        self.assertIn("Missing service checkout: apps/shop-frontend", first.stdout)
        self.assertEqual(json.loads((clone / ".kilo/repos.json").read_text()), {
            "control": ".", "shop-frontend": "apps/shop-frontend"})
        exclude = (clone / ".git/info/exclude").read_bytes()
        self.cli(self.factory, "restore", "--destination", str(clone))
        self.assertEqual((clone / ".git/info/exclude").read_bytes(), exclude)
        shutil.rmtree(clone / ".kilo")
        shutil.rmtree(clone / ".devcontainer")
        (clone / "AGENTS.md").unlink()
        (clone / "kilo.jsonc").unlink()
        (clone / "docs/BOARD.md").unlink()
        self.cli(self.factory, "restore", "--destination", str(clone))
        self.assertEqual(self.state(clone), before)
        for p, content in tracked.items():
            self.assertEqual((clone / p).read_bytes(), content)

    def test_separate_clone_restore_context_and_lifecycle_root(self):
        root = self.create()
        self.cli(root, "app", "shop-frontend", "--git", "separate")
        self.git(root, "add", "services.json")
        self.git(root, "commit", "-m", "fixture manifest")
        clone = self.clone(root)
        self.cli(self.factory, "restore", "--destination", str(clone))
        app = clone / "apps/shop-frontend"
        app.parent.mkdir(exist_ok=True)
        self.git(clone, "clone", str(root / "apps/shop-frontend"), str(app))
        before, control_before = self.state(app), self.state(clone)
        restored = self.cli(self.factory, "restore", "--destination", str(app), "--project", str(clone))
        self.assertIn("without an app devcontainer", restored.stdout)
        self.cli(self.factory, "restore", "--destination", str(app))
        self.assertTrue((app / ".kilo/skills/git-worktree/scripts/worktree.py").is_file())
        self.assertFalse((app / ".devcontainer").exists())
        instructions = (app / "AGENTS.md").read_text()
        self.assertIn("../../", instructions)
        self.assertNotIn(str(clone), instructions)
        self.assertFalse((app / ".kilo/local/control-root").exists())
        self.assertFalse((app / ".kilo/repos.json").exists())
        self.assertFalse((app / "docs/BOARD.md").exists())
        self.assertEqual(self.state(app), before)
        self.assertEqual(self.state(clone), control_before)
        result = subprocess.run([sys.executable, "-c",
            "import worktree; print(worktree.control_root('.'))"], cwd=app,
            env={**self.env, "PYTHONPATH": str(app / ".kilo/skills/git-worktree/scripts")},
            text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(clone))
        standalone = self.clone(root / "apps/shop-frontend", "standalone")
        self.assertIn("requires --project", self.cli(self.factory, "restore", "--destination", str(standalone), ok=False).stderr)
        self.assertIn("must occupy", self.cli(self.factory, "restore", "--destination", str(standalone), "--project", str(clone), ok=False).stderr)

        # Moving the entire control simulates a different container mount prefix.
        mounted = self.base / "container-workspace"
        clone.rename(mounted)
        app = mounted / "apps/shop-frontend"
        config = json.loads((mounted / ".devcontainer/devcontainer.json").read_text())
        effective_config = config["remoteEnv"]["KILO_CONFIG"].replace("${containerWorkspaceFolder}", str(mounted))
        self.assertEqual(Path(effective_config), mounted / "kilo.jsonc")
        self.assertTrue(Path(effective_config).is_file())
        self.assertEqual((app / "../../").resolve(), mounted)
        result = subprocess.run([sys.executable, "-c",
            "import guard, worktree; print(worktree.control_root('.')); print(guard.control_root(None))"],
            cwd=app, env={**self.env, "KILO_CONFIG": effective_config,
                         "PYTHONPATH": str(app / ".kilo/skills/git-worktree/scripts")},
            text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [str(mounted), str(mounted)])
        self.assertEqual((app / "kilo.jsonc").read_bytes(), (mounted / "kilo.jsonc").read_bytes())

    def test_restore_conflict_preflight_writes_nothing(self):
        root = self.clone(self.create())
        (root / "AGENTS.md").write_text("handwritten custom instructions\n")
        before = self.state(root)
        exclude = (root / ".git/info/exclude").read_bytes()
        result = self.cli(self.factory, "restore", "--destination", str(root), ok=False)
        self.assertIn("restore conflict; no files written", result.stderr)
        self.assertFalse((root / ".kilo").exists())
        self.assertFalse((root / ".devcontainer").exists())
        self.assertEqual((root / ".git/info/exclude").read_bytes(), exclude)
        self.assertEqual(self.state(root), before)

    def test_restore_missing_source_roots_and_source_symlinks(self):
        root = self.clone(self.create())
        shutil.rmtree(self.factory / ".devcontainer")
        self.cli(self.factory, "restore", "--destination", str(root), ok=False)
        self.assertFalse((root / ".kilo").exists())
        shutil.copytree(SOURCE / ".devcontainer", self.factory / ".devcontainer")
        (self.factory / ".kilo/command/linked.md").symlink_to(self.factory / "templates/project/README.md")
        self.cli(self.factory, "restore", "--destination", str(root), ok=False)
        self.assertFalse((root / ".kilo").exists())

    def test_restore_rejects_factory_linked_checkout_and_destination_symlinks(self):
        root = self.create()
        for destination in (self.factory, self.base / "alias", self.base / "linked"):
            if destination.name == "alias":
                destination.symlink_to(root, target_is_directory=True)
            if destination.name == "linked":
                self.git(root, "worktree", "add", "-b", "fixture", str(destination))
            self.cli(self.factory, "restore", "--destination", str(destination), ok=False)
        clone = self.clone(root)
        (clone / ".kilo").symlink_to(self.factory / ".kilo", target_is_directory=True)
        self.cli(self.factory, "restore", "--destination", str(clone), ok=False)

    def test_manifest_validation_before_restore_writes(self):
        root = self.clone(self.create())
        good = {"name": "shop-backend", "path": "apps/shop-backend", "git": "project"}
        for services in ([good, good], [{**good, "path": "../escape"}],
                         [{**good, "git": "guess"}], [{**good, "name": "Bad_Name"}]):
            (root / "services.json").write_text(json.dumps({"services": services}))
            self.cli(self.factory, "restore", "--destination", str(root), ok=False)
            self.assertFalse((root / ".kilo").exists())

    def test_missing_identity_preflight_and_commit_failure_retained_state(self):
        self.git(self.factory, "config", "--global", "--unset", "user.name")
        self.git(self.factory, "config", "--global", "--unset", "user.email")
        self.git(self.factory, "config", "--global", "user.useConfigOnly", "true")
        result = self.cli(self.factory, "project", ok=False)
        self.assertIn("identity unavailable", result.stderr)
        self.assertFalse((self.factory / "project").exists())
        # Parent-only identity passes preflight but is not inherited by the new repo.
        self.git(self.factory, "config", "user.name", "Fixture Parent")
        self.git(self.factory, "config", "user.email", "parent@example.invalid")
        result = self.cli(self.factory, "project", ok=False)
        self.assertIn("Git commit failed", result.stderr)
        self.assertIn("partial state retained", result.stderr)
        partial = self.factory / "project"
        self.assertTrue((partial / ".git").is_dir())
        self.assertNotEqual(self.git(partial, "rev-parse", "--verify", "HEAD", ok=False).returncode, 0)
        self.assertIn("services.json", self.git(partial, "ls-files").stdout)
        # A rejecting installed hook must not be bypassed; fixture-only hook configuration.
        hooks = self.base / "hooks"
        hooks.mkdir()
        hook = hooks / "pre-commit"
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
        self.git(self.factory, "config", "--global", "user.name", "Fixture")
        self.git(self.factory, "config", "--global", "user.email", "fixture@example.invalid")
        self.git(self.factory, "config", "--global", "core.hooksPath", str(hooks))
        root = self.base / "hook-rejected"
        result = self.cli(self.factory, "project", "--destination", str(root), "--allow-outside", ok=False)
        self.assertIn("partial state retained", result.stderr)
        self.assertTrue((root / ".git").is_dir())
        self.assertNotEqual(self.git(root, "rev-parse", "--verify", "HEAD", ok=False).returncode, 0)
        self.assertIn("services.json", self.git(root, "ls-files").stdout)
        self.cli(self.factory, "project", "--destination", str(root), "--allow-outside", ok=False)

    def test_all_initial_policy_commands_and_unknown_context_denials(self):
        path = self.factory / ".kilo/policies/git-policy.json"
        original = json.loads(path.read_text())
        for index, command in enumerate(("git init*", "git add*", "git commit*")):
            policy = json.loads(json.dumps(original))
            policy["bash"].append({"pattern": command, "action": "deny"})
            path.write_text(json.dumps(policy))
            destination = self.base / ("denied-" + str(index))
            result = self.cli(self.factory, "project", "--destination", str(destination), "--allow-outside", ok=False)
            self.assertIn("guard refused", result.stderr)
            self.assertFalse(destination.exists())
        original["context"].append({"applies_to": ["git commit*"], "check": "always", "action": "deny"})
        path.write_text(json.dumps(original))
        destination = self.base / "denied-context"
        result = self.cli(self.factory, "project", "--destination", str(destination), "--allow-outside", ok=False)
        self.assertIn("guard refused", result.stderr)
        self.assertFalse(destination.exists())

    def test_restore_nonregular_exclude_refuses_before_local_writes(self):
        root = self.clone(self.create())
        exclude = root / ".git/info/exclude"
        exclude.unlink()
        exclude.mkdir()
        self.cli(self.factory, "restore", "--destination", str(root), ok=False)
        self.assertFalse((root / ".kilo").exists())
        self.assertFalse((root / ".devcontainer").exists())

    def test_restore_refuses_missing_tracked_tooling_without_source_changes(self):
        root = self.clone(self.create())
        instructions = root / "AGENTS.md"
        instructions.write_text("Handwritten tracked instructions\n")
        self.git(root, "add", "-f", "AGENTS.md")
        self.git(root, "commit", "-m", "fixture tracked instructions")
        instructions.unlink()
        before = self.state(root)
        result = self.cli(self.factory, "restore", "--destination", str(root), ok=False)
        self.assertIn("tracked source", result.stderr)
        self.assertFalse(instructions.exists())
        self.assertFalse((root / ".kilo").exists())
        self.assertEqual(self.state(root), before)

    def test_restore_refuses_deleted_tracked_ancestors_before_any_writes(self):
        original = self.create()
        for index, (relative, kind) in enumerate(((".kilo", "file"), (".devcontainer", "symlink"),
                                                  (".kilo/skills", "gitlink"))):
            with self.subTest(kind=kind):
                root = self.clone(original, "ancestor-" + str(index))
                path = root / relative
                if kind == "gitlink":
                    commit = self.git(root, "rev-parse", "HEAD").stdout.strip()
                    self.git(root, "update-index", "--add", "--cacheinfo", "160000", commit, relative)
                else:
                    if kind == "file":
                        path.write_text("tracked ancestor source\n")
                    else:
                        path.symlink_to("README.md")
                    self.git(root, "add", "-f", "--", relative)
                self.git(root, "commit", "-m", "fixture tracked ancestor")
                if kind != "gitlink":
                    path.unlink()
                before = self.state(root)
                exclude = (root / ".git/info/exclude").read_bytes()
                result = self.cli(self.factory, "restore", "--destination", str(root), ok=False)
                self.assertIn("tracked source", result.stderr)
                self.assertFalse(os.path.lexists(path))
                for output in (".kilo", ".devcontainer", "kilo.jsonc", "AGENTS.md", "docs/BOARD.md"):
                    self.assertFalse((root / output).exists(), output)
                self.assertEqual((root / ".git/info/exclude").read_bytes(), exclude)
                self.assertEqual(self.state(root), before)

    def test_factory_app_cli_honors_target_control_policy_denials(self):
        root = self.create()
        policy_path = root / ".kilo/policies/git-policy.json"
        original = json.loads(policy_path.read_text())
        for index, command in enumerate(("git init*", "git add*", "git commit*")):
            with self.subTest(command=command):
                policy = json.loads(json.dumps(original))
                policy["bash"].append({"pattern": command, "action": "deny"})
                policy_path.write_text(json.dumps(policy))
                before = self.state(root)
                manifest = (root / "services.json").read_bytes()
                mapping = (root / ".kilo/repos.json").read_bytes()
                name = "denied-worker-" + str(index)
                result = self.cli(root, "app", name, "--git", "separate", ok=False,
                                  script_root=self.factory)
                self.assertIn("guard refused", result.stderr)
                self.assertFalse((root / "apps" / name).exists())
                self.assertEqual((root / "services.json").read_bytes(), manifest)
                self.assertEqual((root / ".kilo/repos.json").read_bytes(), mapping)
                self.assertEqual(self.state(root), before)

    def test_app_unsafe_ignore_or_stale_map_creates_nothing(self):
        root = self.create()
        ignore = root / ".gitignore"
        content = ignore.read_bytes()
        before = (root / "services.json").read_bytes()
        for kind in ("missing", "directory", "symlink"):
            ignore.unlink()
            if kind == "directory":
                ignore.mkdir()
            elif kind == "symlink":
                ignore.symlink_to(self.factory / "templates/project/.gitignore")
            for mode in ("separate", "project"):
                self.cli(root, "app", "billing-worker", "--git", mode, ok=False)
                self.assertFalse((root / "apps/billing-worker").exists())
            if ignore.is_dir():
                ignore.rmdir()
            elif ignore.is_symlink():
                ignore.unlink()
            ignore.write_bytes(content)
        (root / ".kilo/repos.json").write_text('{"control":".","stale":"apps/stale"}')
        self.cli(root, "app", "billing-worker", "--git", "project", ok=False)
        self.assertFalse((root / "apps/billing-worker").exists())
        self.assertEqual((root / "services.json").read_bytes(), before)

    def test_project_prerequisites_existing_parent_and_traversal(self):
        for destination in (self.base / "missing-parent/project", self.base / "child/../escape"):
            self.cli(self.factory, "project", "--destination", str(destination), "--allow-outside", ok=False)
        self.assertFalse((self.base / "escape").exists())
        (self.factory / "kilo.jsonc").unlink()
        self.cli(self.factory, "project", ok=False)
        self.assertFalse((self.factory / "project").exists())

    def test_hard_policy_denials_not_bypassed_and_integrated_no_commit(self):
        root = self.create()
        policy_path = self.factory / ".kilo/policies/git-policy.json"
        policy = json.loads(policy_path.read_text())
        policy["bash"].append({"pattern": "git commit*", "action": "deny", "reason": "fixture denial"})
        policy_path.write_text(json.dumps(policy))
        self.cli(root, "app", "shop-frontend", "--git", "separate", ok=False)
        self.assertFalse((root / "apps/shop-frontend").exists())
        before = self.state(root)[:2]
        self.cli(root, "app", "billing-worker", "--git", "project")
        self.assertEqual(self.state(root)[:2], before)
        destination = self.base / "denied"
        result = self.cli(self.factory, "project", "--destination", str(destination), "--allow-outside", ok=False)
        self.assertIn("guard refused", result.stderr)
        self.assertFalse(destination.exists())

    def test_invalid_names_collisions_existing_paths_and_required_git_choice(self):
        root = self.create()
        for name in ("Bad_Name", "../escape", "control", "worker--one"):
            self.cli(root, "app", name, "--git", "separate", ok=False)
        result = subprocess.run([sys.executable, str(self.factory / ".kilo/skills/git-worktree/scripts/bootstrap.py"),
                                 "app", "shop-frontend"], cwd=root, env=self.env, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.cli(root, "app", "shop-frontend", "--git", "separate")
        before = self.state(root)
        self.cli(root, "app", "shop-frontend", "--git", "project", ok=False)
        self.assertEqual(self.state(root), before)
        self.cli(self.factory, "project", ok=False)
        alias = self.base / "alias"
        alias.symlink_to(root, target_is_directory=True)
        self.cli(self.factory, "project", "--destination", str(alias), ok=False)


if __name__ == "__main__":
    unittest.main()
