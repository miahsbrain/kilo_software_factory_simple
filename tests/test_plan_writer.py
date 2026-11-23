import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / '.kilo/skills/plan/scripts/plan.py'


class PlanWriterTest(unittest.TestCase):
    def git(self, *args, cwd=None):
        env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        subprocess.run(['git', *args], cwd=cwd or self.primary, env=env, check=True, capture_output=True)

    def setUp(self):
        artifacts = ROOT / 'artifacts'
        artifacts.mkdir(exist_ok=True)
        fixture = tempfile.TemporaryDirectory(dir=artifacts)
        self.addCleanup(fixture.cleanup)
        self.base = Path(fixture.name)
        self.primary = self.base / 'primary control'
        self.primary.mkdir()
        self.git('init', '-q')
        (self.primary / 'docs').mkdir()
        (self.primary / 'docs/BOARD.md').write_text('# Board\n')
        (self.primary / '.kilo').mkdir()
        self.mapping = self.primary / '.kilo/repos.json'
        self.mapping.write_text('{"control":"."}')
        self.ignore = self.primary / '.gitignore'
        self.ignore.write_text('/docs/implementation_plans/\n')
        self.plans = self.primary / 'docs/implementation_plans'
        self.target = self.plans / 'rollout-audit.md'

    def cli(self, action='create', key='rollout-audit', body=b'# Draft\n', cwd=None, **env):
        return subprocess.run([sys.executable, SCRIPT, action, key], cwd=cwd or self.primary,
                              input=body, capture_output=True, env={**os.environ, **env})

    def rejected(self, *args, **kwargs):
        result = self.cli(*args, **kwargs)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b'')
        self.assertTrue(result.stderr)
        self.assertNotIn(b'Traceback', result.stderr)

    def test_linked_control_shares_primary_and_update_replaces_inode(self):
        # Borrow an existing commit for a linked checkout without creating a commit.
        self.git('fetch', '-q', '--depth=1', str(ROOT), 'HEAD')
        linked = self.base / 'linked checkout'
        self.git('worktree', 'add', '--no-checkout', '--detach', linked, 'FETCH_HEAD')
        key = 'BOARD-123-order-cancellation'
        target = self.plans / (key + '.md')
        for action, cwd, body in [('create', linked, b'# Draft\r\n'),
                                  ('update', self.primary, b'# Final\n')]:
            with self.subTest(action=action):
                old = target.stat().st_ino if target.exists() else None
                result = self.cli(action, key, body, cwd=cwd)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, os.fsencode(target) + b'\n')
                self.assertEqual(target.read_bytes(), body)
                self.assertNotEqual(old, target.stat().st_ino)
        self.assertFalse((linked / 'docs').exists())

    def test_create_race_has_one_winner(self):
        bodies = [b'first', b'second']
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(lambda body: self.cli(body=body), bodies))
        winners = [body for body, result in zip(bodies, results) if result.returncode == 0]
        self.assertEqual(winners, [self.target.read_bytes()])
        self.assertEqual(list(self.plans.iterdir()), [self.target])

    def test_invalid_input_and_missing_update_leave_no_directory(self):
        for key in ('', '../escape', '.hidden', 'x/y', 'x\\y', 'plan.md', str(self.base / 'x')):
            with self.subTest(key=key):
                self.rejected(key=key)
        for body in (b'', b' \t\n'):
            self.rejected(body=body)
        self.rejected('update')
        self.assertFalse(self.plans.exists())

    def test_requires_ignored_directory_not_just_file(self):
        for rules in ('', '*.md\n'):
            self.ignore.write_text(rules)
            self.rejected()
            self.assertFalse(self.plans.exists())

    def test_staged_sibling_blocks_both_actions(self):
        self.plans.mkdir()
        self.target.write_text('original')
        sibling = self.plans / 'other.md'
        sibling.touch()
        self.git('add', '-f', '--', sibling)
        self.rejected(key='new', GIT_INDEX_FILE=str(self.base / 'empty-index'))
        self.rejected('update')
        self.assertEqual(self.target.read_text(), 'original')
        self.assertFalse((self.plans / 'new.md').exists())

    def test_only_control_roots_can_call(self):
        app = self.primary / 'app'
        app.mkdir()
        self.rejected(cwd=app)
        self.git('init', '-q', cwd=app)
        self.rejected(cwd=app, GIT_DIR=str(self.primary / '.git'))
        self.rejected(cwd=self.base)
        self.assertFalse(self.plans.exists())

    def test_requires_regular_board_and_valid_map(self):
        for content in ('{', '[]', '{}', '{"control":".."}'):
            self.mapping.write_text(content)
            self.rejected()
        external = self.base / 'repos.json'
        external.write_text('{"control":"."}')
        self.mapping.unlink()
        self.mapping.symlink_to(external)
        self.rejected()
        self.mapping.unlink()
        self.mapping.write_text(external.read_text())
        board = self.primary / 'docs/BOARD.md'
        board.unlink()
        self.rejected()
        board.symlink_to(external)
        self.rejected()
        self.assertFalse(self.plans.exists())

    def test_rejects_nested_destination_repo(self):
        self.plans.mkdir()
        self.git('init', '-q', cwd=self.plans)
        self.rejected()
        self.assertFalse(self.target.exists())

    def test_rejects_symlink_ancestors_and_nonregular_targets(self):
        docs = self.primary / 'docs'
        outside = self.base / 'outside'
        docs.rename(outside)
        docs.symlink_to(outside)
        self.rejected()
        docs.unlink()
        outside.rename(docs)
        outside.mkdir()
        self.plans.symlink_to(outside)
        self.rejected()
        self.assertEqual(list(outside.iterdir()), [])
        self.plans.unlink()
        self.plans.mkdir()
        victim = outside / 'victim'
        self.target.symlink_to(victim)
        self.rejected()
        self.rejected('update')
        victim.write_text('unchanged')
        self.rejected('update')
        self.assertEqual(victim.read_text(), 'unchanged')
        self.target.unlink()
        os.mkfifo(self.target)
        self.rejected('update')


if __name__ == '__main__':
    unittest.main()
