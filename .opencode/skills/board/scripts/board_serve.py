#!/usr/bin/env python3
"""Read-only live board dashboard.

    board_serve.py [--port 15180] [--host 127.0.0.1] [--open]
                   [--file PATH] [--refresh 60]

Serves a single-page HTML dashboard of docs/BOARD.md plus the live git
worktrees. Everything is read fresh on every request and nothing is ever
written: the board file and the repository are only read.

Endpoints:
    GET /                     the HTML dashboard
    GET /gallery              the component gallery (read-only)
    GET /static/board.css     the prebuilt Tailwind stylesheet
    GET /static/fonts/<file>  the two self-hosted Geist fonts and the licence
    GET /api/board            JSON: rows, lanes, generated_at
    GET /api/worktrees        JSON: the list of worktrees
    GET /health               JSON: {"ok": true}

Standard library only. Python 3.9+. The static CSS is built ahead of time by
`.opencode/skills/board/ui`; the server only reads it.
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
from pathlib import Path

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
DEFAULT_REFRESH = 60
BOARD_READ_HINT = (" Check that the board path (--file or docs/BOARD.md) "
                   "exists and is a valid board table.")
# Inline favicon: the page stays offline and makes no favicon request.
FAVICON = ("data:image/svg+xml,"
           "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E"
           "%3Crect width='16' height='16' rx='3' fill='%23c2410c'/%3E%3C/svg%3E")
STATIC_ROOT = Path(__file__).resolve().parent.parent / "static"
STATIC_FONT_TYPES = {
    "geist-sans-variable.woff2": "font/woff2",
    "geist-mono-variable.woff2": "font/woff2",
    "OFL.txt": "text/plain; charset=utf-8",
}


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
        if (os.path.exists(os.path.join(parent, ".opencode"))
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
        return [], (err or "cannot read the board") + BOARD_READ_HINT
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
    """Fresh worktrees for control and registered project, with stable repo ids."""
    repos, error = worktree.load_repos(root)
    if error:
        raise ValueError(error)
    entries = []
    for repo_id in ("control", "project"):
        if repo_id not in repos:
            continue
        target, error = worktree.resolve_repo(root, repos, repo_id)
        if error:
            raise ValueError(error)
        if repo_id != "control" and not worktree.is_git_repo(target):
            continue
        listed = worktree.list_worktrees(target)
        main_path = os.path.realpath(listed[0]["path"]) if listed else None
        base = worktree.default_base(target) if listed else None
        for wt in listed:
            path = os.path.abspath(wt["path"])
            branch = wt["branch"]
            short_sha = git_out(worktree, path, "rev-parse", "--short", "HEAD")
            if short_sha is None:
                short_sha = (wt["head"] or "")[:7] or None
            ahead = git_out(worktree, path, "rev-list", "--count", "%s..HEAD" % base)
            behind = git_out(worktree, path, "rev-list", "--count", "HEAD..%s" % base)
            dirty = git_out(worktree, path, "status", "--porcelain")
            entries.append({
                "path": path,
                "branch": branch or "(detached)",
                "sha": short_sha,
                "ahead": int(ahead) if ahead and ahead.isdigit() else None,
                "behind": int(behind) if behind and behind.isdigit() else None,
                "dirty": bool(dirty),
                "main": os.path.realpath(path) == main_path,
                "repo": repo_id,
                "base": base,
            })
    return entries


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

  var lanes = all(".wb-lane");
  var cards = all(".wb-card");
  var boards = all("[data-board-panel]");

  lanes.forEach(function (lane) {
    var key = laneKey(lane);
    if (has(state.lanes, key)) { lane.open = !!state.lanes[key]; }
    var body = lane.querySelector(".lane-body");
    var button = lane.querySelector(".wb-more");
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

  all(".wb-lane .wb-more").forEach(function (button) {
    button.addEventListener("click", function () {
      var lane = button.closest(".wb-lane");
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
  var typeSels = all("#type-filter, #main-type-filter");
  var prioSels = all("#priority-filter, #main-priority-filter");
  var typeSel = typeSels[0] || null;
  var prioSel = prioSels[0] || null;
  var resultCount = document.getElementById("result-count");
  var resetBtn = document.getElementById("reset");
  var searchClear = document.getElementById("search-clear");
  var kbd = document.querySelector(".wb-kbd");
  var pipes = all("[data-status-filter]");
  var themeBtn = document.getElementById("theme-toggle");
  var densityBtn = document.getElementById("density-toggle");
  var pauseBtn = document.getElementById("pause");
  var refreshBtn = document.getElementById("refresh");
  var live = document.querySelector(".wb-live");
  var liveText = document.querySelector(".wb-live-text");
  var statusFilter = "";
  var selected = null;

  var appbar = document.querySelector(".appbar");
  function measureAppbar() {
    document.documentElement.style.setProperty(
      "--appbar-h", appbar ? appbar.offsetHeight + "px" : "0px");
  }
  measureAppbar();
  window.addEventListener("resize", measureAppbar);
  if (window.ResizeObserver && appbar) {
    try { new ResizeObserver(measureAppbar).observe(appbar); } catch (e) { /* observer unavailable */ }
  }

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
      var laneCards = all(".wb-card", lane);
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

      var empty = lane.querySelector(".wb-empty");
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

      var count = lane.querySelector(".wb-lane-count");
      if (count) {
        count.textContent = anyActive
          ? laneShown + "/" + laneCards.length
          : String(laneCards.length);
      }
    });

    boards.forEach(function (board) {
      var visible = true;
      if (f.status) {
        visible = all(".wb-lane", board).some(function (lane) {
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
    var lane = card.closest(".wb-lane");
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

  function syncSelects(selects, value) {
    selects.forEach(function (sel) { sel.value = value; });
  }

  function clearFilters() {
    if (search) { search.value = ""; }
    syncSelects(typeSels, "");
    syncSelects(prioSels, "");
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
  function bindSelectSync(selects) {
    selects.forEach(function (sel) {
      sel.addEventListener("change", function () {
        syncSelects(selects, sel.value);
        apply();
      });
    });
  }
  bindSelectSync(typeSels);
  bindSelectSync(prioSels);
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

  var refreshSeconds = parseInt(document.body.getAttribute("data-refresh"), 10) || 60;
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
  function boardIdle() {
    if (paused) { return false; }
    if (document.visibilityState !== "visible") { return false; }
    if (document.querySelector(".wb-card[open]")) { return false; }
    if (search && search.value.trim()) { return false; }
    if (typeSel && typeSel.value) { return false; }
    if (prioSel && prioSel.value) { return false; }
    if (all(".lane-body.searching").length) { return false; }
    var active = document.activeElement;
    if (active && active !== document.body && active.closest && active.closest(".wb-layout")) {
      return false;
    }
    return true;
  }
  window.setInterval(function () {
    if (boardIdle()) { window.location.reload(); }
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
    if (params.get("type")) { syncSelects(typeSels, params.get("type")); }
    if (params.get("priority")) { syncSelects(prioSels, params.get("priority")); }
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

GALLERY_JS = """
(function () {
  var KEY = "board-dashboard-state";
  var state = {theme: "system", density: "comfortable"};
  try {
    var saved = JSON.parse(window.localStorage.getItem(KEY) || "{}");
    if (saved && typeof saved === "object") {
      if (saved.theme) { state.theme = saved.theme; }
      if (saved.density) { state.density = saved.density; }
    }
  } catch (e) { /* storage is unavailable; the server defaults are used */ }

  function save() {
    try { window.localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* ignore */ }
  }
  function each(selector, fn) {
    Array.prototype.forEach.call(document.querySelectorAll(selector), fn);
  }
  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    var label = theme === "system" ? "System" : (theme === "dark" ? "Dark" : "Light");
    each("[data-wb-theme]", function (button) {
      button.textContent = label;
      button.setAttribute("aria-label", "Colour theme: " + label + " (click to change)");
    });
    state.theme = theme;
  }
  function applyDensity(density) {
    var compact = density === "compact";
    document.body.classList.toggle("compact", compact);
    each("[data-wb-density]", function (button) {
      button.textContent = compact ? "Compact" : "Comfortable";
      button.setAttribute("aria-pressed", compact ? "true" : "false");
      button.setAttribute("aria-label", "Density: " + (compact ? "compact" : "comfortable") + " (click to change)");
    });
    state.density = compact ? "compact" : "comfortable";
  }
  each("[data-wb-theme]", function (button) {
    button.addEventListener("click", function () {
      var next = state.theme === "system" ? "light" : (state.theme === "light" ? "dark" : "system");
      applyTheme(next);
      save();
    });
  });
  each("[data-wb-density]", function (button) {
    button.addEventListener("click", function () {
      applyDensity(state.density === "compact" ? "comfortable" : "compact");
      save();
    });
  });
  each("[data-status-filter]", function (button) {
    button.addEventListener("click", function () {
      var lane = button.getAttribute("data-status-filter");
      var next = button.getAttribute("aria-pressed") !== "true";
      each("[data-status-filter]", function (peer) {
        if (peer.getAttribute("data-status-filter") === lane) {
          peer.setAttribute("aria-pressed", next ? "true" : "false");
        }
      });
    });
  });
  each("[data-copy]", function (button) {
    button.addEventListener("click", function () {
      var value = button.getAttribute("data-copy") || "";
      var done = function () {
        button.textContent = "copied";
        window.setTimeout(function () { button.textContent = "copy"; }, 1200);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(value).then(done, function () {});
      }
    });
  });
  var search = document.getElementById("search");
  document.addEventListener("keydown", function (event) {
    var target = event.target;
    var typing = target && (target.tagName === "INPUT" || target.tagName === "SELECT" ||
      target.tagName === "TEXTAREA" || target.isContentEditable);
    if (event.key === "/" && !typing && search) {
      event.preventDefault();
      search.focus();
      search.select();
    } else if (event.key === "Escape" && search && document.activeElement === search) {
      search.value = "";
      search.blur();
    }
  });
  applyTheme(state.theme);
  applyDensity(state.density);
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


def wb_meter(counts):
    """One segmented flow meter: a single track plus five clickable stops."""
    values = {lane: int(counts.get(lane, 0) or 0) for lane in ACTIVE_LANES}
    peak = max(values.values()) if values else 0
    segments = "".join(
        '<span class="wb-meter-seg" style="flex-grow: %d" data-peak="%s"></span>'
        % (count, "true" if peak and count == peak else "false")
        for count in values.values() if count > 0
    )
    stops = "".join(
        '<button type="button" class="wb-meter-stop" data-status-filter="%s" aria-pressed="false"%s%s>'
        '<span class="wb-meter-name">%s</span>'
        '<span class="wb-meter-count">%d</span></button>'
        % (esc(lane),
           ' data-peak="true"' if peak and count == peak else "",
           ' data-zero="true"' if count == 0 else "",
           esc(lane), count)
        for lane, count in values.items()
    )
    return (
        '<div class="wb-meter" role="group" aria-label="Work in flight by lane">'
        '<div class="wb-meter-track" aria-hidden="true">%s</div>'
        '<div class="wb-meter-stops">%s</div></div>'
    ) % (segments, stops)


def wb_lane(lane, count, description, cards_html, open=False, signal=False, board=""):
    """A 44px lane summary on the continuous board surface."""
    return (
        '<details class="wb-lane%s" data-board="%s" data-lane="%s"%s>'
        '<summary>'
        '<span class="wb-lane-rail" aria-hidden="true"></span>'
        '<span class="wb-lane-name">%s</span>'
        '<span class="wb-lane-count">%d</span>'
        '<span class="wb-lane-desc">%s</span>'
        '<span class="wb-caret" aria-hidden="true">&#9656;</span>'
        '</summary>'
        '<div class="wb-lane-body lane-body">%s</div>'
        '</details>'
    ) % (
        " wb-lane--signal" if signal else "",
        esc(board),
        esc(lane),
        " open" if open else "",
        esc(lane),
        count,
        esc(description),
        cards_html,
    )


def wb_chip(kind, text):
    dot = '<span class="wb-dot" aria-hidden="true"></span>' if kind.startswith("risk") else ""
    return '<span class="wb-chip wb-chip--%s">%s%s</span>' % (esc(kind), dot, esc(text))


def wb_empty(lane, hidden=False):
    text = EMPTY_TEXT.get(lane, "Nothing in this lane.")
    return '<p class="wb-empty%s" data-empty-default="%s">%s</p>' % (
        " hidden" if hidden else "", esc(text), esc(text))


def wb_card(card):
    """A 44px card row; the expanded body reuses render_notes and row_fingerprint."""
    card_id = clean_text(card.get("ID"))
    task = clean_text(card.get("Task"))
    kind = clean_text(card.get("Type"))
    priority = clean_text(card.get("Priority"))
    risk_text = clean_text(card.get("Risk"))
    level = risk_class(risk_text)
    risk_word = level if level else RISK_EMOJI.sub("", risk_text).strip()
    blocked = clean_text(card.get("Blocked by"))
    if blocked in ("-", "- None.", "", "None."):
        blocked = "none"
    branch = clean_text(card.get("Branch/Worktree"))
    if branch in ("-", ""):
        branch = ""
    fingerprint = row_fingerprint(card.get("Notes") or "")
    kv = ["<dt>Blocked by</dt><dd>%s</dd>" % esc(blocked)]
    if branch:
        name = branch_name(branch)
        copy = ""
        if name:
            copy = (
                '<button type="button" class="wb-copy" data-copy="%s"'
                ' aria-label="Copy branch %s">copy</button>'
            ) % (esc(name), esc(name))
        kv.append(
            '<dt>Branch</dt><dd><span class="wb-kv-line">%s%s</span></dd>'
            % (esc(branch), copy)
        )
    if fingerprint:
        kv.append("<dt>Fingerprint</dt><dd>%s</dd>" % esc(fingerprint))
    detail = '<dl class="wb-card-kv">%s</dl>' % "".join(kv)
    notes_html = render_notes(str(card.get("Notes raw", "")).strip())
    if notes_html:
        detail += notes_html
    chips = (
        wb_chip("type", kind)
        + wb_chip("prio", priority)
        + wb_chip("risk-" + (level or "unknown"), risk_word)
    )
    return (
        '<details class="wb-card%s" data-board="%s" data-lane="%s" data-card="%s"'
        ' data-type="%s" data-priority="%s"%s>'
        '<summary>'
        '<span class="wb-card-id">%s</span>'
        '<span class="wb-card-task">%s</span>'
        '%s'
        '<span class="wb-caret" aria-hidden="true">&#9656;</span>'
        '</summary>'
        '<div class="wb-card-detail">%s</div>'
        '</details>'
    ) % (
        " extra" if card.get("extra") else "",
        esc(card.get("board", "")),
        esc(card.get("lane", "")),
        esc(card_id),
        esc(kind),
        esc(priority),
        " open" if card.get("open") else "",
        esc(card_id),
        esc(task),
        chips,
        detail,
    )


def wb_panel(title, meta, body_html, attrs=""):
    """A 12px, hairline, soft-shadow dashboard panel with a 40px header."""
    return (
        '<section class="wb-panel"%s>'
        '<div class="wb-panel-head"><h2 class="wb-panel-title">%s</h2>'
        '<span class="wb-panel-meta">%s</span></div>'
        '%s</section>'
    ) % (attrs, esc(title), esc(meta), body_html)


def wb_rail(title, meta, body_html):
    """The sticky worktrees panel."""
    return (
        '<aside class="wb-rail">'
        '<div class="wb-rail-head"><h2 class="wb-rail-title">%s</h2>'
        '<span class="wb-rail-meta">%s</span></div>'
        '<div class="wb-rail-body">%s</div>'
        '</aside>'
    ) % (esc(title), esc(meta), body_html)


def wb_filter_selects(prefix, visible_labels=False):
    """Type and priority selects; `prefix` keeps sidebar and toolbar ids unique."""
    types = ("Feature", "Fix", "Chore", "Docs", "Research")
    priorities = ("P1", "P2", "P3", "P4")
    type_options = '<option value="">All types</option>' + "".join(
        '<option value="%s">%s</option>' % (esc(t), esc(t)) for t in types)
    prio_options = '<option value="">All priorities</option>' + "".join(
        '<option value="%s">%s</option>' % (esc(p), esc(p)) for p in priorities)
    type_id = ("%s-type-filter" % prefix) if prefix else "type-filter"
    prio_id = ("%s-priority-filter" % prefix) if prefix else "priority-filter"
    type_label = "Type" if visible_labels else "Filter by type"
    prio_label = "Priority" if visible_labels else "Filter by priority"
    label_class = "wb-field-label" if visible_labels else "sr-only"
    return (
        '<div class="wb-field"><label class="%s" for="%s">%s</label>'
        '<span class="wb-select-wrap"><select id="%s" class="wb-select">%s</select></span></div>'
        '<div class="wb-field"><label class="%s" for="%s">%s</label>'
        '<span class="wb-select-wrap"><select id="%s" class="wb-select">%s</select></span></div>'
    ) % (
        label_class, esc(type_id), esc(type_label), esc(type_id), type_options,
        label_class, esc(prio_id), esc(prio_label), esc(prio_id), prio_options,
    )


def wb_toolbar(total=0):
    return (
        '<div class="wb-toolbar" role="search">'
        '<div class="wb-search">'
        '<label class="sr-only" for="search">Search cards</label>'
        '<input id="search" type="search" placeholder="Search id, task, branch"'
        ' autocomplete="off" spellcheck="false">'
        '<button type="button" id="search-clear" class="wb-search-clear"'
        ' aria-label="Clear search" hidden>&times;</button>'
        '<kbd class="wb-kbd" aria-hidden="true">/</kbd>'
        '</div>'
        '<div class="wb-toolbar-filters">%s</div>'
        '<span id="result-count" class="wb-result" aria-live="polite">showing %d of %d</span>'
        '<button type="button" id="reset" class="wb-btn" hidden>Reset</button>'
        '</div>'
    ) % (wb_filter_selects("main"), total, total)


def wb_wt_row(worktree):
    tags = []
    if worktree["main"]:
        tags.append(wb_chip("main", "main"))
    tags.append(wb_chip("dirty", "dirty") if worktree["dirty"] else wb_chip("clean", "clean"))
    ahead = worktree["ahead"] if worktree["ahead"] is not None else "?"
    behind = worktree["behind"] if worktree["behind"] is not None else "?"
    return (
        '<div class="wb-wt">'
        '<div class="wb-wt-top">'
        '<span class="wb-wt-branch">%s</span>%s'
        '<span class="wb-wt-figs">'
        '<span aria-label="ahead %s">+%s</span>'
        '<span aria-label="behind %s">-%s</span>'
        '</span></div>'
        '<span class="wb-wt-path">%s</span>'
        '</div>'
    ) % (
        esc(worktree["branch"]),
        " ".join(tags),
        esc(ahead), esc(ahead),
        esc(behind), esc(behind),
        esc(worktree["path"]),
    )


def row_fingerprint(notes):
    """The fingerprint carried in a row's Notes cell, or an empty string."""
    match = re.search(r"\bfp=([^\s|·]+\|[^\s|·]+\|[^\s|·]+\|[^\s|·]+)", clean_text(notes))
    return match.group(1) if match else ""


def lane_open_by_default(lane, card_count):
    """A lane with no cards stays collapsed; the server knows the card count."""
    if card_count == 0:
        return False
    return lane not in COLLAPSED_BY_DEFAULT


def wb_lane_filters(counts):
    """Sidebar lane rows; the meter stops reuse the same data attribute."""
    return "".join(
        '<button type="button" class="wb-lane-filter" data-status-filter="%s" aria-pressed="false">'
        '<span class="wb-lane-filter-name">%s</span>'
        '<span class="wb-lane-filter-count">%d</span></button>'
        % (esc(lane), esc(lane), int(counts.get(lane, 0) or 0))
        for lane in ACTIVE_LANES
    )


def wb_row_card(row, board_label, lane, extra=False):
    """Adapt a board row to the shared wb_card component."""
    card = dict(row)
    card.update({"board": board_label, "lane": lane, "extra": extra})
    return wb_card(card)


def render_board_lane(lane, rows, board_label, signal=False):
    lane_rows = [row for row in rows if row["Status"] == lane]
    preview = lane_rows
    extra = []
    if lane == "Merged" and len(lane_rows) > MERGED_PREVIEW:
        preview = lane_rows[-MERGED_PREVIEW:]
        extra = lane_rows[:-MERGED_PREVIEW]
    cards = [wb_row_card(row, board_label, lane, extra=True) for row in extra]
    cards += [wb_row_card(row, board_label, lane) for row in preview]
    more = ""
    if extra:
        more = (
            '<button type="button" class="wb-more" aria-expanded="false"'
            ' data-label-expand="Show all %d" data-label-collapse="Show only the last %d">'
            'Show all %d</button>'
        ) % (len(lane_rows), MERGED_PREVIEW, len(lane_rows))
    body = "".join(cards) + wb_empty(lane, hidden=bool(cards)) + more
    return wb_lane(
        lane,
        len(lane_rows),
        LANE_DESCRIPTION.get(lane, ""),
        body,
        open=lane_open_by_default(lane, len(lane_rows)),
        signal=signal,
        board=board_label,
    )


def board_signal_lane(counts):
    peak = max((int(counts.get(lane, 0) or 0) for lane in ACTIVE_LANES), default=0)
    if peak <= 0:
        return None
    for lane in ACTIVE_LANES:
        if int(counts.get(lane, 0) or 0) == peak:
            return lane
    return None


def render_board_panel(entry, toolbar_html=""):
    """A board panel: its toolbar, path, banner and every lane."""
    rows = entry["rows"]
    signal = board_signal_lane(entry["counts"])
    lanes_html = "".join(
        render_board_lane(lane, rows, entry["label"], signal=(lane == signal))
        for lane in LANE_ORDER
    )
    path = '<p class="wb-board-path" title="%s">%s</p>' % (
        esc(entry["path"]), esc_path(entry["path"]))
    banner = ""
    if entry.get("error"):
        banner = '<p class="wb-banner" role="alert">%s</p>' % esc(entry["error"])
    body = toolbar_html + path + banner + '<div class="wb-lanes">%s</div>' % lanes_html
    return wb_panel(
        "%s board" % entry["label"],
        "%d cards" % len(rows),
        body,
        attrs=' data-board-panel="%s"' % esc(entry["label"]),
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


def render_board_toolbar(total, board_count):
    """With several boards the toolbar sits in its own panel."""
    return wb_panel(
        "Board",
        "%d boards · %d cards" % (board_count, total),
        wb_toolbar(total),
    )


def build_html(boards, worktrees, generated_at, error, refresh):
    total = sum(len(entry["rows"]) for entry in boards)
    counts = active_counts(boards)
    active_total = sum(counts.values())
    if active_total == 0:
        merged = last_merged_id(boards)
        subtitle_bits = ["Nothing in flight"]
        if merged:
            subtitle_bits.append("last merged %s" % merged)
        subtitle_bits.append("as of %s" % generated_at.split("T")[0])
        subtitle = " · ".join(subtitle_bits)
    else:
        subtitle = ("Lanes, cards and live worktrees — what is in flight right now. "
                    "Read fresh on every request.")

    if len(boards) == 1:
        panels_html = render_board_panel(boards[0], wb_toolbar(total))
    elif boards:
        panels_html = render_board_toolbar(total, len(boards))
        panels_html += "".join(render_board_panel(entry) for entry in boards)
    else:
        panels_html = wb_panel(
            "Board", "0 cards",
            '<p class="wb-empty">No board file found. Point the server at one with --file.</p>')

    banner = ""
    if error:
        banner = '<p class="wb-banner" role="alert">%s</p>' % esc(error)

    kpi_facts = "".join(
        '<div class="wb-kpi-fact"><span class="wb-kpi-num-sm">%d</span>'
        '<span class="wb-kpi-label">%s</span></div>' % (value, esc(label))
        for value, label in (
            (counts.get("Pending Merge", 0), "pending merge"),
            (counts.get("Blocked", 0), "blocked"),
            (total, "total"),
        )
    )

    active = sum(1 for wt in worktrees if not wt["main"])
    wt_meta = "%d worktrees · %d non-main" % (len(worktrees), active)
    ordered_worktrees = sorted(worktrees, key=lambda wt: 1 if wt["main"] else 0)
    rail_body = "".join(wb_wt_row(wt) for wt in ordered_worktrees)
    if not rail_body:
        rail_body = ('<p class="wb-empty">No git worktrees found. '
                     'Start one with worktree.py create.</p>')
    rail = wb_rail("Worktrees", wt_meta, rail_body)

    try:
        epoch_ms = int(datetime.datetime.fromisoformat(generated_at).timestamp() * 1000)
    except (TypeError, ValueError):
        epoch_ms = 0
    mark = (
        '<svg class="wb-mark" viewBox="0 0 24 24" aria-hidden="true" fill="none" '
        'stroke="currentColor" stroke-width="1.8" stroke-linejoin="round">'
        '<path d="M3 20V9l6 3V9l6 3V4h6v16z"/>'
        '<path d="M6 16h3M12 16h3"/></svg>'
    )
    theme_boot = (
        'try{var s=JSON.parse(localStorage.getItem("board-dashboard-state")||"{}");'
        'if(s&&s.theme){document.documentElement.setAttribute("data-theme",s.theme);}}'
        'catch(e){}'
    )
    html_parts = [
        "<!doctype html>\n",
        '<html lang="en" data-theme="system"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="color-scheme" content="light dark">',
        '<link rel="icon" href="', FAVICON, '">',
        '<link rel="stylesheet" href="/static/board.css">',
        "<title>Factory board</title><script>", theme_boot, "</script></head><body",
        ' data-refresh="', str(refresh), '">\n',
        '<div class="wb-layout">',
        '<aside class="wb-sidebar">',
        '<div class="wb-side-brand">', mark,
        '<div class="min-w-0"><span class="wb-wordmark">Factory board</span>',
        '<span class="wb-brand-meta">Read-only · live</span></div></div>',
        '<nav class="wb-side-nav" aria-label="Lane filters">',
        '<p class="wb-side-label">Lanes</p>',
        '<div class="wb-lane-filters">', wb_lane_filters(counts), '</div></nav>',
        '<div class="wb-side-filters">',
        '<p class="wb-side-label">Filters</p>',
        wb_filter_selects("", visible_labels=True),
        '</div>',
        '<div class="wb-side-footer">',
        '<p class="wb-live" data-ms="', str(epoch_ms), '">',
        '<span class="wb-live-dot" aria-hidden="true"></span>',
        '<span class="wb-live-text">updated ', esc(generated_at[11:19]), '</span></p>',
        '<div class="wb-side-actions">',
        '<button type="button" class="wb-btn" id="pause" aria-pressed="false">Pause</button>',
        '<button type="button" class="wb-btn" id="theme-toggle" aria-label="Colour theme">System</button>',
        '<button type="button" class="wb-btn" id="density-toggle" aria-pressed="false"',
        ' aria-label="Density">Comfortable</button>',
        '</div></div></aside>',
        '<main class="wb-main">',
        '<header class="wb-page-head">',
        '<div class="min-w-0"><h1 class="wb-title">Factory board</h1>',
        '<p class="wb-sub">', esc(subtitle), '</p></div>',
        '<button type="button" class="wb-btn" id="refresh">Refresh now</button>',
        '</header>',
        '<section class="wb-kpi" aria-label="Board summary">',
        '<div class="wb-kpi-primary"><span class="wb-kpi-num">%d</span>' % active_total,
        '<span class="wb-kpi-label">in flight</span></div>',
        kpi_facts,
        '</section>',
        wb_panel("Flow", "%d lanes" % len(ACTIVE_LANES), wb_meter(counts)),
        banner,
        panels_html,
        '<footer class="wb-footer">', str(total), ' card' + ('' if total == 1 else 's'),
        ' across ', str(len(boards)), ' board' + ('' if len(boards) == 1 else 's'),
        ' · refresh every ', str(refresh), 's, pausable',
        ' · <a href="/gallery">Components</a></footer>',
        '</main>',
        rail,
        '</div>',
        "<script>", JS, "</script>\n",
        "</body></html>",
    ]
    return "".join(html_parts)


GALLERY_COUNTS = {
    "Ready": 0,
    "In Progress": 0,
    "In Review": 2,
    "Pending Merge": 0,
    "Blocked": 1,
}
WB_SWATCHES = (
    ("--color-paper", "canvas"),
    ("--color-surface", "surface"),
    ("--color-surface-2", "surface 2"),
    ("--color-ink", "ink"),
    ("--color-ink-soft", "ink soft"),
    ("--color-ink-faint", "ink faint"),
    ("--color-line", "line"),
    ("--color-line-soft", "line soft"),
    ("--color-signal", "signal"),
    ("--color-signal-soft", "signal soft"),
    ("--color-ok", "ok"),
    ("--color-warn", "warn"),
    ("--color-bad", "bad"),
)
WB_TYPE_STEPS = (
    ("--text-micro", "11px", "Meta and chips"),
    ("--text-tiny", "12px", "Dense controls"),
    ("--text-meta", "13px", "Body and rows"),
    ("--text-body", "15px", "Lead paragraphs"),
    ("--text-lead", "20px", "Section and figures"),
    ("--text-display", "32px", "Page title"),
)
WB_SPACE_STEPS = (
    ("4px", 4),
    ("8px", 8),
    ("12px", 12),
    ("16px", 16),
    ("24px", 24),
    ("32px", 32),
    ("48px", 48),
    ("64px", 64),
)
WB_RADII = (("6px", "chip"), ("8px", "control"), ("12px", "panel"))


def gallery_tokens_html():
    swatches = "".join(
        '<div class="wb-swatch"><span class="wb-swatch-chip" style="background: var(%s)"></span>'
        '<span class="wb-swatch-label">%s</span></div>' % (esc(name), esc(label))
        for name, label in WB_SWATCHES
    )
    type_rows = "".join(
        '<div class="wb-type-row"><span class="wb-type-sample" style="font-size: var(%s)">'
        'Factory components</span><span class="wb-type-label">%s · %s</span></div>'
        % (esc(name), esc(size), esc(role))
        for name, size, role in WB_TYPE_STEPS
    )
    space_rows = "".join(
        '<div class="wb-space-row"><span class="wb-space-bar" style="width: %dpx"></span>'
        '<span>%s</span></div>' % (px, esc(name))
        for name, px in WB_SPACE_STEPS
    )
    radius_boxes = "".join(
        '<div class="wb-radius-box" style="border-radius: %s">%s</div>'
        % (esc(value), esc(label))
        for value, label in WB_RADII
    )
    return (
        '<div class="wb-tokens">'
        '<div class="wb-token-group"><h3>Colour</h3>'
        '<div class="wb-swatches">%s</div></div>'
        '<div class="wb-token-group"><h3>Type</h3>%s</div>'
        '<div class="wb-token-group"><h3>Spacing</h3>%s</div>'
        '<div class="wb-token-group"><h3>Radius</h3>'
        '<div class="wb-radius-row">%s</div></div>'
        '</div>'
    ) % (swatches, type_rows, space_rows, radius_boxes)


def gallery_fixtures():
    open_card = {
        "ID": "BOARD-112",
        "Task": "Rebuild the factory gallery in Tailwind",
        "Type": "Feature",
        "Priority": "P2",
        "Risk": "🟡 medium — visual only, the console is read-only",
        "Blocked by": "- None.",
        "Branch/Worktree": ("branch feat/rebuild-factory-pages-as-a-split · "
                            ".opencode/worktrees/rebuild-factory-pages-as-a-split"),
        "Notes": "fp=feat|visual|/gallery|swiss",
        "Notes raw": ("- [x] /gallery serves the prebuilt stylesheet proof: HTTP 200 text/css · "
                      "- [ ] Peak lane is the only signal segment proof: capture 1440 · "
                      "- [ ] Board page keeps its inline CSS until the next chunk"),
        "open": True,
    }
    second_card = {
        "ID": "BOARD-113",
        "Task": "Wire the lane filters to the worktree rail",
        "Type": "Fix",
        "Priority": "P1",
        "Risk": "🟢 low — fixture only",
        "Blocked by": "BOARD-112",
        "Branch/Worktree": "branch feat/workbench-filters",
        "Notes": "",
        "Notes raw": ("- [ ] Filter state stays in the URL · "
                      "- [ ] Escape clears every control"),
    }
    blocked_card = {
        "ID": "BOARD-104",
        "Task": "Decide whether the rail folds below the lanes at tablet width",
        "Type": "Feature",
        "Priority": "P3",
        "Risk": "🟡 medium — layout only",
        "Blocked by": "- None.",
        "Branch/Worktree": "-",
        "Notes": "",
        "Notes raw": "Waiting on gallery approval before the split breakpoint is fixed.",
    }
    worktrees = [
        {"main": True, "branch": "main", "path": "/workspaces/yt",
         "ahead": 0, "behind": 0, "dirty": False},
        {"main": False, "branch": "feat/rebuild-factory-pages-as-a-split",
         "path": "/workspaces/yt/.opencode/worktrees/rebuild-factory-pages-as-a-split",
         "ahead": 3, "behind": 0, "dirty": False},
        {"main": False, "branch": "feat/board-console",
         "path": "/workspaces/yt/.opencode/worktrees/board-console",
         "ahead": 7, "behind": 2, "dirty": True},
    ]
    return open_card, second_card, blocked_card, worktrees


def build_gallery_html():
    open_card, second_card, blocked_card, worktrees = gallery_fixtures()
    counts = GALLERY_COUNTS
    total = sum(counts.values())
    lane_cards = {
        "In Review": wb_card(open_card) + wb_card(second_card),
        "Blocked": wb_card(blocked_card),
    }
    open_lanes = {"In Review", "Blocked"}
    lanes = "".join(
        wb_lane(
            lane,
            counts.get(lane, 0),
            LANE_DESCRIPTION[lane],
            lane_cards.get(lane) or wb_empty(lane),
            open=lane in open_lanes,
            signal=counts.get(lane, 0) == max(counts.values()),
        )
        for lane in ACTIVE_LANES
    )
    lane_filters = "".join(
        '<button type="button" class="wb-lane-filter" data-status-filter="%s" aria-pressed="false">'
        '<span class="wb-lane-filter-name">%s</span>'
        '<span class="wb-lane-filter-count">%d</span></button>'
        % (esc(lane), esc(lane), counts.get(lane, 0))
        for lane in ACTIVE_LANES
    )
    rail_body = "".join(wb_wt_row(worktree) for worktree in worktrees)
    rail_body += ('<p class="wb-legend">+ ahead · − behind · chips show main, dirty and clean</p>')
    rail = wb_rail("Worktrees", "3 worktrees · 2 non-main", rail_body)
    chips = " ".join(
        wb_chip(kind, text) for kind, text in (
            ("type", "Feature"), ("prio", "P2"),
            ("risk-low", "low"), ("risk-medium", "medium"), ("risk-high", "high"),
            ("main", "main"), ("dirty", "dirty"), ("clean", "clean"),
        )
    )
    mark = (
        '<svg class="wb-mark" viewBox="0 0 24 24" aria-hidden="true" '
        'fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round">'
        '<path d="M3 20V9l6 3V9l6 3V4h6v16z"/>'
        '<path d="M6 16h3M12 16h3"/></svg>'
    )
    kpi_facts = "".join(
        '<div class="wb-kpi-fact"><span class="wb-kpi-num-sm">%d</span>'
        '<span class="wb-kpi-label">%s</span></div>' % (value, esc(label))
        for value, label in (
            (counts.get("Pending Merge", 0), "pending merge"),
            (counts.get("Blocked", 0), "blocked"),
            (total, "total"),
        )
    )
    return "".join([
        "<!doctype html>\n",
        '<html lang="en" data-theme="system"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="color-scheme" content="light dark">',
        '<link rel="icon" href="', FAVICON, '">',
        '<link rel="stylesheet" href="/static/board.css">',
        "<title>Factory board</title></head><body>\n",
        '<div class="wb-layout">',
        '<aside class="wb-sidebar">',
        '<div class="wb-side-brand">', mark,
        '<div class="min-w-0"><span class="wb-wordmark">Factory board</span>',
        '<span class="wb-brand-meta">Component gallery</span></div></div>',
        '<nav class="wb-side-nav" aria-label="Lane filters">',
        '<p class="wb-side-label">Lanes</p>',
        '<div class="wb-lane-filters">', lane_filters, '</div></nav>',
        '<div class="wb-side-filters">',
        '<p class="wb-side-label">Filters</p>',
        wb_filter_selects("side", visible_labels=True),
        '</div>',
        '<div class="wb-side-footer">',
        '<p class="wb-live"><span class="wb-live-dot" aria-hidden="true"></span>'
        '<span>updated %s</span></p>' % datetime.datetime.now().strftime("%H:%M:%S"),
        '<div class="wb-side-actions">',
        '<button type="button" class="wb-btn" id="pause" aria-pressed="false">Pause</button>',
        '<button type="button" class="wb-btn" data-wb-theme aria-label="Colour theme">System</button>',
        '<button type="button" class="wb-btn" data-wb-density aria-pressed="false" '
        'aria-label="Density">Comfortable</button>',
        '</div></div></aside>',
        '<main class="wb-main">',
        '<header class="wb-page-head">',
        '<div class="min-w-0"><h1 class="wb-title">Factory board</h1>',
        '<p class="wb-sub">Lanes, cards and live worktrees — what is in flight right now</p></div>',
        '<button type="button" class="wb-btn" id="refresh-now">Refresh now</button>',
        '</header>',
        '<section class="wb-kpi" aria-label="Board summary">',
        '<div class="wb-kpi-primary"><span class="wb-kpi-num">%d</span>'
        '<span class="wb-kpi-label">in flight</span></div>' % total,
        kpi_facts,
        '</section>',
        wb_panel(
            "Flow",
            "%d lanes" % len(ACTIVE_LANES),
            wb_meter(counts),
        ),
        '<section class="wb-panel">',
        wb_toolbar(total),
        '<div class="wb-lanes">', lanes, '</div>',
        '</section>',
        '</main>',
        rail,
        '</div>',
        '<div class="wb-sections">',
        '<section class="wb-section">',
        '<h2 class="wb-section-title">Chips and empty state</h2>',
        '<p class="wb-section-meta">Chips stay quiet. The empty state names the next action.</p>',
        '<div class="flex flex-wrap items-center gap-2 py-3">', chips, '</div>',
        wb_empty("Ready"),
        '</section>',
        '<section class="wb-section">',
        '<h2 class="wb-section-title">Tokens</h2>',
        '<p class="wb-section-meta">The language is tokens, not one-off values. '
        'Swatches follow the active theme.</p>',
        gallery_tokens_html(),
        '</section>',
        '</div>',
        '<footer class="mx-auto w-full max-w-[1600px] px-6 pb-16 font-mono text-micro '
        'text-ink-faint"><a href="/">Back to the board</a></footer>\n',
        "<script>", GALLERY_JS, "</script>\n",
        "</body></html>",
    ])


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

    def send_file(self, path, content_type):
        try:
            body = Path(path).read_bytes()
        except OSError:
            self.send_bytes(404, b"not found\n", "text/plain; charset=utf-8")
            return
        self.send_bytes(200, body, content_type)

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
        if path == "/static/board.css":
            self.send_file(STATIC_ROOT / "board.css", "text/css; charset=utf-8")
            return
        if path.startswith("/static/fonts/"):
            name = path[len("/static/fonts/"):]
            content_type = STATIC_FONT_TYPES.get(name)
            if not content_type:
                self.send_bytes(404, b"not found\n", "text/plain; charset=utf-8")
                return
            self.send_file(STATIC_ROOT / "fonts" / name, content_type)
            return
        if path == "/":
            html_body = self.state["html"]()
            self.send_bytes(200, html_body.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path == "/gallery":
            html_body = self.state["gallery"]()
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
        current_paths = paths if paths is not None else (
            discover_boards(root) or [("board", board_file(None, root))])
        return {
            "boards": board_states(board, current_paths),
            "generated_at": now(),
        }

    def worktree_payload():
        try:
            return worktree_state(worktree, root)
        except Exception:
            return []

    def html_page():
        try:
            states = board_payload()["boards"]
            state = worktree_state(worktree, root)
            error = None
        except Exception as exc:
            states, state = [], []
            error = "could not read the board: %s%s" % (exc, BOARD_READ_HINT)
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
        paths = None

    board_payload, worktree_payload, html_page = build_payloads(board, worktree, paths, root)
    Handler.state = {
        "board_payload": board_payload,
        "worktree_payload": worktree_payload,
        "html": html_page,
        "gallery": build_gallery_html,
        "refresh": max(1, args.refresh),
    }

    try:
        server = ThreadingHTTPServer((args.host, args.port), Handler)
    except OSError as exc:
        print("cannot bind %s:%d (%s)" % (args.host, args.port, exc), file=sys.stderr)
        return 1
    url = "http://%s:%d/" % ("127.0.0.1" if args.host == "0.0.0.0" else args.host, args.port)
    for label, path in (paths if paths is not None else discover_boards(root)):
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
