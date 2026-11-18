---
description: Serve the read-only live board viewer
---

Start `python3 .kilo/skills/board/scripts/board_serve.py --port 15180` as a tracked background process. Report its URL and actual readiness. The viewer reads the board and worktree state without editing either; bind beyond loopback only when required and authorized.
