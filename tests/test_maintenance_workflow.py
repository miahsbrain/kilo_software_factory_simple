import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


FACTORY = Path(__file__).resolve().parents[1]
BOARD = FACTORY / '.kilo/skills/board/scripts/board.py'
WORKTREE = FACTORY / '.kilo/skills/git-worktree/scripts/worktree.py'


class MaintenanceWorkflowTests(unittest.TestCase):
    def test_adaptive_checkout_and_scoped_acceptance(self):
        fixtures = FACTORY / 'artifacts/tmp/tests'
        self.assertEqual(fixtures.resolve(), fixtures)
        fixtures.mkdir(parents=True, exist_ok=True)
        temp = tempfile.TemporaryDirectory(prefix='maintenance-', dir=fixtures)
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        path = root / 'docs/BOARD.md'
        path.parent.mkdir()
        shutil.copyfile(FACTORY / 'templates/project/docs/BOARD.md', path)
        policy = Path('.kilo/policies/git-policy.json')
        (root / policy.parent).mkdir(parents=True)
        shutil.copyfile(FACTORY / policy, root / policy)
        shutil.copyfile(FACTORY / 'kilo.jsonc', root / 'kilo.jsonc')
        (root / '.kilo/repos.json').write_text('{"control":"."}\n')
        env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_') and k != 'KILO_CONFIG'}
        env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1', PYTHONDONTWRITEBYTECODE='1')

        def run(*args, refusal=None):
            result = subprocess.run(args, cwd=root, env=env, capture_output=True, text=True, timeout=30)
            if refusal is None:
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            else:
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(refusal, result.stderr)
            return result.stdout.strip()

        row = 'BOARD-002'
        board = (sys.executable, BOARD, '--file', path)
        worktree = (sys.executable, WORKTREE)
        skip = (*worktree, 'create', '--board', row, '--repo', 'control', '--skip-worktree')
        run('git', 'init', '-b', 'main')
        run(*board, 'add', '--id', row, '--task', 'Refresh guidance', '--type', 'Docs',
            '--status', 'Ready', '--priority', 'P2', '--risk', 'low', '--blocked-by', '- None.',
            '--repos', 'control', '--note', 'Check the wording')
        run(*worktree, 'mode', 'adaptive')
        self.assertIn('adaptive', run(*worktree, 'mode', 'status'))
        before = path.read_bytes()
        run(*skip, refusal='protected branch')
        self.assertEqual(run('git', 'symbolic-ref', '--short', 'HEAD'), 'main')
        run('git', 'switch', '-c', 'docs/current')
        checkouts = run('git', 'worktree', 'list', '--porcelain')
        run(*skip)
        self.assertEqual(path.read_bytes(), before)

        run(*board, 'set-field', row, '--field', 'blocked-by', '--value', 'review:wording; BOARD-001')
        run(*skip, refusal='dependency')
        run(*board, 'set-status', row, 'Blocked')
        approve = (*board, 'approve-review', row, '--scope', 'wording', '--evidence', 'Fixture decision 42')
        run(*approve)
        shown = run(*board, 'show', row)
        self.assertIn(' | Blocked | P2 | low | BOARD-001 | control | - |', shown)
        self.assertIn('[user-approved:wording] Fixture decision 42', shown)
        run(*skip, refusal='Ready or In Progress')
        self.assertEqual(run('git', 'worktree', 'list', '--porcelain'), checkouts)
