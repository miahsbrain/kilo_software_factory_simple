# STACK

Approved stack, package managers, commands, and ports. This is the first source for any command
an agent needs. Do not guess commands. Do not read `docs/ENVIRONMENT.md` for stack information.

## How to run in development

```bash
# Board viewer (from the repo root)
python3 .kilo/skills/board/scripts/board_serve.py --port 15180

# API/services (from apps/api/)
TBD

# Web (from apps/web/)
TBD

# Mobile (from apps/mobile/), when applicable
TBD
```

The board viewer is read-only: it serves the board and the live worktree state, and never writes
to either. It re-reads `docs/BOARD.md` on every request, so the page is always current.

## Web

Stack: TBD
Package manager: TBD
Dev command: TBD
Verification command: TBD
Port: 15173

## Board viewer

Tool: Python 3 standard library server (`board_serve.py`), no dependencies
Port: 15180
Dev command: `python3 .kilo/skills/board/scripts/board_serve.py --port 15180`
Host: `127.0.0.1` by default; `--host 0.0.0.0` to bind wider
Refresh: the page re-reads the board every request and auto-refreshes every 10 seconds

## Playwright

Tool: the global install the devcontainer provides, plus the Playwright MCP
Library: `/usr/local/share/npm-global/lib/node_modules/@playwright/mcp/node_modules/playwright`
MCP server: `playwright-mcp` (on PATH), configured in `kilo.jsonc`
Browser: system chromium at `/usr/bin/chromium` — the container sets
`PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1`, so there is no downloaded browser

The QA capture script uses the project's own Playwright when it has one, and the global install
otherwise. It never installs anything.

Browser resolution, highest priority first:

1. `--chromium <path>`
2. `PLAYWRIGHT_CHROMIUM_PATH`
3. the browser Playwright downloaded
4. the system chromium: `/usr/bin/chromium`, `/usr/bin/chromium-browser`, `which chromium`

When no chromium is found, the capture script exits 2 and prints the list of places it searched
plus the commands that point it at a binary. It never installs a browser and never falls back to
another driver.

## Mobile

Stack: TBD
Package manager: TBD
Dev command: TBD
Verification command: TBD
Port: TBD

## API and Services

Stack: TBD
Package manager: TBD
Dev command: TBD
Verification command: TBD
Port: TBD

## Database

Database: TBD

## Auth

Auth approach: TBD

## Notes

- Update this file after the user approves a stack or after targeted discovery confirms values.
- Pass the relevant stack and command to builders instead of making them discover it.
