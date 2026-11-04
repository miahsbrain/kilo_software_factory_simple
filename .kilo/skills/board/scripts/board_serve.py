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
  --bg: #f7f7f5;
  --surface: #ffffff;
  --line: #e3e3df;
  --line-soft: #eeeeea;
  --ink: #16181a;
  --ink-soft: #5c6166;
  --ink-faint: #8b9096;
  --accent: #2f6feb;
  --accent-soft: #e8f0fe;
  --ok: #1f7a45;
  --warn: #9a6400;
  --bad: #b3261e;
  --radius: 6px;
  --radius-lg: 10px;
  --s1: 4px; --s2: 8px; --s3: 12px; --s4: 16px; --s6: 24px; --s8: 32px;
  --t-xs: 11px; --t-sm: 13px; --t-md: 15px; --t-lg: 20px; --t-xl: 30px;
  --mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
  --sans: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #101214;
    --surface: #171a1d;
    --line: #2a2f34;
    --line-soft: #22262a;
    --ink: #e8eaec;
    --ink-soft: #a4abb2;
    --ink-faint: #767d84;
    --accent: #6f9dff;
    --accent-soft: #1b2740;
    --ok: #56c58a;
    --warn: #e0ac4c;
    --bad: #ef8078;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font: var(--t-md)/1.55 var(--sans);
  -webkit-font-smoothing: antialiased;
}
a { color: var(--accent); }
header {
  padding: var(--s6) var(--s6) var(--s4);
  border-bottom: 1px solid var(--line);
  display: flex; flex-wrap: wrap; align-items: baseline; gap: var(--s3) var(--s6);
}
header > * { min-width: 0; }
h1 { font-size: var(--t-xl); line-height: 1.15; margin: 0; letter-spacing: -0.02em; font-weight: 650; }
.sub { color: var(--ink-soft); font-size: var(--t-sm); margin: 0; }
.spacer { flex: 1 1 auto; }
.meta {
  color: var(--ink-faint); font-size: var(--t-sm); font-family: var(--mono);
  overflow-wrap: anywhere; word-break: break-word; min-width: 0;
}
.banner {
  margin: var(--s4) var(--s6) 0; padding: var(--s3) var(--s4);
  border: 1px solid var(--bad); border-left-width: 3px; border-radius: var(--radius);
  color: var(--bad); background: var(--surface); font-size: var(--t-sm);
}
.filter { padding: var(--s4) var(--s6) 0; display: flex; flex-wrap: wrap; align-items: center; gap: var(--s2) var(--s3); }
.filter input {
  font: var(--t-sm)/1.4 var(--sans); color: var(--ink); background: var(--surface);
  border: 1px solid var(--line); border-radius: var(--radius); padding: var(--s2) var(--s3);
  min-width: 0; flex: 1 1 200px; max-width: 320px; min-height: 32px;
}
.filter input:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.panel { margin: var(--s6) var(--s6) 0; }
.panel-head {
  display: flex; flex-wrap: wrap; align-items: baseline; gap: var(--s3);
  border-bottom: 1px solid var(--line); padding-bottom: var(--s2); margin-bottom: var(--s3);
}
.panel-head > * { min-width: 0; }
.panel-head h2 { font-size: var(--t-md); margin: 0; font-weight: 600; letter-spacing: -0.01em; }
.panel-head .meta { margin-left: auto; }
details.panel > summary {
  list-style: none; cursor: pointer; min-height: 40px; align-items: center;
  border-radius: var(--radius);
}
details.panel > summary::-webkit-details-marker { display: none; }
details.panel > summary::marker { content: ""; }
details.panel > summary:hover { background: var(--line-soft); }
details.panel > summary:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.panel-title { font-size: var(--t-md); font-weight: 600; letter-spacing: -0.01em; }
.wt-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(320px, 100%), 1fr)); gap: var(--s2); }
.wt {
  border: 1px solid var(--line); border-radius: var(--radius); background: var(--surface);
  padding: var(--s3) var(--s4);
  display: flex; flex-wrap: wrap; align-items: center; gap: var(--s1) var(--s3);
}
.wt.branch { border-left: 3px solid var(--accent); }
.wt-branch { font-family: var(--mono); font-size: var(--t-sm); font-weight: 600; overflow-wrap: break-word; flex: 1 1 180px; min-width: 0; }
.wt-path { flex: 1 1 100%; font-family: var(--mono); font-size: var(--t-xs); color: var(--ink-faint); overflow-wrap: anywhere; word-break: break-word; min-width: 0; }
.wt-stat { font-family: var(--mono); font-size: var(--t-xs); color: var(--ink-soft); }
.wt-stat b { font-weight: 600; color: var(--ink); }
.tag {
  display: inline-block; font-size: var(--t-xs); font-family: var(--mono);
  border: 1px solid var(--line); border-radius: 999px; padding: 0 var(--s2); color: var(--ink-soft);
}
.tag.main { border-color: var(--accent); color: var(--accent); }
.tag.dirty { border-color: var(--bad); color: var(--bad); }
.board { margin: 0 var(--s6); }
.lane-stack {
  margin: var(--s6) 0 var(--s8);
  display: flex; flex-direction: column; gap: var(--s2);
  max-width: 1080px;
}
.lane { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-lg); }
.lane > summary {
  display: flex; align-items: center; gap: var(--s2);
  padding: var(--s3) var(--s4); cursor: pointer; min-height: 44px;
  list-style: none; border-radius: var(--radius-lg);
}
.lane > summary::-webkit-details-marker { display: none; }
.lane > summary::marker { content: ""; }
.lane > summary:hover { background: var(--line-soft); }
.lane > summary:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
.caret {
  color: var(--ink-faint); flex: none; font-size: var(--t-xs);
  transition: transform 150ms ease;
}
.lane[open] > summary .caret, .wt-panel[open] > summary .caret { transform: rotate(90deg); }
.lane-name { font-size: var(--t-sm); font-weight: 600; letter-spacing: 0.02em; text-transform: uppercase; color: var(--ink-soft); }
.count {
  font-family: var(--mono); font-size: var(--t-xs); color: var(--ink-faint);
  border: 1px solid var(--line); border-radius: var(--radius); padding: 0 var(--s2);
}
.lane-body { display: flex; flex-direction: column; gap: var(--s2); padding: 0 var(--s3) var(--s3); }
.card { border: 1px solid var(--line); border-radius: var(--radius); background: var(--bg); }
.card.extra { display: none; }
.lane-body.all .card.extra { display: block; }
.card > summary {
  display: flex; flex-wrap: wrap; align-items: center; gap: var(--s2);
  padding: var(--s2) var(--s3); cursor: pointer; min-height: 36px;
  list-style: none; border-radius: var(--radius);
}
.card > summary::-webkit-details-marker { display: none; }
.card > summary::marker { content: ""; }
.card > summary:hover { background: var(--line-soft); }
.card > summary:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
.card-id { font-family: var(--mono); font-size: var(--t-xs); font-weight: 700; color: var(--accent); }
.card-task { font-size: var(--t-sm); line-height: 1.35; margin: 0; font-weight: 550; flex: 1 1 240px; min-width: 0; }
.chip {
  font-size: var(--t-xs); font-family: var(--mono); border-radius: var(--radius);
  padding: 1px var(--s2); border: 1px solid var(--line); color: var(--ink-soft);
}
.chip.type { border-color: var(--line); }
.chip.prio { border-color: var(--ink-faint); color: var(--ink); }
.chip.risk { border-color: var(--line); display: inline-flex; align-items: center; gap: 6px; color: var(--ink-soft); }
.chip.risk.low { border-color: var(--ok); }
.chip.risk.medium { border-color: var(--warn); }
.chip.risk.high { border-color: var(--bad); }
.risk-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--ink-faint); flex: none; }
.chip.risk.low .risk-dot { background: var(--ok); }
.chip.risk.medium .risk-dot { background: var(--warn); }
.chip.risk.high .risk-dot { background: var(--bad); }
.card-detail { padding: 0 var(--s3) var(--s3); }
.card-notes {
  font-size: var(--t-xs); color: var(--ink-soft); margin: var(--s2) 0 0;
  white-space: pre-wrap; overflow-wrap: break-word;
}
.card-kv { display: grid; grid-template-columns: auto 1fr; gap: 0 var(--s2); font-size: var(--t-xs); margin: var(--s2) 0 0; }
.card-kv dt { color: var(--ink-faint); font-family: var(--mono); }
.card-kv dd { margin: 0; color: var(--ink-soft); font-family: var(--mono); overflow-wrap: anywhere; word-break: break-word; min-width: 0; }
.more {
  align-self: flex-start; font: var(--t-xs)/1.4 var(--mono); color: var(--accent);
  background: transparent; border: 1px solid var(--line); border-radius: var(--radius);
  padding: var(--s1) var(--s3); min-height: 28px; cursor: pointer;
}
.more:hover { border-color: var(--accent); }
.more:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.filter .more { align-self: center; }
.hint { color: var(--ink-faint); font-size: var(--t-xs); margin: var(--s2) 0 0; flex-basis: 100%; }
.empty { font-size: var(--t-xs); color: var(--ink-faint); padding: var(--s2) var(--s1); }
footer { padding: 0 var(--s6) var(--s8); color: var(--ink-faint); font-size: var(--t-xs); font-family: var(--mono); }
.hidden { display: none !important; }
.filtered { display: none !important; }
@media (max-width: 480px) {
  header { padding: var(--s4) var(--s3) var(--s3); gap: var(--s2) var(--s3); }
  h1 { font-size: var(--t-lg); }
  .meta { font-size: var(--t-xs); }
  .banner { margin: var(--s3) var(--s3) 0; }
  .filter { padding: var(--s4) var(--s3) 0; }
  .panel { margin: var(--s4) var(--s3) 0; }
  .board { margin: 0 var(--s3); }
  .lane-stack { margin: var(--s4) 0 var(--s6); }
  footer { padding: 0 var(--s3) var(--s6); }
}
"""

JS = """
(function () {
  var KEY = "board-dashboard-state";
  var state = {lanes: {}, cards: {}, more: {}};
  try {
    var saved = JSON.parse(window.localStorage.getItem(KEY) || "{}");
    if (saved && typeof saved === "object") {
      state.lanes = saved.lanes || {};
      state.cards = saved.cards || {};
      state.more = saved.more || {};
    }
  } catch (e) { /* storage is unavailable; the server defaults are used */ }

  function save() {
    try { window.localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* ignore */ }
  }

  function laneKey(el) { return el.getAttribute("data-board") + "::" + el.getAttribute("data-lane"); }
  function cardKey(el) {
    return laneKey(el) + "::" + el.getAttribute("data-card");
  }
  function has(obj, key) { return Object.prototype.hasOwnProperty.call(obj, key); }

  var lanes = Array.prototype.slice.call(document.querySelectorAll(".lane"));
  var cards = Array.prototype.slice.call(document.querySelectorAll(".card"));

  lanes.forEach(function (lane) {
    var key = laneKey(lane);
    if (has(state.lanes, key)) { lane.open = !!state.lanes[key]; }
    var body = lane.querySelector(".lane-body");
    var button = lane.querySelector(".more");
    if (button && body) {
      if (state.more[key]) { body.classList.add("all"); }
      var all = body.classList.contains("all");
      button.setAttribute("aria-expanded", all ? "true" : "false");
      button.textContent = all
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

  document.querySelectorAll(".lane .more").forEach(function (button) {
    button.addEventListener("click", function () {
      var lane = button.closest(".lane");
      var body = lane ? lane.querySelector(".lane-body") : null;
      if (!body) { return; }
      var all = body.classList.toggle("all");
      state.more[laneKey(lane)] = all;
      save();
      button.setAttribute("aria-expanded", all ? "true" : "false");
      button.textContent = all
        ? button.getAttribute("data-label-collapse")
        : button.getAttribute("data-label-expand");
    });
  });

  var input = document.getElementById("filter");
  var expand = document.getElementById("expand-matches");

  function apply() {
    var q = input ? input.value.trim().toLowerCase() : "";
    var closedWithMatches = 0;
    lanes.forEach(function (lane) {
      var body = lane.querySelector(".lane-body");
      var all = body ? body.classList.contains("all") : true;
      var laneCards = lane.querySelectorAll(".card");
      var shown = 0;
      var laneMatches = 0;
      Array.prototype.forEach.call(laneCards, function (card) {
        var hit = !q || card.textContent.toLowerCase().indexOf(q) !== -1;
        card.classList.toggle("filtered", !hit);
        if (!hit) { return; }
        laneMatches++;
        if (all || !card.classList.contains("extra")) { shown++; }
      });
      var empty = lane.querySelector(".empty");
      if (empty) { empty.classList.toggle("hidden", shown !== 0); }
      var count = lane.querySelector(".count");
      if (count) {
        count.textContent = q ? shown + "/" + laneCards.length : String(laneCards.length);
        count.title = q ? shown + " of " + laneCards.length + " cards match" : "";
      }
      if (laneMatches > 0 && !lane.open) { closedWithMatches++; }
    });
    if (expand) {
      expand.classList.toggle("hidden", !(q && closedWithMatches > 0));
      expand.textContent = "Open " + closedWithMatches + " matching lane(s)";
    }
  }

  if (expand) {
    expand.addEventListener("click", function () {
      var q = input.value.trim().toLowerCase();
      lanes.forEach(function (lane) {
        if (lane.open) { return; }
        var hit = Array.prototype.some.call(lane.querySelectorAll(".card"), function (card) {
          return !q || card.textContent.toLowerCase().indexOf(q) !== -1;
        });
        if (hit) { lane.open = true; }
      });
    });
  }

  if (input) {
    input.addEventListener("input", apply);
    apply();
  }
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
    tags = []
    if wt["main"]:
        tags.append('<span class="tag main">main checkout</span>')
    if wt["dirty"]:
        tags.append('<span class="tag dirty">dirty</span>')
    ahead = wt["ahead"] if wt["ahead"] is not None else "?"
    behind = wt["behind"] if wt["behind"] is not None else "?"
    return (
        '<div class="wt%s">'
        '<span class="wt-branch">%s</span>'
        '<span class="wt-stat">%s</span>'
        '<span class="wt-path">%s</span>'
        '<span class="wt-stat">ahead <b>%s</b> &middot; behind <b>%s</b>%s</span>'
        '</div>'
    ) % (
        " branch" if not wt["main"] else "",
        esc_path(wt["branch"]),
        " ".join(tags) if tags else (esc(wt["sha"] or "")),
        esc_path(wt["path"]),
        esc(ahead),
        esc(behind),
        "",
    )


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
        kv += "<dt>worktree</dt><dd>%s</dd>" % "<br>".join(
            esc_path(part) for part in branch_parts)
    fingerprint = row_fingerprint(row["Notes"])
    if fingerprint:
        kv += "<dt>fp</dt><dd>%s</dd>" % esc(fingerprint)
    notes = str(row.get("Notes raw", "")).strip()
    detail = ""
    if kv:
        detail += '<dl class="card-kv">%s</dl>' % kv
    if notes:
        detail += '<p class="card-notes">%s</p>' % esc(notes)
    return (
        '<details class="card%s" data-board="%s" data-lane="%s" data-card="%s">'
        '<summary>'
        '<span class="card-id">%s</span>'
        '<span class="card-task">%s</span>'
        '<span class="chip type">%s</span>'
        '<span class="chip prio">%s</span>'
        '%s'
        '</summary>'
        '<div class="card-detail">%s</div>'
        '</details>'
    ) % (
        " extra" if extra else "",
        esc(board_label),
        esc(lane),
        esc(row["ID"]),
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
    body += '<p class="empty%s">Nothing in this lane.</p>' % (" hidden" if cards else "")
    open_attr = " open" if lane_open_by_default(lane, len(lane_rows)) else ""
    return (
        '<details class="lane" data-board="%s" data-lane="%s"%s>'
        '<summary>'
        '<span class="caret" aria-hidden="true">&#9656;</span>'
        '<span class="lane-name">%s</span>'
        '<span class="count">%d</span>'
        '</summary>'
        '<div class="lane-body">%s%s</div>'
        '</details>'
    ) % (
        esc(board_label),
        esc(lane),
        open_attr,
        esc(lane),
        len(lane_rows),
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
        '<section class="board" data-board="%s">'
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


def build_html(boards, worktrees, generated_at, error, refresh):
    total = sum(len(entry["rows"]) for entry in boards)
    boards_html = "\n".join(render_board(entry) for entry in boards)
    if not boards_html:
        boards_html = '<p class="empty">No board file found.</p>'
    wt_html = "".join(render_worktree(wt) for wt in worktrees)
    if not wt_html:
        wt_html = '<p class="empty">No git worktrees found.</p>'
    active = sum(1 for wt in worktrees if not wt["main"])
    active_names = ", ".join(wt["branch"] for wt in worktrees if not wt["main"])
    wt_meta = "%d worktree(s) · %d non-main" % (len(worktrees), active)
    if active_names:
        wt_meta += ": " + active_names
    banner = ""
    if error:
        banner = '<p class="banner">%s</p>' % esc(error)
    lane_counts = []
    for entry in boards:
        counts = entry["counts"]
        lane_counts.append("%s: %s" % (
            entry["label"],
            ", ".join("%s %d" % (lane, counts.get(lane, 0))
                      for lane in LANE_ORDER if counts.get(lane, 0))))
    count_text = " | ".join(lane_counts)
    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta http-equiv="refresh" content="%d">'
        '<link rel="icon" href="%s">'
        "<title>Live board</title>"
        "<style>%s</style></head><body>\n"
        "<header>\n"
        "<div><h1>Live board</h1>\n"
        '<p class="sub">What is in flight right now. Lanes and worktrees, read from the board file on every request.</p></div>\n'
        '<div class="spacer"></div>\n'
        '<div class="meta">%s</div>\n'
        '<div class="meta">generated %s &middot; refresh %ds</div>\n'
        "</header>\n"
        "%s\n"
        '<div class="filter"><label class="meta" for="filter">Filter cards</label>\n'
        '<input id="filter" type="search" placeholder="task, id, branch" autocomplete="off">\n'
        '<button type="button" id="expand-matches" class="more hidden">Open matching lanes</button>\n'
        '<p class="hint">Fold a lane with the caret, open a card for its detail. Folds are kept in this browser.</p></div>\n'
        '<details class="panel wt-panel">\n'
        '<summary class="panel-head">'
        '<span class="caret" aria-hidden="true">&#9656;</span>'
        '<span class="panel-title">Live worktrees</span>'
        '<span class="meta">%s</span></summary>\n'
        '<div class="wt-list">%s</div>\n'
        "</details>\n"
        '%s\n'
        '<footer>%d card(s) across %d board(s)</footer>\n'
        "<script>%s</script>\n"
        "</body></html>"
    ) % (
        refresh,
        FAVICON,
        CSS,
        esc(count_text),
        esc(generated_at),
        refresh,
        banner,
        esc(wt_meta),
        wt_html,
        boards_html,
        total,
        len(boards),
        JS,
    )


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
