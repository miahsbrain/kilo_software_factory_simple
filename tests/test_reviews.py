import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CLI = Path(__file__).resolve().parents[1] / ".claude/skills/git-worktree/scripts/worktree.py"


class ReviewSwitchTests(unittest.TestCase):
    def setUp(self):
        fixture = tempfile.TemporaryDirectory(prefix="review-switches-")
        self.addCleanup(fixture.cleanup)
        self.root = Path(fixture.name) / "factory"
        self.root.mkdir()
        self.git(self.root, "init")
        (self.root / ".claude").mkdir()
        (self.root / "docs").mkdir()
        (self.root / "docs/BOARD.md").touch()
        self.map = self.root / ".claude/repos.json"
        self.map.write_text('{"control":"."}')
        self.state = self.root / ".git/claude-workspace.json"

    def git(self, cwd, *args):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
        subprocess.run(["git", "-c", "core.hooksPath=" + os.devnull, "-c", "user.name=Test",
                        "-c", "user.email=test@example.invalid", *args], cwd=cwd,
                       env=env, capture_output=True, check=True)

    def reviews(self, *args, cwd=None, code=0):
        result = subprocess.run([sys.executable, CLI, "reviews", *args], cwd=cwd or self.root,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, code, result.stderr)
        if code:
            self.assertEqual(result.stdout, "")
            self.assertTrue(result.stderr)
        return result.stdout

    def test_independent_switches_preserve_mode_permissions_and_metadata(self):
        self.assertEqual(self.factory_status(), {"mode": "required", "qa": True, "ui": True})
        enabled = '{"qa":true,"ui":true}\n'
        self.assertEqual(self.reviews("status"), enabled)
        self.assertFalse(self.state.exists())
        baseline = {"mode": "adaptive", "workspaces": {"record": {}}, "other": [1]}
        self.state.write_text(json.dumps(baseline))
        config = self.root / "kilo.jsonc"
        config.write_bytes(b'// fixture permission config\n{}\n')
        for args, expected in [("qa off", '{"qa":false,"ui":true}\n'),
                               ("ui off", '{"qa":false,"ui":false}\n'),
                               ("qa on", '{"qa":true,"ui":false}\n'),
                               ("both off", '{"qa":false,"ui":false}\n'), ("both on", enabled)]:
            self.assertEqual(self.reviews(*args.split()), expected)
            self.assertEqual(self.reviews("status"), expected)
            self.assertEqual(self.factory_status(), {"mode": "adaptive", **json.loads(expected)})
            self.assertEqual(json.loads(self.state.read_text()), {**baseline, "reviews": json.loads(expected)})
        self.assertEqual(config.read_bytes(), b'// fixture permission config\n{}\n')

    def factory_status(self, cwd=None):
        result = subprocess.run([sys.executable, CLI, "status"], cwd=cwd or self.root,
                                capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    def test_control_and_mapped_app_linked_worktrees_share_control_state(self):
        app = self.root / "app"
        app.mkdir()
        self.git(app, "init")
        self.map.write_text('{"control":".","app":"app"}')
        for repo in (self.root, app):
            self.git(repo, "commit", "--allow-empty", "-m", "disposable fixture")
            linked = repo / ".claude/worktrees/linked"
            self.git(repo, "worktree", "add", "--detach", str(linked))
            nested = linked / "nested"
            nested.mkdir()
            self.assertEqual(self.reviews("ui", "off", cwd=nested), '{"qa":true,"ui":false}\n')
            self.assertEqual(self.reviews("status"), self.reviews("status", cwd=nested))
            self.assertEqual(self.factory_status(nested), {"mode": "required", "qa": True, "ui": False})
            self.reviews("both", "on")
        self.assertFalse((app / ".git/claude-workspace.json").exists())

    def test_malformed_state_is_not_reset(self):
        for reviews in (None, [], {}, {"qa": True}, {"qa": 0, "ui": True},
                        {"qa": True, "ui": "off"}, {"qa": True, "ui": True, "x": True}):
            state = {"mode": "required", "workspaces": {}, "reviews": reviews}
            self.assert_refused_state(json.dumps(state))
        for raw in ("[", "[]", "{}"):
            self.assert_refused_state(raw)

    def assert_refused_state(self, raw):
        self.state.write_text(raw)
        for args in (("status",), ("both", "off")):
            self.reviews(*args, code=1)
            self.assertEqual(self.state.read_text(), raw)

    def test_unmapped_or_outside_caller_cannot_write(self):
        for cwd in (self.root / "unmapped", self.root.parent / "outside"):
            cwd.mkdir()
            self.git(cwd, "init")
            self.reviews("both", "off", cwd=cwd, code=1)
            self.assertFalse((cwd / ".git/claude-workspace.json").exists())
        self.assertFalse(self.state.exists())

    def test_usage_errors_do_not_write(self):
        for args in ((), ("status", "off"), ("qa",), ("ui", "false")):
            self.reviews(*args, code=2)
        self.assertFalse(self.state.exists())


if __name__ == "__main__":
    unittest.main()
