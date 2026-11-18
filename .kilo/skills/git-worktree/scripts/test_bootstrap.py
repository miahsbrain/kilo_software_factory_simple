"""Bootstrap tests use temporary factory/project fixtures, never the real project."""

import contextlib
import io
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


SOURCE = Path(__file__).resolve().parents[4]


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bootstrap-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.factory = self.base / "factory"
        self.factory.mkdir()
        shutil.copytree(SOURCE / "templates", self.factory / "templates")
        for name in bootstrap.HARNESS:
            shutil.copytree(SOURCE / ".kilo" / name, self.factory / ".kilo" / name,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for name in (".kilo/.gitignore", "kilo.jsonc"):
            shutil.copy2(SOURCE / name, self.factory / name)
        self.run_git(self.factory, "init")

    def run_git(self, root, *args, check=True):
        return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True,
                              check=check)

    def cli(self, root, *args, script_root=None, ok=True):
        script = (script_root or root) / ".kilo/skills/git-worktree/scripts/bootstrap.py"
        env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        result = subprocess.run([sys.executable, str(script), *args], cwd=root,
                                env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0 if ok else 1, result.stdout + result.stderr)
        return result

    def create(self):
        self.cli(self.factory, "project")
        return self.factory / "project"

    def assert_empty_git(self, root):
        self.assertEqual(self.run_git(root, "rev-parse", "--show-toplevel").stdout.strip(), str(root))
        self.assertNotEqual(self.run_git(root, "rev-parse", "--verify", "HEAD", check=False).returncode, 0)
        self.assertEqual(self.run_git(root, "ls-files", "--stage").stdout, "")

    def test_default_project_full_harness_and_no_local_copy(self):
        for relative in ("docs/BOARD.md", ".kilo/repos.json", ".kilo/local/qa-navigation.json",
                         ".kilo/skills/artifacts/report.txt", ".kilo/skills/.env",
                         "templates/project/.env", "templates/project/artifacts/report.txt",
                         "templates/project/.kilo/local/qa-navigation.json"):
            path = self.factory / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture-local\n")
        # A checkout-local change proves we copy this fixture checkout, not the primary factory.
        marker = self.factory / ".kilo/command/checkout-marker.md"
        marker.write_text("fixture source\n")
        project = self.create()
        self.assert_empty_git(project)
        self.assertEqual(list((project / "apps").iterdir()), [])
        self.assertEqual(json.loads((project / ".kilo/repos.json").read_text()), {"control": "."})
        self.assertEqual((project / "AGENTS.md").read_bytes(),
                         (self.factory / "templates/project/AGENTS.md").read_bytes())
        self.assertEqual((project / "docs/BOARD.md").read_bytes(),
                         (self.factory / "templates/project/docs/BOARD.md").read_bytes())
        self.assertEqual((project / ".kilo/.gitignore").read_bytes(),
                         (self.factory / ".kilo/.gitignore").read_bytes())
        self.assertEqual((project / "kilo.jsonc").read_bytes(), (self.factory / "kilo.jsonc").read_bytes())
        for name in bootstrap.HARNESS:
            self.assertTrue((project / ".kilo" / name).is_dir())
        self.assertTrue((project / ".kilo/command/checkout-marker.md").is_file())
        for relative in (".env", "artifacts", ".kilo/local", ".kilo/skills/.env",
                         ".kilo/skills/artifacts"):
            self.assertFalse((project / relative).exists(), relative)

    def test_isolated_destination_and_static_ignore_probes(self):
        project = self.base / "isolated"
        self.cli(self.factory, "project", "--destination", str(project))
        ignored = ["docs/BOARD.md", "nested/docs/BOARD.md", "artifacts/report.txt",
                   ".env", "nested/.env.local", "secret.key", "cert.pem", "cert.p12",
                   "id_rsa_test", ".kilo/local/qa-navigation.json", ".kilo/qa-local/note",
                   ".kilo/worktrees/demo/file", ".tmp/file", "apps/frontend/code.py",
                   ".kilo/agent-manager.json", "nested/__pycache__/x.pyc"]
        for pattern in (".playwright-mcp", ".playwright", "playwright-report", "test-results", "blob-report"):
            ignored.extend([pattern + "/result.txt", "nested/" + pattern + "/result.txt"])
        for path in ignored:
            self.assertEqual(self.run_git(project, "check-ignore", "--no-index", path, check=False).returncode, 0, path)
        for path in (".env.example", "src/main.py", ".kilo/policies/git-policy.json",
                     "kilo.jsonc", ".kilo/skills/git-worktree/scripts/test_bootstrap.py",
                     ".kilo/command/bootstrap.md", ".kilo/repos.json"):
            self.assertEqual(self.run_git(project, "check-ignore", "--no-index", path, check=False).returncode, 1, path)
        self.assertNotIn("/project/", (project / ".gitignore").read_text().splitlines())

    def test_template_board_remains_tracked(self):
        tracked = self.run_git(SOURCE, "ls-files", "--", "templates/project/docs/BOARD.md")
        self.assertEqual(tracked.stdout.strip(), "templates/project/docs/BOARD.md")

    def test_copied_tool_initializes_arbitrary_real_apps_only(self):
        project = self.create()
        ignore_path = project / ".gitignore"
        ignore_path.write_text(ignore_path.read_text() + "\n.project-local-cache/\n")
        for name in ("customer-portal", "billing-worker", "backend", "frontend"):
            self.cli(project, "app", name, "--git", "separate")
            app = project / "apps" / name
            self.assert_empty_git(app)
            self.assertEqual(sorted(path.name for path in app.iterdir()), [".git", ".gitignore"])
            self.assertEqual((app / ".gitignore").read_text(), "".join(
                line for line in ignore_path.read_text().splitlines(keepends=True)
                if line.strip() != "apps/*/"))
            ignored = [".env", ".env.production", "nested/.env.local", "secret.key", "cert.pem",
                       "cert.p12", "id_rsa_test", ".kilo/worktrees/demo/file",
                       ".kilo/local/qa-navigation.json", ".kilo/qa-local/note",
                       "artifacts/report.txt", "node_modules/pkg/index.js", ".tmp/file",
                       "nested/__pycache__/x.pyc", ".project-local-cache/file"]
            for pattern in (".playwright-mcp", ".playwright", "playwright-report", "test-results", "blob-report"):
                ignored.extend([pattern + "/result.txt", "nested/" + pattern + "/result.txt"])
            for path in ignored:
                self.assertEqual(self.run_git(app, "check-ignore", "--no-index", path, check=False).returncode, 0, path)
            for path in (".env.example", "nested/.env.example", "src/main.py", "tests/test_main.py",
                         "apps/nested/src/main.py", ".gitignore", "kilo.jsonc"):
                self.assertEqual(self.run_git(app, "check-ignore", "--no-index", path, check=False).returncode, 1, path)
            self.assertEqual(json.loads((project / ".kilo/repos.json").read_text())[name], "apps/" + name)
        self.assert_empty_git(project)
        before = (project / ".kilo/repos.json").read_bytes()
        self.cli(project, "app", "customer-portal", "--git", "separate", ok=False)
        self.assertEqual((project / ".kilo/repos.json").read_bytes(), before)

    def test_app_choice_required_before_mutation(self):
        project = self.create()
        before = {path: (project / path).read_bytes()
                  for path in (".gitignore", ".kilo/repos.json")}
        for options in ([], ["--git", "unknown"]):
            result = subprocess.run(
                [sys.executable, str(project / ".kilo/skills/git-worktree/scripts/bootstrap.py"),
                 "app", "demo", *options], cwd=project, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("--git", result.stderr)
            self.assertEqual(list((project / "apps").iterdir()), [])
            for path, content in before.items():
                self.assertEqual((project / path).read_bytes(), content)
        self.assert_empty_git(project)

    def test_project_app_tracks_source_without_git_or_mapping(self):
        project = self.create()
        ignore = project / ".gitignore"
        ignore.write_text(ignore.read_text() + "\n.project-local-cache/\n")
        before = ignore.read_text()
        map_before = (project / ".kilo/repos.json").read_bytes()
        # No init is performed here, so even a hard init denial is irrelevant.
        policy_path = project / ".kilo/policies/git-policy.json"
        policy = json.loads(policy_path.read_text())
        for rule in policy["bash"]:
            if rule["pattern"] == "git init*":
                rule["action"] = "deny"
        policy_path.write_text(json.dumps(policy))
        self.cli(project, "app", "portal", "--git", "project")
        self.assertEqual([path.name for path in (project / "apps/portal").iterdir()], [".gitignore"])
        self.assertEqual((project / ".kilo/repos.json").read_bytes(), map_before)
        self.assertEqual(ignore.read_text(), before + "\n!/apps/portal/\n")
        source = project / "apps/portal/src/main.py"
        source.parent.mkdir()
        source.write_text("# fixture source\n")
        untracked = self.run_git(project, "ls-files", "--others", "--exclude-standard").stdout.splitlines()
        self.assertIn("apps/portal/src/main.py", untracked)
        for path in ("src/main.py", ".env.example", "nested/.env.example"):
            self.assertEqual(self.run_git(project, "check-ignore", "--no-index",
                                         "apps/portal/" + path, check=False).returncode, 1, path)
        for path in (".env", "nested/.env.local", "secret.key", "cert.pem", "cert.p12",
                     "id_rsa_test", "artifacts/file", "node_modules/pkg/file", ".tmp/file",
                     ".kilo/local/qa-navigation.json", ".kilo/agent-manager.json", ".kilo/worktrees/demo/file",
                     ".kilo/qa-local/file", "nested/__pycache__/x.pyc", ".project-local-cache/file",
                     ".playwright/file", ".playwright-mcp/file", "playwright-report/file",
                     "test-results/file", "blob-report/file"):
            self.assertEqual(self.run_git(project, "check-ignore", "--no-index",
                                         "apps/portal/" + path, check=False).returncode, 0, path)
        self.assertEqual(self.run_git(project, "check-ignore", "apps/other/src/main.py",
                                     check=False).returncode, 0)
        self.cli(project, "app", "independent", "--git", "separate", ok=False)
        self.assertFalse((project / "apps/independent").exists())
        for mode in ("separate", "project"):
            self.cli(project, "app", "portal", "--git", mode, ok=False)
        self.assert_empty_git(project)

    def test_app_ignore_source_preflight_creates_nothing(self):
        project = self.create()
        (project / "apps").rmdir()  # Empty fixture only.
        before = (project / ".kilo/repos.json").read_bytes()
        ignore_path = project / ".gitignore"
        saved = project / "saved-ignore"
        ignore_path.rename(saved)
        for kind in ("missing", "symlink", "directory"):
            if kind == "symlink":
                ignore_path.symlink_to(saved)
            elif kind == "directory":
                ignore_path.unlink()  # Fixture symlink, not its target.
                ignore_path.mkdir()
            for mode in ("separate", "project"):
                self.cli(project, "app", "demo", "--git", mode, ok=False)
            self.assertFalse((project / "apps").exists())
            self.assertEqual((project / ".kilo/repos.json").read_bytes(), before)
            self.assertTrue(saved.is_file())

    def test_project_refuses_existing_empty_file_and_symlink_destinations(self):
        paths = [self.base / "empty", self.base / "file", self.base / "link", self.base / "dangling"]
        paths[0].mkdir()
        paths[1].write_text("unchanged")
        paths[2].symlink_to(paths[0], target_is_directory=True)
        paths[3].symlink_to(self.base / "missing")
        for path in paths:
            self.cli(self.factory, "project", "--destination", str(path), ok=False)
        self.assertEqual(paths[1].read_text(), "unchanged")
        self.assertFalse((paths[0] / ".git").exists())
        project = self.create()
        before = (project / "kilo.jsonc").read_bytes()
        self.cli(self.factory, "project", ok=False)
        self.assertEqual((project / "kilo.jsonc").read_bytes(), before)

    def test_app_rejects_invalid_names_paths_existing_and_symlinks(self):
        project = self.create()
        before = (project / ".kilo/repos.json").read_bytes()
        for name in ("../escape", "a/b", "/absolute", "..", ".", "UPPER", "a_b", "control"):
            for mode in ("separate", "project"):
                self.cli(project, "app", name, "--git", mode, ok=False)
        existing = project / "apps/existing"
        existing.mkdir()
        (existing / "keep").write_text("unchanged")
        (project / "apps/link").symlink_to(self.base / "absent")
        for name in ("existing", "link"):
            for mode in ("separate", "project"):
                self.cli(project, "app", name, "--git", mode, ok=False)
        self.assertEqual((existing / "keep").read_text(), "unchanged")
        self.assertEqual((project / ".kilo/repos.json").read_bytes(), before)
        self.assertFalse((self.base / "escape").exists())

    def test_malformed_maps_and_collisions_leave_no_app(self):
        project = self.create()
        map_path = project / ".kilo/repos.json"
        for data in ('{', '[]', '{"control":"other"}', '{"control":".","x":4}',
                     '{"control":".","x":"../x"}', '{"control":".","control":"."}',
                     '{"control":".","other":"apps/demo"}',
                     '{"control":".","demo":"apps/other"}',
                     '{"control":".","a":"apps/x","b":"apps/x"}'):
            map_path.write_text(data)
            for mode in ("separate", "project"):
                self.cli(project, "app", "demo", "--git", mode, ok=False)
            self.assertEqual(map_path.read_text(), data)
            self.assertFalse((project / "apps/demo").exists())

    def test_nonproject_missing_git_repo_and_symlink_apps_refused(self):
        for mode in ("separate", "project"):
            self.cli(self.factory, "app", "demo", "--git", mode, ok=False)
        project = self.create()
        other = self.base / "not-initialized"
        shutil.copytree(project, other, ignore=shutil.ignore_patterns(".git"))
        for mode in ("separate", "project"):
            self.cli(other, "app", "demo", "--git", mode, ok=False)
        (project / "apps").rmdir()  # Empty fixture only; never a real project.
        (project / "apps").symlink_to(self.base, target_is_directory=True)
        for mode in ("separate", "project"):
            self.cli(project, "app", "demo", "--git", mode, ok=False)
        self.assertFalse((self.base / "demo").exists())
        for mode in ("separate", "project"):
            self.cli(self.factory / "templates/project", "app", "demo", "--git", mode,
                     script_root=self.factory, ok=False)

    def test_missing_sources_and_source_symlink_preflight(self):
        config = self.factory / "kilo.jsonc"
        config.rename(self.factory / "saved-config")
        self.cli(self.factory, "project", ok=False)
        self.assertFalse((self.factory / "project").exists())
        (self.factory / "saved-config").rename(config)
        (self.factory / ".kilo/command/link.md").symlink_to(config)
        self.cli(self.factory, "project", ok=False)
        self.assertFalse((self.factory / "project").exists())
        self.cli(self.factory, "project", "--destination", str(self.base / "missing/child"), ok=False)
        self.assertFalse((self.base / "missing").exists())

    def test_guard_hard_denial_and_destination_traversal_create_nothing(self):
        policy_path = self.factory / ".kilo/policies/git-policy.json"
        policy = json.loads(policy_path.read_text())
        for rule in policy["bash"]:
            if rule["pattern"] == "git init*":
                rule["action"] = "deny"
        policy_path.write_text(json.dumps(policy))
        result = self.cli(self.factory, "project", ok=False)
        self.assertIn("guard refused", result.stderr)
        self.assertFalse((self.factory / "project").exists())
        with self.assertRaisesRegex(ValueError, "traversal"):
            bootstrap.project(self.factory, self.base / "factory/../escape")
        self.assertFalse((self.base / "escape").exists())

    def test_retained_map_temporary_path_refused_before_app_creation(self):
        project = self.create()
        temporary = project / ".kilo/repos.json.bootstrap-tmp"
        temporary.write_text("retained fixture")
        for mode in ("separate", "project"):
            self.cli(project, "app", "demo", "--git", mode, ok=False)
        self.assertEqual(temporary.read_text(), "retained fixture")
        self.assertFalse((project / "apps/demo").exists())

    def test_missing_git_and_environment_overrides_create_nothing(self):
        with patch("bootstrap.shutil.which", return_value=None), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(bootstrap.main(["project", "--destination", str(self.base / "absent")]), 1)
        with patch.dict(os.environ, {"GIT_DIR": "fixture-override"}), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(bootstrap.main(["project", "--destination", str(self.base / "absent")]), 1)
        self.assertFalse((self.base / "absent").exists())

    def test_git_init_failure_retains_partial_state_and_map(self):
        project = self.base / "partial"
        with patch("bootstrap.git", side_effect=ValueError("Git init failed")):
            with self.assertRaisesRegex(ValueError, "partial state retained"):
                bootstrap.project(self.factory, project)
        self.assertTrue((project / "kilo.jsonc").is_file())
        self.assertFalse((project / ".git").exists())
        control = self.create()
        before = (control / ".kilo/repos.json").read_bytes()
        with patch("bootstrap.git", side_effect=[str(control), ValueError("Git init failed")]):
            with self.assertRaisesRegex(ValueError, "partial state retained"):
                bootstrap.app(control, control, "failed-app", "separate")
        self.assertTrue((control / "apps/failed-app").is_dir())
        self.assertTrue((control / "apps/failed-app/.gitignore").is_file())
        self.assertEqual((control / ".kilo/repos.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
