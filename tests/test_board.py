import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

FACTORY = Path(__file__).resolve().parents[1]
BOARD_CLI = FACTORY / '.claude/skills/board/scripts/board.py'


class TitleTests(unittest.TestCase):
    def test_generated_titles_preserve_vocabulary_and_are_idempotent(self):
        spec = importlib.util.spec_from_file_location('board_titles', BOARD_CLI)
        board = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(board)
        for source, expected in (
            ('feat(web): rewrite the HTTP client', 'Rewrote the HTTP client'),
            ('[Feature] web: build a CLI', 'Built a CLI'),
            ('fix/ web - simplify OAuth2', 'Simplified OAuth2'),
            ('update docs', 'Updated docs'),
            ('added API support', 'Added API support'),
            ('add\U0001f469\U0001f3fd\u200d\U0001f4bbAPI 1\ufe0f\u20e3 v2', 'Added API v2'),
            ('Build pipeline', 'Build pipeline'), ('Test coverage', 'Test coverage'),
            ('WebSocket retry', 'WebSocket retry'), ('xAPI: add docs', 'xAPI: add docs'),
            ('re-add TLS', 're-add TLS'), ('ADD opcode', 'ADD opcode'),
            ('add C# and UTF-8', 'Added C# and UTF-8'),
        ):
            with self.subTest(source=source):
                self.assertEqual(board.generated_title(source, {'web'}), expected)
                self.assertEqual(board.generated_title(expected, {'web'}), expected)


class ManualReviewTests(unittest.TestCase):
    def setUp(self):
        fixtures = FACTORY / 'artifacts/tmp/tests'
        self.assertEqual(fixtures.resolve(), fixtures)
        fixtures.mkdir(parents=True, exist_ok=True)
        temp = tempfile.TemporaryDirectory(prefix='board-', dir=fixtures)
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'BOARD.md'
        self.path.write_text((FACTORY / 'templates/project/docs/BOARD.md').read_text())

    def cli(self, *args, expected=0):
        result = subprocess.run([sys.executable, str(BOARD_CLI), '--file', str(self.path), *args],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stderr)
        return result.stdout

    def add(self, blockers='review:flow-v1', lane='Blocked', row='A', expected=0):
        self.cli('add', '--id', row, '--task', 'Checkout', '--type', 'Fix', '--status', lane,
                 '--priority', 'P2', '--risk', 'low', '--blocked-by', blockers,
                 '--fingerprint', 'bug|ui|checkout|flow', '--note', 'Existing checks', expected=expected)

    def approve(self, evidence='User decision #42', expected=0):
        self.cli('approve-review', 'A', '--scope', 'flow-v1', '--evidence', evidence, expected=expected)

    def test_add_names_only_new_task_cell(self):
        root = self.path.parent
        (root / '.claude').mkdir()
        (root / '.claude/repos.json').write_text('{"billing":"apps/payments"}')
        (root / 'frontend').mkdir()
        legacy = '\U0001f680 [feat] inhouz_agentic_ms: add kus deployment manifests'
        for row, task, name in [('A', legacy, 'Added kus deployment manifests'),
                                ('B', '[billing] frontend: payments: write docs', 'Wrote docs')]:
            before = self.path.read_text().splitlines()
            self.cli('add', '--id', row, '--task', task, '--type', 'Feature', '--status', 'Ready',
                     '--priority', 'P2', '--risk', 'low', '--note', legacy)
            shown = self.cli('show', row)
            self.assertTrue(shown.startswith(f'{row} | {name} | Feature |'), shown)
            self.assertIn(legacy, shown)
            self.assertTrue(all(line in self.path.read_text().splitlines() for line in before))
        before = self.path.read_bytes()
        self.cli('add', '--id', 'C', '--task', '\U0001f680 [feat]', '--type', 'Feature',
                 '--status', 'Ready', '--priority', 'P2', '--risk', 'low', expected=66)
        self.assertEqual(self.path.read_bytes(), before)

    def test_only_matching_gate_returns_to_review_with_visible_evidence(self):
        self.add()
        self.approve()
        output = self.cli('show', 'A')
        self.assertIn(' | In Review | P2 | low | - None. |', output)
        self.assertIn('Existing checks · [user-approved:flow-v1] User decision #42', output)
        self.approve()
        self.assertEqual(self.cli('show', 'A'), output)
        self.add(row='B', expected=1)
        self.assertEqual(self.cli('show'), output)

    def test_mixed_blockers_are_not_cleared(self):
        self.add('DEP-2; review:flow-v1; review:flow-v10; login broken')
        self.approve()
        self.assertIn(' | Blocked | P2 | low | DEP-2; review:flow-v10; login broken |',
                      self.cli('show', 'A'))

    def test_rephrased_retry_preserves_first_evidence_without_rewriting(self):
        self.add()
        self.approve('Message 42 · checkout accepted')
        self.cli('set-field', 'A', '--field', 'blocked-by', '--value', 'review:flow-v2; DEP-2')
        self.cli('set-status', 'A', 'Blocked')
        before = self.path.read_bytes()
        inode = self.path.stat().st_ino
        self.approve('User confirmed in message 42')
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.path.stat().st_ino, inode)

    def test_late_decision_cannot_record_approval_for_a_different_gate(self):
        self.add('review:flow-v10; DEP-2')
        before = self.path.read_bytes()
        self.approve(expected=1)
        self.assertEqual(self.path.read_bytes(), before)

    def test_legacy_unclassified_blocker_stays_blocked(self):
        self.add('Waiting for review and a security fix')
        self.approve()
        self.assertIn(' | Blocked | P2 | low | Waiting for review and a security fix |',
                      self.cli('show', 'A'))

    def test_explicit_escalation_survives_approval(self):
        self.add()
        self.cli('note', 'A', '--value', 'Authentication failed', '--escalate')
        self.approve()
        self.assertIn(' | Blocked | P2 | low | Escalation: Authentication failed |', self.cli('show'))

    def test_evidence_is_required_and_never_advances_implementation(self):
        self.add(lane='In Progress')
        before = self.path.read_bytes()
        for evidence in (' ', 'decision\nother', 'a|b'):
            self.approve(evidence, expected=66)
            self.assertEqual(before, self.path.read_bytes())
        self.approve()
        self.assertIn(' | In Progress |', self.cli('show'))

    def test_lifecycle_lanes_are_untouched(self):
        self.add()
        for lane in ('Pending Merge', 'Merged', 'Dropped'):
            self.cli('set-status', 'A', lane)
            before = self.path.read_bytes()
            self.approve(expected=1)
            self.assertEqual(before, self.path.read_bytes())
