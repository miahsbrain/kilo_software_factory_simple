#!/usr/bin/env python3
"""Read-only live board dashboard.

    board_serve.py [--port 15180] [--host 127.0.0.1] [--open]
                   [--file PATH] [--refresh 10]

Serves a single-page HTML dashboard of docs/BOARD.md plus the live git
worktrees. Everything is read fresh on every request and nothing is ever
written: the board file and the repository are only read.

Endpoints:
    GET /                the HTML dashboard
    GET /api/board       JSON: rows, lanes, generated_at
    GET /api/worktrees   JSON: the list of worktrees
    GET /health          JSON: {"ok": true}

Standard library only. Python 3.9+.
"""
import argparse
import datetime
import html
import importlib.util
import json
import os
import re
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LANES = ["Backlog", "Ready", "In Progress", "In Review", "Pending Merge",
         "Merged", "Blocked", "Dropped"]
ACTIVE_LANES = ["Ready", "In Progress", "In Review", "Pending Merge", "Blocked"]
HISTORICAL_LANES = ["Backlog", "Merged", "Dropped"]
LANE_ORDER = ACTIVE_LANES + HISTORICAL_LANES
COLLAPSED_BY_DEFAULT = {"Backlog", "Merged", "Dropped"}
MERGED_PREVIEW = 10
LANE_DESCRIPTION = {
    "Backlog": "Identified, not started",
    "Ready": "Scoped and pickable",
    "In Progress": "Build lane running",
    "In Review": "QA and review running",
    "Pending Merge": "Green, waiting for approval",
    "Merged": "Merged into the base branch",
    "Blocked": "Parked for a human decision",
    "Dropped": "Abandoned",
}
EMPTY_TEXT = {
    "Backlog": "Nothing in the backlog. Name the next task.",
    "Ready": "Nothing ready. Add a row with board.py add.",
    "In Progress": "Nothing in progress.",
    "In Review": "Nothing in review.",
    "Pending Merge": "Nothing waiting for merge.",
    "Merged": "No merged work yet.",
    "Blocked": "Nothing blocked.",
    "Dropped": "Nothing dropped.",
}
COLUMNS = ["ID", "Task", "Type", "Status", "Priority", "Risk", "Blocked by",
           "Repos", "Branch/Worktree", "Notes"]
GIT_TIMEOUT = 5
DEFAULT_PORT = 15180
DEFAULT_HOST = "127.0.0.1"
DEFAULT_REFRESH = 10
# Inline favicon: the page stays offline and makes no favicon request.
FAVICON = ("data:image/svg+xml,"
           "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E"
           "%3Crect width='16' height='16' rx='3' fill='%232f6feb'/%3E%3C/svg%3E")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def script_dir():
    return os.path.dirname(os.path.abspath(__file__))


def load_helpers():
    """board.py and worktree.py, loaded by path so the script runs from anywhere."""
    here = script_dir()
    board = load_module("board", os.path.join(here, "board.py"))
    wt_path = os.path.join(here, "..", "..", "git-worktree", "scripts", "worktree.py")
    worktree = load_module("worktree", os.path.abspath(wt_path))
    return board, worktree


def git_out(worktree, path, *args):
    """Output of a git command, or None when it fails or times out."""
    try:
        code, out, _ = worktree.git(path, *args, timeout=GIT_TIMEOUT)
    except Exception:
        return None
    return out if code == 0 else None


def repo_root(worktree, cwd):
    root = worktree.main_checkout_root(cwd)
    if root and os.path.isdir(root):
        return root
    return worktree.script_root()


def board_file(path, root):
    if path:
        return os.path.abspath(path)
    return os.path.join(root, "docs", "BOARD.md")


def discover_boards(root):
    """[(label, path)] for the harness board and the project board, when both exist.

    The factory root has no DOMAIN.md; the project root has one. From either root the
    sibling board is found, so one server shows both boards.
    """
    root = os.path.abspath(root)
    is_project = os.path.exists(os.path.join(root, "DOMAIN.md"))
    boards = []
    if is_project:
        boards.append(("project", os.path.join(root, "docs", "BOARD.md")))
        parent = os.path.dirname(root)
        if (os.path.exists(os.path.join(parent, ".kilo"))
                and os.path.exists(os.path.join(parent, "docs", "BOARD.md"))):
            boards.append(("harness", os.path.join(parent, "docs", "BOARD.md")))
    else:
        boards.append(("harness", os.path.join(root, "docs", "BOARD.md")))
        child = os.path.join(root, "project", "docs", "BOARD.md")
        if os.path.exists(child):
            boards.append(("project", child))
    return [(label, path) for label, path in boards if os.path.exists(path)]


def read_rows(board, path):
    """(rows, error). The board is read fresh; nothing is cached."""
    table, err = board.read_table(path)
    if table is None:
        return [], err
    rows = []
    for i in table["rows"]:
        cells = board.cell_texts(table["lines"], i)
        if len(cells) < len(COLUMNS):
            cells = cells + [""] * (len(COLUMNS) - len(cells))
        row = dict(zip(COLUMNS, cells))
        row["Notes"] = " ".join(row["Notes"].split())
        row["Notes raw"] = cells[COLUMNS.index("Notes")]
        rows.append(row)
    return rows, None


def lane_map(rows):
    lanes = {lane: [] for lane in LANES}
    for row in rows:
        lanes.setdefault(row["Status"], []).append(row["ID"])
    return lanes


def worktree_state(worktree, root):
    """One entry per git worktree, including the main checkout."""
    entries = []
    listed = worktree.list_worktrees(root)
    main_path = os.path.realpath(listed[0]["path"]) if listed else None
    for wt in listed:
        path = os.path.abspath(wt["path"])
        branch = wt["branch"]
        short_sha = git_out(worktree, path, "rev-parse", "--short", "HEAD")
        if short_sha is None:
            short_sha = (wt["head"] or "")[:7] or None
        ahead = git_out(worktree, path, "rev-list", "--count", "main..HEAD")
        behind = git_out(worktree, path, "rev-list", "--count", "HEAD..main")
        dirty = git_out(worktree, path, "status", "--porcelain")
        entries.append({
            "path": path,
            "branch": branch or "(detached)",
            "sha": short_sha,
            "ahead": int(ahead) if ahead and ahead.isdigit() else None,
            "behind": int(behind) if behind and behind.isdigit() else None,
            "dirty": bool(dirty),
            "main": os.path.realpath(path) == main_path,
        })
    return entries


CSS = """
:root {
  --bg: #f5f6f7;
  --surface: #ffffff;
  --surface-2: #fbfbfc;
  --line: #d9dde2;
  --line-soft: #eceef1;
  --ink: #14171a;
  --ink-soft: #4d545c;
  --ink-faint: #767e87;
  --accent: #2f6feb;
  --accent-soft: #e7efff;
  --ok: #1f7a45;
  --warn: #8a5a00;
  --bad: #b3261e;
  --radius: 6px;
  --radius-lg: 10px;
  --s1: 4px; --s2: 8px; --s3: 12px; --s4: 16px; --s6: 24px; --s8: 32px; --s12: 48px;
  --t-xs: 11px; --t-sm: 13px; --t-md: 15px; --t-lg: 20px; --t-xl: 28px;
  --appbar-h: 60px;
  --shell: 1360px;
  --measure: 65ch;
  --shadow: 0 1px 2px rgba(20, 23, 26, 0.06);
  --mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
  --sans: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #0f1113;
    --surface: #171a1d;
    --surface-2: #1c2024;
    --line: #2b3036;
    --line-soft: #23282d;
    --ink: #e9ebee;
    --ink-soft: #a7aeb6;
    --ink-faint: #7c848d;
    --accent: #6f9dff;
    --accent-soft: #1a2740;
    --ok: #56c58a;
    --warn: #e0ac4c;
    --bad: #ef8078;
    --shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
  }
}
:root[data-theme="dark"] {
  --bg: #0f1113;
  --surface: #171a1d;
  --surface-2: #1c2024;
  --line: #2b3036;
  --line-soft: #23282d;
  --ink: #e9ebee;
  --ink-soft: #a7aeb6;
  --ink-faint: #7c848d;
  --accent: #6f9dff;
  --accent-soft: #1a2740;
  --ok: #56c58a;
  --warn: #e0ac4c;
  --bad: #ef8078;
  --shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
}
* { box-sizing: border-box; }
[hidden] { display: none !important; }
.sr-only {
  position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0;
}
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font: var(--t-md)/1.5 var(--sans);
  -webkit-font-smoothing: antialiased;
}
button, input, select { font: inherit; color: inherit; }
a { color: var(--accent); }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

.shell {
  width: 100%; max-width: var(--shell); margin: 0 auto;
  padding-left: var(--s6); padding-right: var(--s6);
}

.appbar {
  position: sticky; top: 0; z-index: 30;
  background: var(--surface); border-bottom: 1px solid var(--line); box-shadow: var(--shadow);
}
.appbar-inner { display: flex; flex-wrap: wrap; align-items: center; gap: var(--s2) var(--s4); min-height: var(--appbar-h); }
.brand { display: flex; align-items: center; gap: var(--s3); min-width: 0; flex: 1 1 260px; }
.mark { width: 28px; height: 28px; flex: none; color: var(--accent); }
.brand-text { min-width: 0; }
.wordmark { display: block; font-size: var(--t-md); font-weight: 650; letter-spacing: -0.01em; line-height: 1.2; }
.sublabel { display: block; font-size: var(--t-xs); color: var(--ink-soft); line-height: 1.3; max-width: var(--measure); }
.appbar-actions { display: flex; flex-wrap: wrap; align-items: center; gap: var(--s2); }

.btn {
  display: inline-flex; align-items: center; gap: var(--s1);
  min-height: 28px; padding: 0 var(--s2); border: 1px solid var(--line);
  background: var(--surface); color: var(--ink); border-radius: var(--radius);
  font-size: var(--t-xs); cursor: pointer; white-space: nowrap;
}
.btn:hover { border-color: var(--ink-faint); }
.btn[aria-pressed="true"] { border-color: var(--accent); background: var(--accent-soft); color: var(--accent); }
.btn .caret-sm { font-size: 10px; color: var(--ink-faint); }

.live { display: inline-flex; align-items: center; gap: 6px; font: var(--t-xs) var(--mono); color: var(--ink-soft); }
.live-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--ok); animation: pulse 2s ease-in-out infinite; }
.live.stale .live-dot { background: var(--ink-faint); animation: none; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }

main { display: block; }

.overview { padding-top: var(--s6); padding-bottom: var(--s4); border-bottom: 1px solid var(--line); }
.headline { font-size: var(--t-xl); line-height: 1.15; margin: 0; letter-spacing: -0.02em; font-weight: 650; max-width: var(--measure); }
.headline .num { font-family: var(--mono); }
.headline .metric, .headline .sep, .headline-meta .metric, .headline-meta .sep { display: inline-block; }
.headline .sep, .headline-meta .sep { margin: 0 4px; }
.headline-meta { font-size: var(--t-sm); color: var(--ink-soft); margin: var(--s1) 0 0; max-width: var(--measure); }
.overview-sub { color: var(--ink-soft); font-size: var(--t-sm); margin: var(--s1) 0 0; max-width: var(--measure); }
.pipeline { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: var(--s2); margin-top: var(--s4); }
.pipe {
  display: flex; flex-direction: column; gap: var(--s1); text-align: left;
  padding: var(--s2) var(--s3); min-height: 60px; cursor: pointer;
  border: 1px solid var(--line); border-radius: var(--radius); background: var(--surface);
  transition: border-color 150ms ease, background 150ms ease;
}
.pipe:hover { border-color: var(--ink-faint); }
.pipe[aria-pressed="true"] { border-color: var(--accent); background: var(--accent-soft); }
.pipe-name { font-size: var(--t-xs); letter-spacing: 0.04em; text-transform: uppercase; color: var(--ink-soft); }
.pipe-count { font: 600 var(--t-lg)/1 var(--mono); }
.pipe-bar { height: 3px; border-radius: 2px; background: var(--line); overflow: hidden; }
.pipe-bar span { display: block; height: 100%; background: var(--accent); }

.toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: var(--s2); padding-top: var(--s3); padding-bottom: var(--s3); border-bottom: 1px solid var(--line); }
.search-wrap { position: relative; display: flex; align-items: center; flex: 1 1 240px; max-width: 360px; }
#search {
  width: 100%; min-height: 32px; padding: var(--s1) 56px var(--s1) var(--s2);
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius);
  font-size: var(--t-sm);
}
#search:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.kbd {
  position: absolute; right: var(--s2); font: var(--t-xs) var(--mono); color: var(--ink-faint);
  border: 1px solid var(--line); border-radius: 4px; padding: 0 6px; pointer-events: none;
}
.search-clear {
  position: absolute; right: var(--s1); width: 28px; height: 28px; display: inline-flex;
  align-items: center; justify-content: center; border: 0; background: transparent;
  color: var(--ink-soft); border-radius: var(--radius); cursor: pointer; font-size: var(--t-md);
}
.search-clear:hover { background: var(--line-soft); }
.toolbar select {
  min-height: 32px; padding: 0 var(--s2); background: var(--surface);
  border: 1px solid var(--line); border-radius: var(--radius); font-size: var(--t-sm);
}
.result-count { font: var(--t-xs) var(--mono); color: var(--ink-soft); margin-left: auto; }
.toolbar .btn { min-height: 32px; }

.banner {
  margin: var(--s4) 0 0; padding: var(--s3) var(--s4);
  border: 1px solid var(--bad); border-left-width: 3px; border-radius: var(--radius);
  color: var(--bad); background: var(--surface); font-size: var(--t-sm);
}
.panel-head {
  display: flex; flex-wrap: wrap; align-items: baseline; gap: var(--s3);
  border-bottom: 1px solid var(--line); padding-bottom: var(--s2); margin-bottom: var(--s3);
}
.panel-head > * { min-width: 0; }
.panel-head h2 { font-size: var(--t-md); margin: 0; font-weight: 600; letter-spacing: -0.01em; }
.panel-head .meta { margin-left: auto; }
.panel { margin: var(--s6) 0 0; }
details.panel > summary {
  list-style: none; cursor: pointer; min-height: 40px; align-items: center; border-radius: var(--radius);
}
details.panel > summary::-webkit-details-marker { display: none; }
details.panel > summary::marker { content: ""; }
details.panel > summary:hover { background: var(--line-soft); }
.panel-title { font-size: var(--t-md); font-weight: 600; letter-spacing: -0.01em; }

.wt-table { width: 100%; border-collapse: collapse; font-size: var(--t-sm); }
.wt-table th {
  text-align: left; font: 600 var(--t-xs) var(--mono); color: var(--ink-faint);
  text-transform: uppercase; letter-spacing: 0.04em; padding: var(--s2) var(--s3);
  border-bottom: 1px solid var(--line); background: var(--surface-2);
}
.wt-table td { padding: var(--s2) var(--s3); border-bottom: 1px solid var(--line-soft); vertical-align: top; }
.wt-table tr:last-child td { border-bottom: 0; }
.wt-table .num { font-family: var(--mono); text-align: right; width: 64px; }
.wt-table .wt-branch { font-family: var(--mono); font-weight: 600; overflow-wrap: anywhere; }
.wt-table .path { font-family: var(--mono); font-size: var(--t-xs); color: var(--ink-faint); overflow-wrap: anywhere; }
.wt-table tr.is-main td { background: var(--surface-2); }
.tag {
  display: inline-block; font-size: var(--t-xs); font-family: var(--mono);
  border: 1px solid var(--line); border-radius: 4px; padding: 0 var(--s2); color: var(--ink-soft);
}
.tag.main { border-color: var(--ink-faint); color: var(--ink); }
.tag.dirty { border-color: var(--bad); color: var(--bad); }
.tag.clean { border-color: var(--ok); color: var(--ok); }

.lane-stack { margin: var(--s6) 0 var(--s8); display: flex; flex-direction: column; gap: var(--s2); }
.lane {
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-lg);
  transition: border-color 150ms ease;
}
.lane[data-lane="Ready"] > summary { --rail: var(--ink-faint); }
.lane[data-lane="In Progress"] > summary { --rail: var(--ink); }
.lane[data-lane="In Review"] > summary { --rail: var(--ink-soft); }
.lane[data-lane="Pending Merge"] > summary { --rail: var(--warn); }
.lane[data-lane="Blocked"] > summary { --rail: var(--bad); }
.lane[data-lane="Merged"] > summary { --rail: var(--ok); }
.lane > summary {
  position: sticky; top: var(--appbar-h); z-index: 5;
  display: flex; align-items: center; gap: var(--s2);
  padding: var(--s2) var(--s4) var(--s2) var(--s3); cursor: pointer; min-height: 44px;
  list-style: none; border-radius: var(--radius-lg);
  border-left: 4px solid var(--rail, var(--line)); background: var(--surface);
}
.lane > summary::-webkit-details-marker { display: none; }
.lane > summary::marker { content: ""; }
.lane > summary:hover { background: var(--line-soft); }
.caret { color: var(--ink-faint); flex: none; font-size: var(--t-xs); transition: transform 150ms ease; }
.lane[open] > summary .caret, .wt-panel[open] > summary .caret { transform: rotate(90deg); }
.lane-name { font-size: var(--t-sm); font-weight: 650; letter-spacing: 0.02em; text-transform: uppercase; color: var(--ink); }
.count {
  font-family: var(--mono); font-size: var(--t-xs); color: var(--ink-soft);
  border: 1px solid var(--line); border-radius: 4px; padding: 0 var(--s2);
}
.lane-desc { font-size: var(--t-xs); color: var(--ink-faint); flex: 1 1 auto; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.lane-body { display: flex; flex-direction: column; gap: var(--s2); padding: 0 var(--s3) var(--s3); }
.card { border: 1px solid var(--line); border-radius: var(--radius); background: var(--surface-2); transition: border-color 150ms ease; }
.card.extra { display: none; }
.lane-body.all .card.extra { display: block; }
.lane-body.searching .card.extra { display: block; }
.card > summary {
  display: flex; flex-wrap: wrap; align-items: center; gap: var(--s2);
  padding: var(--s2) var(--s3); cursor: pointer; min-height: 36px;
  list-style: none; border-radius: var(--radius);
}
.card > summary::-webkit-details-marker { display: none; }
.card > summary::marker { content: ""; }
.card > summary:hover { background: var(--line-soft); }
.card-caret { margin-left: auto; color: var(--ink-faint); font-size: var(--t-xs); transition: transform 150ms ease; flex: none; }
.card[open] > summary .card-caret { transform: rotate(90deg); }
.card.selected { border-color: var(--accent); }
.card.selected > summary { background: var(--accent-soft); outline: 2px solid var(--accent); outline-offset: -2px; }
.card-id { font-family: var(--mono); font-size: var(--t-xs); font-weight: 700; color: var(--accent); }
.card-task { font-size: var(--t-sm); line-height: 1.35; margin: 0; font-weight: 600; flex: 1 1 240px; min-width: 0; overflow-wrap: anywhere; }
.chip {
  font-size: var(--t-xs); font-family: var(--mono); border-radius: 4px;
  padding: 1px var(--s2); border: 1px solid var(--line); color: var(--ink-soft); white-space: nowrap;
}
.chip.prio { border-color: var(--ink-faint); color: var(--ink); }
.chip.risk { display: inline-flex; align-items: center; gap: 6px; }
.chip.risk.low { border-color: var(--ok); }
.chip.risk.medium { border-color: var(--warn); }
.chip.risk.high { border-color: var(--bad); }
.risk-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--ink-faint); flex: none; }
.chip.risk.low .risk-dot { background: var(--ok); }
.chip.risk.medium .risk-dot { background: var(--warn); }
.chip.risk.high .risk-dot { background: var(--bad); }
.card-detail { padding: 0 var(--s3) var(--s3); }
.card-kv { display: grid; grid-template-columns: auto 1fr; gap: var(--s1) var(--s3); font-size: var(--t-xs); margin: var(--s2) 0 0; }
.card-kv dt { color: var(--ink-faint); font-family: var(--mono); }
.card-kv dd { margin: 0; color: var(--ink-soft); font-family: var(--mono); overflow-wrap: anywhere; word-break: break-word; min-width: 0; }
.kv-line { display: flex; flex-wrap: wrap; align-items: center; gap: var(--s2); }
.copy {
  font: var(--t-xs) var(--mono); min-height: 24px; padding: 0 var(--s2); cursor: pointer;
  border: 1px solid var(--line); background: var(--surface); color: var(--ink-soft); border-radius: 4px;
}
.copy:hover { border-color: var(--accent); color: var(--accent); }
.notes { list-style: none; margin: var(--s2) 0 0; padding: 0; display: flex; flex-direction: column; gap: var(--s1); }
.note { display: flex; align-items: flex-start; gap: var(--s2); font-size: var(--t-xs); color: var(--ink-soft); line-height: 1.45; }
.note-box {
  flex: none; width: 14px; height: 14px; margin-top: 1px; border: 1px solid var(--ink-faint);
  border-radius: 3px; display: inline-flex; align-items: center; justify-content: center;
  font-size: 10px; color: var(--ok);
}
.note-check.done .note-box { border-color: var(--ok); }
.note-text { min-width: 0; overflow-wrap: anywhere; }
.note-proof-text { display: block; margin-top: 1px; font: var(--t-xs) var(--mono); color: var(--ink-faint); }
.note-proof { font-family: var(--mono); color: var(--ink-faint); }
.note-free { color: var(--ink-soft); }
.more {
  align-self: flex-start; font: var(--t-xs)/1.4 var(--mono); color: var(--accent);
  background: transparent; border: 1px solid var(--line); border-radius: var(--radius);
  padding: var(--s1) var(--s3); min-height: 28px; cursor: pointer;
}
.more:hover { border-color: var(--accent); }
.empty { font-size: var(--t-xs); color: var(--ink-faint); padding: var(--s2) var(--s1); }
footer { padding-top: var(--s6); padding-bottom: var(--s8); color: var(--ink-faint); font-size: var(--t-xs); font-family: var(--mono); }
.hidden { display: none !important; }
.filtered { display: none !important; }
.lane-filtered { display: none !important; }

body.compact .lane-body { gap: var(--s1); padding-bottom: var(--s2); }
body.compact .card > summary { min-height: 28px; padding: 2px var(--s2); }
body.compact .lane > summary { min-height: 36px; padding-top: var(--s1); padding-bottom: var(--s1); }
body.compact .card-task { font-size: var(--t-xs); }
body.compact .note { line-height: 1.35; }

@media (max-width: 760px) {
  .pipeline { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .lane-desc { display: none; }
}
@media (max-width: 640px) {
  .wt-table thead { display: none; }
  .wt-table, .wt-table tbody, .wt-table tr, .wt-table td { display: block; width: 100%; }
  .wt-table tr { border: 1px solid var(--line); border-radius: var(--radius); margin-bottom: var(--s2); background: var(--surface); }
  .wt-table td { border: 0; padding: var(--s1) var(--s3); display: flex; gap: var(--s2); }
  .wt-table td::before { content: attr(data-label); font: var(--t-xs) var(--mono); color: var(--ink-faint); flex: 0 0 72px; }
  .wt-table .num { text-align: left; width: auto; }
}
@media (max-width: 480px) {
  :root { --appbar-h: 56px; }
  .shell { padding-left: var(--s3); padding-right: var(--s3); }
  .overview { padding-top: var(--s4); padding-bottom: var(--s3); }
  .headline { font-size: var(--t-lg); }
  .toolbar { padding-top: var(--s2); padding-bottom: var(--s2); }
  .banner { margin: var(--s3) 0 0; }
  .panel { margin: var(--s4) 0 0; }
  .lane-stack { margin: var(--s4) 0 var(--s6); }
  footer { padding-top: var(--s6); padding-bottom: var(--s6); }
  .result-count { margin-left: 0; }
}
@media (prefers-reduced-motion: reduce) {
  * { transition: none !important; animation: none !important; }
}
"""

JS = """
(function () {
  var KEY = "board-dashboard-state";
  var state = {lanes: {}, cards: {}, more: {}, theme: "system", density: "comfortable"};
  try {
    var saved = JSON.parse(window.localStorage.getItem(KEY) || "{}");
    if (saved && typeof saved === "object") {
      state.lanes = saved.lanes || {};
      state.cards = saved.cards || {};
      state.more = saved.more || {};
      if (saved.theme) { state.theme = saved.theme; }
      if (saved.density) { state.density = saved.density; }
    }
  } catch (e) { /* storage is unavailable; the server defaults are used */ }

  function save() {
    try { window.localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* ignore */ }
  }

  function laneKey(el) { return el.getAttribute("data-board") + "::" + el.getAttribute("data-lane"); }
  function cardKey(el) { return laneKey(el) + "::" + el.getAttribute("data-card"); }
  function has(obj, key) { return Object.prototype.hasOwnProperty.call(obj, key); }
  function all(selector, root) { return Array.prototype.slice.call((root || document).querySelectorAll(selector)); }

  var lanes = all(".lane");
  var cards = all(".card");
  var boards = all("section.board");

  lanes.forEach(function (lane) {
    var key = laneKey(lane);
    if (has(state.lanes, key)) { lane.open = !!state.lanes[key]; }
    var body = lane.querySelector(".lane-body");
    var button = lane.querySelector(".more");
    if (button && body) {
      if (state.more[key]) { body.classList.add("all"); }
      var expanded = body.classList.contains("all");
      button.setAttribute("aria-expanded", expanded ? "true" : "false");
      button.textContent = expanded
        ? button.getAttribute("data-label-collapse")
        : button.getAttribute("data-label-expand");
    }
  });

  cards.forEach(function (card) {
    var key = cardKey(card);
    if (has(state.cards, key)) { card.open = !!state.cards[key]; }
  });

  lanes.forEach(function (lane) {
    lane.addEventListener("toggle", function () {
      state.lanes[laneKey(lane)] = lane.open;
      save();
    });
  });
  cards.forEach(function (card) {
    card.addEventListener("toggle", function () {
      state.cards[cardKey(card)] = card.open;
      save();
    });
  });

  all(".lane .more").forEach(function (button) {
    button.addEventListener("click", function () {
      var lane = button.closest(".lane");
      var body = lane ? lane.querySelector(".lane-body") : null;
      if (!body) { return; }
      var expanded = body.classList.toggle("all");
      state.more[laneKey(lane)] = expanded;
      save();
      button.setAttribute("aria-expanded", expanded ? "true" : "false");
      button.textContent = expanded
        ? button.getAttribute("data-label-collapse")
        : button.getAttribute("data-label-expand");
    });
  });

  var search = document.getElementById("search");
  var typeSel = document.getElementById("type-filter");
  var prioSel = document.getElementById("priority-filter");
  var resultCount = document.getElementById("result-count");
  var resetBtn = document.getElementById("reset");
  var searchClear = document.getElementById("search-clear");
  var kbd = document.querySelector(".kbd");
  var pipes = all(".pipe");
  var themeBtn = document.getElementById("theme-toggle");
  var densityBtn = document.getElementById("density-toggle");
  var pauseBtn = document.getElementById("pause");
  var refreshBtn = document.getElementById("refresh-now");
  var live = document.querySelector(".live");
  var liveText = document.querySelector(".live-text");
  var statusFilter = "";
  var selected = null;

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    if (themeBtn) {
      var label = theme === "system" ? "System" : (theme === "dark" ? "Dark" : "Light");
      themeBtn.textContent = label;
      themeBtn.setAttribute("aria-label", "Colour theme: " + label + " (click to change)");
    }
    state.theme = theme;
  }

  function applyDensity(density) {
    var compact = density === "compact";
    document.body.classList.toggle("compact", compact);
    if (densityBtn) {
      densityBtn.textContent = compact ? "Compact" : "Comfortable";
      densityBtn.setAttribute("aria-pressed", compact ? "true" : "false");
      densityBtn.setAttribute("aria-label", "Density: " + (compact ? "compact" : "comfortable") + " (click to change)");
    }
    state.density = compact ? "compact" : "comfortable";
  }

  function filters() {
    return {
      q: search ? search.value.trim().toLowerCase() : "",
      type: typeSel ? typeSel.value : "",
      priority: prioSel ? prioSel.value : "",
      status: statusFilter
    };
  }

  function setParam(params, name, value) {
    if (value) { params.set(name, value); } else { params.delete(name); }
  }

  function updateUrl(f) {
    try {
      var params = new URLSearchParams(window.location.search);
      setParam(params, "q", search ? search.value.trim() : "");
      setParam(params, "type", f.type);
      setParam(params, "priority", f.priority);
      setParam(params, "status", f.status);
      setParam(params, "density", state.density === "compact" ? "compact" : "");
      var qs = params.toString();
      history.replaceState(null, "", qs ? "?" + qs : window.location.pathname);
    } catch (e) { /* replaceState can fail on file://; the filters still work */ }
  }

  function apply() {
    var f = filters();
    var anyActive = !!(f.q || f.type || f.priority || f.status);
    var matched = 0;

    lanes.forEach(function (lane) {
      var status = lane.getAttribute("data-lane");
      var laneHidden = !!(f.status && status !== f.status);
      lane.classList.toggle("lane-filtered", laneHidden);
      var body = lane.querySelector(".lane-body");
      if (body) { body.classList.toggle("searching", anyActive); }
      var expanded = body ? body.classList.contains("all") : true;
      var laneShown = 0;
      var laneMatches = 0;
      var laneCards = all(".card", lane);
      laneCards.forEach(function (card) {
        var hit = !laneHidden &&
          (!f.q || card.textContent.toLowerCase().indexOf(f.q) !== -1) &&
          (!f.type || card.getAttribute("data-type") === f.type) &&
          (!f.priority || card.getAttribute("data-priority") === f.priority);
        card.classList.toggle("filtered", !hit);
        if (hit) {
          matched += 1;
          laneMatches += 1;
          if (expanded || !card.classList.contains("extra")) { laneShown += 1; }
        }
      });

      var empty = lane.querySelector(".empty");
      if (empty) {
        if (laneHidden) {
          empty.classList.add("hidden");
        } else if (laneShown === 0) {
          empty.classList.remove("hidden");
          empty.textContent = (anyActive && laneMatches === 0 && laneCards.length > 0)
            ? "No cards in this lane match the filters."
            : empty.getAttribute("data-empty-default");
        } else {
          empty.classList.add("hidden");
        }
      }

      var count = lane.querySelector(".count");
      if (count) {
        count.textContent = anyActive
          ? laneShown + "/" + laneCards.length
          : String(laneCards.length);
      }
    });

    boards.forEach(function (board) {
      var visible = true;
      if (f.status) {
        visible = all(".lane", board).some(function (lane) {
          return lane.getAttribute("data-lane") === f.status;
        });
      }
      board.classList.toggle("hidden", !visible);
    });

    if (selected && selected.classList.contains("filtered")) { deselect(); }

    if (resultCount) { resultCount.textContent = "showing " + matched + " of " + cards.length; }
    if (resetBtn) { resetBtn.hidden = !anyActive; }
    if (searchClear) { searchClear.hidden = !(search && search.value); }
    if (kbd) { kbd.hidden = !!(search && search.value); }
    pipes.forEach(function (pipe) {
      pipe.setAttribute("aria-pressed",
        pipe.getAttribute("data-status-filter") === f.status ? "true" : "false");
    });
    updateUrl(f);
  }

  function deselect() {
    if (selected) { selected.classList.remove("selected"); }
    selected = null;
  }

  function setSelected(card) {
    if (selected) { selected.classList.remove("selected"); }
    selected = card;
    card.classList.add("selected");
    var lane = card.closest(".lane");
    if (lane && !lane.open) {
      lane.open = true;
      state.lanes[laneKey(lane)] = true;
      save();
    }
    var summary = card.querySelector("summary");
    if (summary) {
      try { summary.focus({preventScroll: true}); } catch (e) { summary.focus(); }
    }
    card.scrollIntoView({block: "nearest"});
  }

  function visibleCards() {
    return cards.filter(function (card) {
      return !card.classList.contains("filtered") && card.offsetParent !== null;
    });
  }

  function move(direction) {
    var list = visibleCards();
    if (!list.length) { return; }
    var index = selected ? list.indexOf(selected) : -1;
    index = index + direction;
    if (index < 0) { index = 0; }
    if (index >= list.length) { index = list.length - 1; }
    setSelected(list[index]);
  }

  function clearFilters() {
    if (search) { search.value = ""; }
    if (typeSel) { typeSel.value = ""; }
    if (prioSel) { prioSel.value = ""; }
    statusFilter = "";
    deselect();
    apply();
  }

  if (search) {
    search.addEventListener("input", apply);
  }
  if (searchClear) {
    searchClear.addEventListener("click", function () {
      if (search) { search.value = ""; search.focus(); }
      apply();
    });
  }
  if (typeSel) { typeSel.addEventListener("change", apply); }
  if (prioSel) { prioSel.addEventListener("change", apply); }
  if (resetBtn) { resetBtn.addEventListener("click", clearFilters); }

  pipes.forEach(function (pipe) {
    pipe.addEventListener("click", function () {
      var value = pipe.getAttribute("data-status-filter");
      statusFilter = statusFilter === value ? "" : value;
      apply();
    });
  });

  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      var next = state.theme === "system" ? "light" : (state.theme === "light" ? "dark" : "system");
      applyTheme(next);
      save();
    });
  }
  if (densityBtn) {
    densityBtn.addEventListener("click", function () {
      applyDensity(state.density === "compact" ? "comfortable" : "compact");
      save();
      apply();
    });
  }

  all("[data-copy]").forEach(function (button) {
    button.addEventListener("click", function () {
      var value = button.getAttribute("data-copy");
      var done = function () {
        button.textContent = "copied";
        window.setTimeout(function () { button.textContent = "copy"; }, 1200);
      };
      var fallback = function () {
        var area = document.createElement("textarea");
        area.value = value;
        area.setAttribute("readonly", "");
        area.style.position = "fixed";
        area.style.opacity = "0";
        document.body.appendChild(area);
        area.select();
        try { document.execCommand("copy"); done(); } catch (e) { /* copy unavailable */ }
        document.body.removeChild(area);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(value).then(done, fallback);
      } else {
        fallback();
      }
    });
  });

  var refreshSeconds = parseInt(document.body.getAttribute("data-refresh"), 10) || 10;
  var paused = false;
  var generatedMs = live ? parseInt(live.getAttribute("data-ms"), 10) : 0;

  function tick() {
    if (!live) { return; }
    var age = generatedMs ? (Date.now() - generatedMs) : 0;
    var stale = paused || age > refreshSeconds * 1500;
    live.classList.toggle("stale", stale);
    if (liveText) {
      var time = generatedMs ? new Date(generatedMs).toLocaleTimeString() : "";
      liveText.textContent = "updated " + time + (paused ? " · paused" : (stale ? " · stale" : " · live"));
    }
  }
  if (live) {
    tick();
    window.setInterval(tick, 1000);
  }

  if (pauseBtn) {
    pauseBtn.setAttribute("aria-pressed", "false");
    pauseBtn.addEventListener("click", function () {
      paused = !paused;
      pauseBtn.textContent = paused ? "Resume" : "Pause";
      pauseBtn.setAttribute("aria-pressed", paused ? "true" : "false");
      tick();
    });
  }
  if (refreshBtn) {
    refreshBtn.addEventListener("click", function () { window.location.reload(); });
  }
  window.setInterval(function () {
    if (!paused) { window.location.reload(); }
  }, refreshSeconds * 1000);

  document.addEventListener("keydown", function (event) {
    var target = event.target;
    var typing = target && (target.tagName === "INPUT" || target.tagName === "SELECT" ||
      target.tagName === "TEXTAREA" || target.tagName === "BUTTON" ||
      target.tagName === "A" || target.isContentEditable);
    if (event.key === "/" && !typing) {
      event.preventDefault();
      if (search) { search.focus(); search.select(); }
      return;
    }
    if (event.key === "Escape") {
      clearFilters();
      if (search) { search.focus(); }
      return;
    }
    if (typing) { return; }
    if (event.key === "j" || event.key === "k") {
      event.preventDefault();
      move(event.key === "j" ? 1 : -1);
    } else if (event.key === "Enter" && selected) {
      event.preventDefault();
      selected.open = !selected.open;
      state.cards[cardKey(selected)] = selected.open;
      save();
    }
  });

  try {
    var params = new URLSearchParams(window.location.search);
    if (search && params.get("q")) { search.value = params.get("q"); }
    if (typeSel && params.get("type")) { typeSel.value = params.get("type"); }
    if (prioSel && params.get("priority")) { prioSel.value = params.get("priority"); }
    if (params.get("status")) { statusFilter = params.get("status"); }
    applyTheme(state.theme);
    applyDensity(params.get("density") === "compact" ? "compact" : state.density);
  } catch (e) {
    applyTheme(state.theme);
    applyDensity(state.density);
  }

  apply();
})();
"""


def esc(value):
    return html.escape("" if value is None else str(value), quote=True)


RISK_EMOJI = re.compile("[\U0001F7E2\U0001F7E1\U0001F534]")


def clean_text(value):
    text = "" if value is None else str(value)
    text = text.replace("`", "")
    text = re.sub(r"\*+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def esc_path(value):
    text = esc(value)
    for sep in ("/", "_"):
        text = text.replace(sep, sep + "<wbr>")
    return text


CHECK_MARK = re.compile(r"^- \[(x|X| )\]\s*(.*)$")
PROOF_MARK = re.compile(r"proof\s*:", re.IGNORECASE)


def split_proof(body):
    """Split an item on its first ``proof:`` marker into (claim, proof)."""
    match = PROOF_MARK.search(body)
    if not match:
        return body, ""
    return body[:match.start()], body[match.end():]


def parse_notes(raw):
    """Turn a raw Notes cell into render items.

    Returns a list of {kind, text, checked, proof}. Notebook cells separate items
    with ``·``; a cell without that separator falls back to one free-text item.
    """
    text = "" if raw is None else str(raw).strip()
    if not text:
        return []
    parts = [part.strip() for part in text.split("·") if part.strip()]
    if not parts:
        return []
    items = []
    for part in parts:
        check = CHECK_MARK.match(part)
        if check:
            claim, proof = split_proof(check.group(2).strip())
            items.append({
                "kind": "check",
                "checked": check.group(1).lower() == "x",
                "text": clean_text(claim),
                "proof": clean_text(proof),
            })
        elif PROOF_MARK.match(part):
            items.append({"kind": "proof", "text": clean_text(part)})
        else:
            items.append({"kind": "text", "text": clean_text(part)})
    return items


def render_notes(raw):
    items = parse_notes(raw)
    if not items:
        return ""
    rendered = []
    for item in items:
        if item["kind"] == "check":
            state_word = "Done" if item["checked"] else "Open"
            proof = ""
            if item["proof"]:
                proof = '<span class="note-proof-text">proof: %s</span>' % esc(item["proof"])
            check_html = (
                '<li class="note note-check%s">'
                '<span class="note-box" aria-hidden="true">%s</span>'
                '<span class="sr-only">%s: </span>'
                '<span class="note-text">%s</span>%s</li>'
            ) % (
                " done" if item["checked"] else "",
                "&#10003;" if item["checked"] else "",
                esc(state_word),
                esc(item["text"]),
                proof,
            )
            rendered.append(check_html)
        elif item["kind"] == "proof":
            rendered.append(
                '<li class="note note-proof"><span class="note-text">%s</span></li>'
                % esc(item["text"])
            )
        else:
            rendered.append(
                '<li class="note note-free"><span class="note-text">%s</span></li>'
                % esc(item["text"])
            )
    return '<ul class="notes">%s</ul>' % "".join(rendered)


def branch_name(value):
    """The branch token inside a Branch/Worktree part, or an empty string."""
    match = re.search(r"\bbranch\s+(\S+)", value, re.IGNORECASE)
    return match.group(1) if match else ""


def risk_class(risk):
    """The risk level from the risk text, or an empty string when unknown."""
    text = RISK_EMOJI.sub("", clean_text(risk)).strip()
    match = re.match(r"^(low|medium|high)\b", text, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    match = re.search(r"\b(low|medium|high)\b", text, re.IGNORECASE)
    return match.group(1).lower() if match else ""


def render_risk(risk):
    """A CSS-coloured dot, the plain level word, and the risk text in the title."""
    text = clean_text(risk)
    title = RISK_EMOJI.sub("", text).strip()
    level = risk_class(text)
    word = level if level else title
    return (
        '<span class="chip risk %s" title="%s">'
        '<span class="risk-dot" aria-hidden="true"></span>%s</span>'
    ) % (level, esc(title), esc(word))


def render_worktree(wt):
    """One worktree row for the worktrees table."""
    tags = []
    if wt["main"]:
        tags.append('<span class="tag main">main</span>')
    tags.append(
        '<span class="tag dirty">dirty</span>' if wt["dirty"]
        else '<span class="tag clean">clean</span>')
    ahead = wt["ahead"] if wt["ahead"] is not None else "?"
    behind = wt["behind"] if wt["behind"] is not None else "?"
    return (
        '<tr class="wt-row%s">'
        '<td data-label="Branch"><span class="wt-branch">%s</span></td>'
        '<td data-label="State">%s</td>'
        '<td data-label="Ahead" class="num">%s</td>'
        '<td data-label="Behind" class="num">%s</td>'
        '<td data-label="Path" class="path">%s</td>'
        '</tr>'
    ) % (
        " is-main" if wt["main"] else "",
        esc_path(wt["branch"]),
        " ".join(tags),
        esc(ahead),
        esc(behind),
        esc_path(wt["path"]),
    )


def render_worktrees(worktrees):
    ordered = sorted(worktrees, key=lambda wt: 1 if wt["main"] else 0)
    rows = "".join(render_worktree(wt) for wt in ordered)
    if not rows:
        rows = ('<tr><td colspan="5" class="empty">'
                'No git worktrees found. Start one with worktree.py create.</td></tr>')
    return (
        '<table class="wt-table">'
        '<thead><tr><th scope="col">Branch</th><th scope="col">State</th>'
        '<th scope="col" class="num">Ahead</th><th scope="col" class="num">Behind</th>'
        '<th scope="col">Path</th></tr></thead>'
        '<tbody>%s</tbody></table>'
    ) % rows


def row_fingerprint(notes):
    """The fingerprint carried in a row's Notes cell, or an empty string."""
    match = re.search(r"\bfp=([^\s|·]+\|[^\s|·]+\|[^\s|·]+\|[^\s|·]+)", clean_text(notes))
    return match.group(1) if match else ""


def render_card(row, board_label, lane, extra=False):
    blocked = clean_text(row["Blocked by"])
    if blocked in ("-", "- None.", "", "None."):
        blocked = "none"
    branch = clean_text(row["Branch/Worktree"])
    if branch.strip() in ("-", ""):
        branch = ""
    branch_parts = [clean_text(part) for part in branch.split("·") if clean_text(part)]
    kv = ""
    if blocked:
        kv += "<dt>blocked</dt><dd>%s</dd>" % esc(blocked)
    if branch_parts:
        lines = []
        for part in branch_parts:
            name = branch_name(part)
            copy = ""
            if name:
                copy = (
                    '<button type="button" class="copy" data-copy="%s"'
                    ' aria-label="Copy branch %s">copy</button>'
                ) % (esc(name), esc(name))
            lines.append(
                '<span class="kv-line">%s%s</span>' % (esc_path(part), copy))
        kv += "<dt>worktree</dt><dd>%s</dd>" % "".join(lines)
    fingerprint = row_fingerprint(row["Notes"])
    if fingerprint:
        kv += "<dt>fingerprint</dt><dd>%s</dd>" % esc(fingerprint)
    notes = str(row.get("Notes raw", "")).strip()
    detail = ""
    if kv:
        detail += '<dl class="card-kv">%s</dl>' % kv
    notes_html = render_notes(notes)
    if notes_html:
        detail += notes_html
    return (
        '<details class="card%s" data-board="%s" data-lane="%s" data-card="%s"'
        ' data-type="%s" data-priority="%s">'
        '<summary>'
        '<span class="card-id">%s</span>'
        '<span class="card-task">%s</span>'
        '<span class="chip type">%s</span>'
        '<span class="chip prio">%s</span>'
        '%s'
        '<span class="card-caret" aria-hidden="true">&#9656;</span>'
        '</summary>'
        '<div class="card-detail">%s</div>'
        '</details>'
    ) % (
        " extra" if extra else "",
        esc(board_label),
        esc(lane),
        esc(row["ID"]),
        esc(clean_text(row["Type"])),
        esc(clean_text(row["Priority"])),
        esc(row["ID"]),
        esc(clean_text(row["Task"])),
        esc(clean_text(row["Type"])),
        esc(clean_text(row["Priority"])),
        render_risk(row["Risk"]),
        detail,
    )


def lane_open_by_default(lane, card_count):
    """A lane with no cards stays collapsed; the server knows the card count."""
    if card_count == 0:
        return False
    return lane not in COLLAPSED_BY_DEFAULT


def render_lane(lane, rows, board_label):
    lane_rows = [row for row in rows if row["Status"] == lane]
    preview = lane_rows
    extra = []
    if lane == "Merged" and len(lane_rows) > MERGED_PREVIEW:
        preview = lane_rows[-MERGED_PREVIEW:]
        extra = lane_rows[:-MERGED_PREVIEW]
    cards = [render_card(row, board_label, lane, extra=True) for row in extra]
    cards += [render_card(row, board_label, lane) for row in preview]
    more = ""
    if extra:
        more = (
            '<button type="button" class="more" aria-expanded="false"'
            ' data-label-expand="Show all %d" data-label-collapse="Show only the last %d">'
            'Show all %d</button>'
        ) % (len(lane_rows), MERGED_PREVIEW, len(lane_rows))
    body = "".join(cards)
    empty_text = EMPTY_TEXT.get(lane, "Nothing in this lane.")
    body += (
        '<p class="empty%s" data-empty-default="%s">%s</p>'
    ) % (" hidden" if cards else "", esc(empty_text), esc(empty_text))
    open_attr = " open" if lane_open_by_default(lane, len(lane_rows)) else ""
    return (
        '<details class="lane" data-board="%s" data-lane="%s"%s>'
        '<summary>'
        '<span class="caret" aria-hidden="true">&#9656;</span>'
        '<span class="lane-name">%s</span>'
        '<span class="count">%d</span>'
        '<span class="lane-desc">%s</span>'
        '</summary>'
        '<div class="lane-body">%s%s</div>'
        '</details>'
    ) % (
        esc(board_label),
        esc(lane),
        open_attr,
        esc(lane),
        len(lane_rows),
        esc(LANE_DESCRIPTION.get(lane, "")),
        body,
        more,
    )


def render_board(entry):
    """One board: its heading and every lane."""
    rows = entry["rows"]
    counts = entry["counts"]
    banner = ""
    if entry.get("error"):
        banner = '<p class="banner">%s</p>' % esc(entry["error"])
    lanes_html = "\n".join(render_lane(lane, rows, entry["label"]) for lane in LANE_ORDER)
    return (
        '<section class="board shell" data-board="%s">'
        '<div class="panel-head"><h2>%s board</h2>'
        '<span class="meta">%d card(s) &middot; %s</span></div>'
        '<p class="meta board-path" title="%s">%s</p>%s'
        '<div class="lane-stack">%s</div>'
        '</section>'
    ) % (
        esc(entry["label"]),
        esc(entry["label"]),
        len(rows),
        esc(", ".join("%s %d" % (lane, counts.get(lane, 0)) for lane in LANE_ORDER)),
        esc(entry["path"]),
        esc_path(entry["path"]),
        banner,
        lanes_html,
    )


def active_counts(boards):
    """Aggregate the five active lanes across every visible board."""
    return {
        lane: sum(entry["counts"].get(lane, 0) for entry in boards)
        for lane in ACTIVE_LANES
    }


def last_merged_id(boards):
    last = ""
    for entry in boards:
        for row in entry["rows"]:
            if row["Status"] == "Merged":
                last = row["ID"]
    return last


def render_pipeline(counts):
    peak = max(counts.values()) or 1
    parts = []
    for lane in ACTIVE_LANES:
        count = counts.get(lane, 0)
        width = int(round(count * 100 / peak)) if count else 0
        button = (
            '<button type="button" class="pipe" data-status-filter="%s" aria-pressed="false">'
            '<span class="pipe-name">%s</span>'
            '<span class="pipe-count">%d</span>'
            '<span class="pipe-bar" aria-hidden="true">'
            '<span style="width: %d%%"></span></span>'
            '</button>'
        ) % (esc(lane), esc(lane), count, width)
        parts.append(button)
    return '<div class="pipeline">%s</div>' % "".join(parts)


def render_toolbar(total_cards):
    types = ("Feature", "Fix", "Chore", "Docs", "Research")
    priorities = ("P1", "P2", "P3", "P4")
    type_options = '<option value="">All types</option>' + "".join(
        '<option value="%s">%s</option>' % (esc(t), esc(t)) for t in types)
    prio_options = '<option value="">All priorities</option>' + "".join(
        '<option value="%s">%s</option>' % (esc(p), esc(p)) for p in priorities)
    return (
        '<div class="toolbar shell" role="search">'
        '<div class="search-wrap">'
        '<label class="sr-only" for="search">Search cards</label>'
        '<input id="search" type="search" placeholder="Search id, task, branch"'
        ' autocomplete="off" spellcheck="false">'
        '<kbd class="kbd" aria-hidden="true">/</kbd>'
        '<button type="button" id="search-clear" class="search-clear"'
        ' aria-label="Clear search" hidden>&times;</button>'
        '</div>'
        '<label class="sr-only" for="type-filter">Filter by type</label>'
        '<select id="type-filter">%s</select>'
        '<label class="sr-only" for="priority-filter">Filter by priority</label>'
        '<select id="priority-filter">%s</select>'
        '<span id="result-count" class="result-count" aria-live="polite">'
        'showing %d of %d</span>'
        '<button type="button" id="reset" class="btn" hidden>Reset</button>'
        '</div>'
    ) % (type_options, prio_options, total_cards, total_cards)


def build_html(boards, worktrees, generated_at, error, refresh):
    total = sum(len(entry["rows"]) for entry in boards)
    boards_html = "\n".join(render_board(entry) for entry in boards)
    if not boards_html:
        boards_html = '<p class="empty">No board file found. Point the server at one with --file.</p>'
    counts = active_counts(boards)
    active_total = sum(counts.values())
    sep = '<span class="sep" aria-hidden="true">&middot;</span>'
    banner = ""
    if error:
        banner = '<div class="shell"><p class="banner">%s</p></div>' % esc(error)
    if active_total == 0:
        meta = []
        merged = last_merged_id(boards)
        if merged:
            meta.append("last merged %s" % merged)
        meta.append("as of %s" % generated_at.split("T")[0])
        meta_html = sep.join('<span class="metric">%s</span>' % esc(m) for m in meta)
        headline = (
            '<h1 class="headline">All clear &mdash; nothing in flight</h1>'
            '<p class="headline-meta">%s</p>'
        ) % meta_html
    else:
        headline = (
            '<h1 class="headline">'
            '<span class="metric"><span class="num">%d</span> active</span>%s'
            '<span class="metric"><span class="num">%d</span> pending merge</span>%s'
            '<span class="metric"><span class="num">%d</span> blocked</span></h1>'
            '<p class="overview-sub">Filter a lane below, or press <kbd>/</kbd> to search. '
            'The board is read fresh on every request.</p>'
        ) % (active_total, sep, counts.get("Pending Merge", 0), sep, counts.get("Blocked", 0))

    active = sum(1 for wt in worktrees if not wt["main"])
    wt_meta = "%d worktree(s) &middot; %d non-main" % (len(worktrees), active)
    try:
        epoch_ms = int(datetime.datetime.fromisoformat(generated_at).timestamp() * 1000)
    except (TypeError, ValueError):
        epoch_ms = 0
    mark = (
        '<svg class="mark" viewBox="0 0 24 24" aria-hidden="true" fill="none" '
        'stroke="currentColor" stroke-width="1.8" stroke-linejoin="round">'
        '<path d="M3 20V9l6 3V9l6 3V4h6v16z"/>'
        '<path d="M6 16h3M12 16h3"/></svg>'
    )
    html_parts = [
        "<!doctype html>\n",
        '<html lang="en" data-theme="', esc("system"), '"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="color-scheme" content="light dark">',
        '<link rel="icon" href="', FAVICON, '">',
        "<title>Factory Board</title><style>", CSS, "</style></head><body",
        ' data-refresh="', str(refresh), '">\n',
        '<header class="appbar">',
        '<div class="shell appbar-inner">',
        '<div class="brand">', mark,
        '<div class="brand-text">',
        '<span class="wordmark">Factory Board</span>',
        '<span class="sublabel">Lanes, cards and live worktrees — what is in flight right now</span>',
        '</div></div>',
        '<div class="appbar-actions">',
        '<span class="live" data-ms="', str(epoch_ms), '">',
        '<span class="live-dot" aria-hidden="true"></span>',
        '<span class="live-text">updated ', esc(generated_at[11:19]), '</span></span>',
        '<button type="button" class="btn" id="pause" aria-pressed="false">Pause</button>',
        '<button type="button" class="btn" id="refresh-now">Refresh now</button>',
        '<button type="button" class="btn" id="theme-toggle" aria-label="Colour theme">System</button>',
        '<button type="button" class="btn" id="density-toggle" aria-pressed="false">Comfortable</button>',
        '</div></div></header>\n',
        '<main>',
        '<section class="overview shell">', headline, render_pipeline(counts), '</section>',
        render_toolbar(total),
        banner,
        boards_html,
        '<details class="panel wt-panel shell">',
        '<summary class="panel-head">',
        '<span class="caret" aria-hidden="true">&#9656;</span>',
        '<span class="panel-title">Worktrees</span>',
        '<span class="meta">', wt_meta, '</span></summary>',
        render_worktrees(worktrees),
        '</details>',
        '</main>',
        '<footer class="shell">', str(total), ' card(s) across ', str(len(boards)), ' board(s)',
        ' &middot; refresh every ', str(refresh), 's, pausable</footer>\n',
        "<script>", JS, "</script>\n",
        "</body></html>",
    ]
    return "".join(html_parts)


class Handler(BaseHTTPRequestHandler):
    server_version = "board-serve/1.0"
    state = {}

    def log_message(self, fmt, *args):
        print("%s %s" % (self.address_string(), fmt % args), flush=True)

    def send_bytes(self, code, body, content_type):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def send_json(self, code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_bytes(code, body, "application/json; charset=utf-8")

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path == "/health":
            self.send_json(200, {"ok": True})
            return
        if path == "/api/board":
            self.send_json(200, self.state["board_payload"]())
            return
        if path == "/api/worktrees":
            self.send_json(200, self.state["worktree_payload"]())
            return
        if path == "/":
            html_body = self.state["html"]()
            self.send_bytes(200, html_body.encode("utf-8"), "text/html; charset=utf-8")
            return
        self.send_bytes(404, b"not found\n", "text/plain; charset=utf-8")


def board_states(board, paths):
    states = []
    for label, path in paths:
        rows, error = read_rows(board, path)
        lanes = lane_map(rows)
        states.append({
            "label": label,
            "path": path,
            "rows": rows,
            "lanes": lanes,
            "counts": {lane: len(lanes.get(lane, [])) for lane in LANES},
            "error": error,
        })
    return states


def build_payloads(board, worktree, paths, root):
    def board_payload():
        return {
            "boards": board_states(board, paths),
            "generated_at": now(),
        }

    def worktree_payload():
        try:
            return worktree_state(worktree, root)
        except Exception:
            return []

    def html_page():
        try:
            states = board_states(board, paths)
            state = worktree_state(worktree, root)
            error = None
        except Exception as exc:
            states, state = [], []
            error = "could not read the board: %s" % exc
        return build_html(states, state, now(), error, Handler.state["refresh"])

    return board_payload, worktree_payload, html_page


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def main(argv):
    parser = argparse.ArgumentParser(
        prog="board_serve.py",
        description="Serve a read-only HTML dashboard of the board and the live worktrees.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help="port to listen on (default: %d)" % DEFAULT_PORT)
    parser.add_argument("--host", default=DEFAULT_HOST,
                        help="address to bind (default: %s)" % DEFAULT_HOST)
    parser.add_argument("--open", action="store_true",
                        help="open the dashboard in the default browser")
    parser.add_argument("--file", help="board file (default: docs/BOARD.md in the repo root)")
    parser.add_argument("--refresh", type=int, default=DEFAULT_REFRESH,
                        help="auto-refresh interval in seconds (default: %d)" % DEFAULT_REFRESH)
    args = parser.parse_args(argv)

    board, worktree = load_helpers()
    cwd = os.getcwd()
    root = repo_root(worktree, cwd)
    if args.file:
        paths = [("board", board_file(args.file, root))]
    else:
        paths = discover_boards(root)
        if not paths:
            paths = [("board", board_file(None, root))]

    board_payload, worktree_payload, html_page = build_payloads(board, worktree, paths, root)
    Handler.state = {
        "board_payload": board_payload,
        "worktree_payload": worktree_payload,
        "html": html_page,
        "refresh": max(1, args.refresh),
    }

    try:
        server = ThreadingHTTPServer((args.host, args.port), Handler)
    except OSError as exc:
        print("cannot bind %s:%d (%s)" % (args.host, args.port, exc), file=sys.stderr)
        return 1
    url = "http://%s:%d/" % ("127.0.0.1" if args.host == "0.0.0.0" else args.host, args.port)
    for label, path in paths:
        print("board:   %-8s %s" % (label, path))
    print("serving: %s" % url)
    print("stop with Ctrl-C")
    if args.open:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
