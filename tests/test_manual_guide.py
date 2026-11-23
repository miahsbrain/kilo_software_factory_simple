import subprocess
import sys
import unittest
from pathlib import Path


CLI = Path(__file__).resolve().parents[1] / '.kilo/skills/qa-review/scripts/check-finding.py'
SECTION = '''## BOARD-021: Chat readability
Changed: Conversation text is larger.
Setup: Open the chat fixture.
- [ ] Open a long message. Check that the text wraps.
'''


class ManualGuideTests(unittest.TestCase):
    def validate(self, body):
        return subprocess.run([sys.executable, CLI, '--manual-guide', '--body-file', '-'],
                              input=body, text=True, capture_output=True)

    def test_accepts_each_section_and_labeled_notes(self):
        second = '''## BOARD-019: Live builder chat
Changed: Replies stream in the chat panel.
Blocked: Wait for the route to be enabled.
- [ ] Sign in on the intended hostname. Check that chat opens.
- [ ] From the project root, run `git status`. Check for a clean working tree.
- [ ] Check each assumption against the plan. Note any mismatch.
Not ready to test: Skip the unimplemented panel.
'''
        result = self.validate('# Builder manual QA\n\n' + SECTION + second)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('fingerprint', result.stdout)

    def test_refuses_nonconforming_lines_even_after_valid_section(self):
        for invalid in ('Here is the rest of the guide.', '| Action | Expected |',
                        '## BOARD-: Chat', '## BOARD-021: ', '### BOARD-022: Chat',
                        SECTION.replace('Changed:', 'Notes:'), SECTION.replace('- [ ]', '- [x]'),
                        SECTION.replace('- [ ]', '- [X]'), SECTION.replace('Changed: Conversation text is larger.', 'Changed:'),
                        SECTION.split('- [ ]')[0], SECTION.replace(' Check that the text wraps.', ''),
                        SECTION.replace('Open a long message.', 'The tester opened a message.'),
                        '- [ ] Open the `check for status` command.', '- [ ] Open chat. Check that.'):
            with self.subTest(invalid=invalid):
                result = self.validate(SECTION + invalid)
                self.assertEqual(result.returncode, 66, result.stdout)
                self.assertTrue(result.stderr)
                self.assertFalse(result.stdout)

    def test_requires_a_section_and_rejects_indented_code(self):
        for body in ('', '# Builder QA', '    ' + SECTION.replace('\n', '\n    ')):
            with self.subTest(body=body):
                self.assertEqual(self.validate(body).returncode, 66)

    def test_default_mode_still_requires_a_finding(self):
        result = subprocess.run([sys.executable, CLI, '--body-file', __file__],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 66)
        self.assertIn('body is missing required section: ## Summary', result.stderr)
