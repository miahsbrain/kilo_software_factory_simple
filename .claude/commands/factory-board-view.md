---
description: Serve the read-only live board viewer
---

Start `python3 .claude/skills/board/scripts/board_serve.py --port 15180` with the Bash tool's `run_in_background` option. Report its URL and actual readiness; in the desktop app you may open it in the integrated browser. The viewer reads the board and worktree state without editing either; bind beyond loopback only when required and authorized.
