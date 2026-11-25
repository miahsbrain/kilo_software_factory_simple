import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


CLI = Path(__file__).resolve().parents[1] / '.claude/skills/qa-review/scripts/check-finding.py'
SECTION = '''## BOARD-021: Chat readability
Changed: Conversation text is larger.
Setup: Open the chat fixture.
- [ ] Open a long message. Check that the text wraps.
'''


class ManualGuideTests(unittest.TestCase):
    def setUp(self):
        scratch = CLI.parents[4] / 'artifacts/tmp/tests'
        scratch.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)
        self.guide = self.repo / 'artifacts/reviews/chat.md'
        self.guide.parent.mkdir(parents=True)
        self.guide.write_text(SECTION)
        subprocess.run(['git', 'init', '-q'], cwd=self.repo, check=True)
        (self.repo / '.gitignore').write_text('/artifacts/\n')
        (self.repo / 'docs').mkdir()
        (self.repo / 'docs/BOARD.md').touch()
        (self.repo / '.claude').mkdir()
        (self.repo / '.claude/repos.json').write_text('{"control":".","web":"apps/web"}')

    def check_path(self, path, **kwargs):
        return subprocess.run([sys.executable, '-B', CLI, '--manual-guide', '--body-file', path],
                              cwd=kwargs.pop('cwd', self.repo), text=True, capture_output=True, **kwargs)

    def validate(self, body):
        self.guide.write_text(body)
        return self.check_path(self.guide.relative_to(self.repo))

    def test_requires_regular_markdown_inside_reviews(self):
        for name in ('outside.md', 'artifacts/other.md', 'artifacts/reviews/chat.txt'):
            (self.repo / name).write_text(SECTION)
        os.mkfifo(self.guide.with_name('pipe.md'))
        for path in ('-', 'outside.md', 'artifacts/other.md', 'artifacts/reviews/chat.txt',
                     'artifacts/reviews/pipe.md', 'artifacts/reviews/../reviews/chat.md',
                     'artifacts/reviews/missing.md'):
            with self.subTest(path=path):
                self.assertEqual(self.check_path(path, input=SECTION, timeout=5).returncode, 66)
        self.assertEqual(self.check_path('artifacts/reviews/chat.md', cwd=self.guide.parent).returncode, 0)

    def test_mapped_service_validates_only_projects_guide(self):
        service = self.repo / 'apps/web'
        service.mkdir(parents=True)
        subprocess.run(['git', 'init', '-q'], cwd=service, check=True)
        relative = self.guide.relative_to(self.repo)
        local = service / relative
        local.parent.mkdir(parents=True)
        local.write_text('invalid source-local guide')
        self.assertEqual(self.check_path(relative, cwd=service).returncode, 0)
        self.assertEqual(self.check_path(local, cwd=service).returncode, 66)
        self.guide.unlink()
        self.assertEqual(self.check_path(relative, cwd=service).returncode, 66)

    def test_refuses_symlink_file_and_ancestor_even_with_internal_target(self):
        link = self.guide.with_name('link.md')
        link.symlink_to(self.guide)
        self.assertEqual(self.check_path(link).returncode, 66)
        self.guide.parent.rename(self.guide.parent.with_name('original'))
        self.guide.parent.symlink_to('original', target_is_directory=True)
        self.assertEqual(self.check_path(self.guide).returncode, 66)

    def test_refuses_nested_repository(self):
        subprocess.run(['git', 'init', '-q'], cwd=self.guide.parent, check=True)
        self.assertEqual(self.check_path(self.guide).returncode, 66)

    def test_requires_ignored_artifacts_root_not_just_ignored_guide(self):
        (self.repo / '.gitignore').write_text('*.md\n')
        self.assertEqual(self.check_path(self.guide).returncode, 66)

    def test_git_checks_fail_closed(self):
        # Simulate index entries, staged deletions, and Git failures without staging fixtures.
        real_git = shutil.which('git')
        wrapper = self.repo / 'git'
        wrapper.write_text('''#!/bin/sh
if [ "$1" = "$PROBE" ] && { [ -z "$TARGET" ] || [ "$4" = "$TARGET" ]; }; then
    if [ "$STATUS" = 0 ]; then printf 'artifacts/other/sibling.txt\\n'; fi
    exit "$STATUS"
fi
exec "$REAL_GIT" "$@"
''')
        wrapper.chmod(0o700)
        for probe, target, status in [('ls-files', '', 0), ('diff', '', 0), ('diff', '', 128),
                                      ('ls-files', '', 128), ('rev-parse', '', 128),
                                      ('check-ignore', 'artifacts/reviews/chat.md', 1)]:
            with self.subTest(probe=probe, status=status):
                env = dict(os.environ, PATH=f'{self.repo}:{os.environ["PATH"]}', REAL_GIT=real_git,
                           PROBE=probe, TARGET=target, STATUS=str(status))
                result = self.check_path(self.guide, env=env)
                self.assertEqual(result.returncode, 66, result.stdout)
                self.assertFalse(result.stdout)

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

    def test_short_tester_steps_instead_of_review_paragraphs(self):
        for step in ('Open a long message. Check that the text is easy to read.',
                     'Send a message and confirm you get a reply.'):
            self.assertEqual(self.validate(SECTION + '- [ ] ' + step).returncode, 0)
        verbose = ('Open the chat panel and confirm that a reply appears. Before completing the review, '
                   'look at the historical branch changes and compare the saved test evidence.')
        self.assertIn('shorten', self.validate(SECTION + '- [ ] ' + verbose).stderr)

    def test_rejects_missing_section_and_indented_code(self):
        for body in ('', '# Builder QA', '    ' + SECTION.replace('\n', '\n    ')):
            with self.subTest(body=body):
                self.assertEqual(self.validate(body).returncode, 66)

    def test_default_mode_still_requires_a_finding(self):
        result = subprocess.run([sys.executable, CLI, '--body-file', __file__],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 66)
        self.assertIn('body is missing required section: ## Summary', result.stderr)
