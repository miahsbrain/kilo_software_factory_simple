# QA capture — BOARD-012

- Command: `/usr/local/bin/node /workspaces/kilo_software_factory_simple/.kilo/worktrees/remove-cdp-and-report-failures/.kilo/skills/qa-review/scripts/browser-review.mjs --base-url http://127.0.0.1:18123 --route / --scope factory --task-id BOARD-012 --project /tmp/kilo/no-such-project --viewports 1440x900`
- Scope: factory
- Task: BOARD-012
- Date: 2026-10-29
- Routes: /
- Viewports: 1440x900
- Schemes: light

| Scheme | Console errors | Page errors | Network failures |
|---|---|---|---|
| light | 1 | 0 | 0 |

The one console error is the static test page's missing favicon (404 on `/favicon.ico`).

## What was checked

| Check | Expected | Actual | Result |
|---|---|---|---|
| Missing chromium is reported | exit 2, the searched list, the three ways out, no install | exit 2 with the full message; nothing installed, no other driver used | pass |
| Chromium found, capture runs | exit 0, screenshot plus console, page-error and network files, `summary.json` | exit 0, `browser_executable: /usr/bin/chromium`, artifacts written, no overflow | pass |
| `--chromium <path>` reaches Playwright | the given binary is launched | `--chromium /usr/bin/chromium` launched that binary through Playwright | pass |

Commands:

```bash
node .kilo/skills/qa-review/scripts/browser-review.mjs --base-url http://127.0.0.1:9 --route / \
    --project /tmp/kilo/no-such-project --chromium /nonexistent/chromium   # exit 2
node .kilo/skills/qa-review/scripts/browser-review.mjs --base-url http://127.0.0.1:18123 --route / \
    --scope factory --task-id BOARD-012 --project /tmp/kilo/no-such-project --viewports 1440x900
```
