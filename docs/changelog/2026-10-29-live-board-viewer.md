# Live board viewer

**Date:** 2026-10-29
**Branch:** `feat/live-board-viewer-html-dashboard-with`
**Board:** BOARD-008

## Why

`docs/BOARD.md` is the right source of truth and the wrong dashboard. Reading it means scanning
nine columns of pipe characters and mentally reconstructing which lanes have work in them. The
question it should answer at a glance is: **what is happening right now?**

## What it is

A read-only Python server that renders the board and the live worktree state:

```bash
python3 .kilo/skills/board/scripts/board_serve.py --port 15180
```

- **One column per lane**, in flow order — `Backlog`, `Ready`, `In Progress`, `In Review`,
  `Pending Merge`, `Merged`, `Blocked`, `Dropped`. Empty lanes still render, so the shape of the
  flow is always visible.
- **Cards** show the ID, task, type, priority, risk badge, `Blocked by`, and the worktree.
- **A live worktrees panel** — every worktree with its branch, path, commits ahead and behind,
  and a dirty marker. The main checkout is listed too, marked as such.
- **Never cached.** The board is re-read on every request; the page auto-refreshes every 10
  seconds.
- **Read-only.** It writes nothing to the board or the repository. The board stays owned by the
  orchestrator; the viewer only renders it.
- `/api/board` and `/api/worktrees` serve the same data as JSON.

Port 15180 is forwarded by the devcontainer as **Factory Board**.

## Two bugs found and fixed along the way

**The board could be corrupted by a value.** A `--note` containing newlines produced a row that
ended at the first line, leaving the rest as orphan text outside the table — and the parser then
saw a malformed board. `board.py` now refuses any cell value containing a newline or a raw pipe,
naming the offending argument and saying what to do instead. It caught a real mistake in this
session: the BOARD-008 row itself was written with a multi-line note.

**The slug could cut mid-phrase.** "Live board viewer: HTML dashboard with lanes and worktrees on
a forwarded port" became `live-board-viewer-html-dashboard-with`, because the 6-word cap stopped
after the connective. Trailing connective words are now dropped after the cap, giving
`live-board-viewer-html-dashboard`. Short titles are untouched.

## Design

The page follows the factory's own anti-slop rules: one accent colour, a real type scale,
asymmetry rather than a centred stack, status colours used only for status, system fonts, and no
network requests at all — it renders fully offline. Light and dark follow the OS preference.
Every value from the board or from git is HTML-escaped, because board cells are untrusted text.
