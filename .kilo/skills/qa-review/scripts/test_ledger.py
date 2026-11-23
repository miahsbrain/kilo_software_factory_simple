import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import ledger


class LedgerTests(unittest.TestCase):
    def setUp(self):
        source = subprocess.run(["git", "rev-parse", "--show-toplevel"], check=True,
                                capture_output=True, text=True).stdout.strip()
        fixtures = Path(source) / "artifacts" / "tmp" / "tests"
        self.assertEqual(fixtures.resolve(), fixtures)
        self.git(source, 'check-ignore', '-q', '--', 'artifacts/tmp/tests/')
        fixtures.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="qa-ledger-", dir=fixtures)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / "artifacts" / "reviews"
        self.git(self.root, "init", "--quiet")
        self.make_control(self.root, {"control": "."})
        cwd = patch("os.getcwd", return_value=str(self.root))
        cwd.start()
        self.addCleanup(cwd.stop)

    def run_ledger(self, *args):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = ledger.main(list(args))
        return code, output.getvalue(), errors.getvalue()

    def git(self, cwd, *args):
        return subprocess.run(["git", "-C", str(cwd), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def make_control(self, root, repos):
        (root / '.kilo').mkdir(exist_ok=True)
        (root / '.kilo/repos.json').write_text(json.dumps(repos))
        (root / 'docs').mkdir(exist_ok=True)
        (root / 'docs/BOARD.md').write_text('# Board\n')
        (root / '.gitignore').write_text('/artifacts/\n')

    def commit_fixture(self, repo):
        self.git(repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "fixture")

    def test_linked_checkout_writes_only_in_primary(self):
        self.git(self.root, "add", ".")
        self.commit_fixture(self.root)
        linked = self.root / ".kilo" / "worktrees" / "review"
        linked.parent.mkdir()
        self.git(self.root, "worktree", "add", "--quiet", "-b", "review", str(linked))
        for cwd in (self.root, linked, linked / "docs"):
            with self.subTest(cwd=cwd):
                self.assertEqual(ledger.artifact_path(cwd=cwd), str(self.directory.parent))
                with patch("os.getcwd", return_value=str(cwd)):
                    self.assertEqual(self.run_ledger("status", "--task-id", "BOARD-TEST")[0], 0)
        with patch("os.getcwd", return_value=str(linked)):
            self.assertEqual(self.run_ledger("next-round", "--task-id", "BOARD-TEST")[0], 0)
        self.assertTrue((self.directory / "BOARD-TEST-ledger.md").exists())
        for suffix in ("qa", "ui", "review", "ledger"):
            path = "artifacts/reviews/BOARD-TEST-%s.md" % suffix
            self.assertEqual(self.git(self.root, "check-ignore", path), path)
        self.assertFalse((linked / 'artifacts').exists())
        self.assertEqual(self.git(self.root, "ls-files", "artifacts"), "")

    def test_three_rounds_then_refusal_preserves_bytes_and_escalates_conditionally(self):
        args = ("--ledger-dir", str(self.directory))
        for number in range(1, 4):
            code, output, _ = self.run_ledger(*args, "next-round", "--task-id", "BOARD-TEST")
            self.assertEqual(code, 0)
            self.assertIn("round %d opened" % number, output)
        path = self.directory / "BOARD-TEST-ledger.md"
        before = path.read_bytes()
        code, _, error = self.run_ledger(*args, "next-round", "--task-id", "BOARD-TEST")
        self.assertEqual(code, 1)
        self.assertEqual(path.read_bytes(), before)
        for text in ("If round 3", "severity", "user impact", "evidence", "attempted fixes",
                     "stop reason", "orchestrator", "ask the user", "revised approach",
                     "defer/drop", "scoped follow-up", "successful round 3 does not imply blockers"):
            self.assertIn(text, error)
        code, output, _ = self.run_ledger(*args, "status", "--task-id", "BOARD-TEST")
        self.assertEqual(code, 0)
        self.assertIn("next round: none (cap reached)", output)
        self.assertNotIn("Blocked", output)

    def test_explicit_override_accepts_primary_absolute_or_relative(self):
        relative = os.path.relpath(self.directory, self.root)
        with patch("os.getcwd", return_value=str(self.root)):
            code, _, _ = self.run_ledger("--ledger-dir", str(self.directory), "next-round",
                                       "--task-id", "BOARD-TEST")
            relative_code, _, _ = self.run_ledger("--ledger-dir", relative, "next-round",
                                                "--task-id", "BOARD-RELATIVE")
        self.assertEqual(code, 0)
        self.assertEqual(relative_code, 0)
        self.assertTrue((self.directory / "BOARD-RELATIVE-ledger.md").exists())
        self.assertEqual(ledger.ledger_path("relative", "BOARD-TEST"),
                          os.path.join("relative", "BOARD-TEST-ledger.md"))

    def test_outside_directory_and_task_traversal_refuse_without_writes(self):
        for directory in (self.root / "outside", self.root / "artifacts" / ".." / "outside"):
            code, _, error = self.run_ledger("--ledger-dir", str(directory), "next-round", "--task-id", "BOARD-TEST")
            self.assertEqual(code, 1)
            self.assertIn("inside primary control artifacts/", error)
            self.assertFalse(directory.exists())
        for task in (".", "..", "../escape", "/absolute", "a/b", "a\\b", ""):
            code, _, error = self.run_ledger("--ledger-dir", str(self.directory), "next-round", "--task-id", task)
            self.assertEqual(code, 1)
            self.assertIn("safe path segment", error)
        self.assertFalse(self.directory.exists())

    def test_symlink_root_ancestors_and_ledger_refuse_without_writes(self):
        target = self.root / "target"
        target.mkdir()
        artifacts = self.root / "artifacts"
        artifacts.symlink_to(target, target_is_directory=True)
        self.assertEqual(self.run_ledger("--ledger-dir", str(self.directory), "next-round", "--task-id", "BOARD-TEST")[0], 1)
        self.assertEqual(list(target.iterdir()), [])
        artifacts.unlink()
        artifacts.mkdir()
        (artifacts / "link").symlink_to(target, target_is_directory=True)
        self.assertEqual(self.run_ledger("--ledger-dir", str(artifacts / "link" / "absent"),
                                        "next-round", "--task-id", "BOARD-TEST")[0], 1)
        self.directory.mkdir()
        (self.directory / "BOARD-TEST-ledger.md").symlink_to(target / "untouched.md")
        self.assertEqual(self.run_ledger("--ledger-dir", str(self.directory), "next-round", "--task-id", "BOARD-TEST")[0], 1)
        self.assertEqual(list(target.iterdir()), [])

    def test_unknown_control_root_refuses_without_fallback(self):
        (self.root / '.kilo/repos.json').unlink()
        code, _, error = self.run_ledger("--ledger-dir", "artifacts/reviews", "next-round", "--task-id", "BOARD-TEST")
        self.assertEqual(code, 1)
        self.assertIn("mapping the caller", error)
        self.assertFalse((self.root / "docs" / "reviews").exists())
        self.assertFalse(self.directory.exists())

    def test_nearest_mapped_project_owns_service_and_its_external_worktree(self):
        project = self.root / 'project'
        service = project / 'apps/server'
        service.mkdir(parents=True)
        self.git(project, 'init', '-q')
        self.git(service, 'init', '-q')
        self.make_control(self.root, {'control': '.', 'service': 'project/apps/server'})
        self.make_control(project, {'control': '.', 'service': 'apps/server'})
        (service / 'source').touch()
        self.git(service, 'add', 'source')
        self.commit_fixture(service)
        linked = self.root / 'external-worktree'
        self.git(service, 'worktree', 'add', '-q', '--detach', str(linked))
        for caller in (project, service, linked):
            result = subprocess.run(['python3', '-B', ledger.__file__, 'artifact-root'], cwd=caller,
                                    text=True, capture_output=True,
                                    env=dict(os.environ, GIT_DIR=str(self.root / '.git')))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, str(project / 'artifacts') + '\n')
        self.assertFalse((project / 'artifacts').exists())
        with patch('os.getcwd', return_value=str(linked)):
            self.assertEqual(self.run_ledger('next-round', '--task-id', 'BOARD-3')[0], 0)
        self.assertTrue((project / 'artifacts/reviews/BOARD-3-ledger.md').is_file())
        for other in (service, linked, self.root):
            self.assertFalse((other / 'artifacts').exists())
        foreign = project / 'apps/unmapped'
        foreign.mkdir()
        self.git(foreign, 'init', '-q')
        with self.assertRaisesRegex(ValueError, 'mapping the caller'):
            ledger.artifact_path(cwd=foreign)

    def test_tracked_added_and_staged_deleted_sibling_all_refuse(self):
        self.directory.mkdir(parents=True)
        sibling = self.directory / 'old.md'
        sibling.touch()
        self.git(self.root, 'add', '-f', str(sibling))
        for state in ('added', 'committed', 'deleted'):
            if state == 'committed':
                self.commit_fixture(self.root)
            if state == 'deleted':
                self.git(self.root, 'rm', '--cached', str(sibling))
            code, output, error = self.run_ledger('artifact-root')
            self.assertEqual((code, output), (1, ''), state)
            self.assertIn('tracked or staged', error)

    def test_mapped_identity_refuses_unregistered_gitfile_and_symlinked_map(self):
        foreign = self.root / 'foreign'
        foreign.mkdir()
        (foreign / '.git').write_text(f'gitdir: {self.root}/.git\n')
        with self.assertRaises(ValueError):
            ledger.artifact_path(cwd=foreign)
        mapping = self.root / '.kilo/repos.json'
        saved = mapping.with_name('original.json')
        mapping.rename(saved)
        mapping.symlink_to(saved)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            ledger.artifact_path(cwd=self.root)

    def test_optional_target_is_verified_without_mkdir(self):
        for target in ('artifacts/reviews', str(self.directory)):
            self.assertEqual(self.run_ledger('artifact-root', target), (0, str(self.directory) + '\n', ''))
        for target in ('artifacts/.git/x', 'artifacts/../artifacts', str(self.root / 'somewhere')):
            self.assertEqual(self.run_ledger('artifact-root', target)[:2], (1, ''))
        self.assertFalse(self.directory.exists())
        self.directory.mkdir(parents=True)
        self.git(self.directory, 'init', '-q')
        self.assertEqual(self.run_ledger('artifact-root', 'artifacts/reviews/subdir')[:2], (1, ''))

    def test_migrated_capped_ledger_is_preserved(self):
        original = self.root / "old-ledger.md"
        text = "# Historical ledger\n\n" + "".join(
            "## Round %d\n- Findings: historical evidence\n- Stop reason: capped\n\n" % n
            for n in range(1, 4))
        original.write_bytes(text.encode("utf-8"))
        self.directory.mkdir(parents=True)
        migrated = self.directory / "BOARD-OLD-ledger.md"
        shutil.copy2(original, migrated)
        args = ("--ledger-dir", str(self.directory))
        self.assertEqual(self.run_ledger(*args, "status", "--task-id", "BOARD-OLD")[0], 0)
        self.assertEqual(self.run_ledger(*args, "next-round", "--task-id", "BOARD-OLD")[0], 1)
        self.assertEqual(migrated.read_bytes(), original.read_bytes())

    def test_unreadable_ledger_does_not_become_new_history(self):
        with patch.object(ledger, "read_ledger", side_effect=PermissionError("denied")):
            code, _, error = self.run_ledger("--ledger-dir", str(self.directory), "next-round",
                                           "--task-id", "BOARD-TEST")
        self.assertEqual(code, 1)
        self.assertIn("denied", error)
        self.assertFalse(self.directory.exists())


if __name__ == "__main__":
    unittest.main()
