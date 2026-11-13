---
description: Serve the live board dashboard in a browser — lanes, cards, and running worktrees
---

Start the read-only board viewer and hand the user the URL.

For UI verification/review of the viewer or `/gallery`, follow `AGENTS.md` §B4.2 and the QA skill:
use the Playwright capture script and configured MCP; hold unavailable criteria without substitution.

```bash
python3 .opencode/skills/board/scripts/board_serve.py --port 15180
```

- It serves the Git-common-dir SQLite board and live `git worktree list` state, re-read on request.
- Startup imports an existing local legacy board once or initializes empty; requests are read-only.
- `docs/BOARD.md` is legacy input, not live state. `board.py export` generates Markdown on demand.
- `--host 0.0.0.0` binds wider when the port must be reached from outside the container.
- `--open` opens the URL in the default browser when that is available.
- `--refresh N` changes the page auto-refresh interval in seconds (default 10).

Endpoints:

| Path | Serves |
|---|---|
| `/` | the dashboard HTML |
| `/api/board` | the board rows and lane counts as JSON |
| `/api/worktrees` | the live worktree state as JSON |
| `/health` | `{"ok": true}` |

The port is forwarded by the devcontainer as **Factory Board (15180)**.

Run it in the background so the user can keep working while it stays up, then report the URL and
what the page shows: the lanes, the cards in each lane, and the worktrees currently running with
their ahead/behind counts.
