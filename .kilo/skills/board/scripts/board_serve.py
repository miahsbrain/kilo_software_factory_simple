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
COLUMNS = ["ID", "Task", "Type", "Status", "Priority", "Risk", "Blocked by",
           "Branch/Worktree", "Notes"]
GIT_TIMEOUT = 5
DEFAULT_PORT = 15180
DEFAULT_HOST = "127.0.0.1"
DEFAULT_REFRESH = 10


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
h1 { font-size: var(--t-xl); line-height: 1.15; margin: 0; letter-spacing: -0.02em; font-weight: 650; }
.sub { color: var(--ink-soft); font-size: var(--t-sm); margin: 0; }
.spacer { flex: 1 1 auto; }
.meta { color: var(--ink-faint); font-size: var(--t-sm); font-family: var(--mono); }
.banner {
  margin: var(--s4) var(--s6) 0; padding: var(--s3) var(--s4);
  border: 1px solid var(--bad); border-left-width: 3px; border-radius: var(--radius);
  color: var(--bad); background: var(--surface); font-size: var(--t-sm);
}
.filter { padding: var(--s4) var(--s6) 0; }
.filter input {
  font: var(--t-sm)/1.4 var(--sans); color: var(--ink); background: var(--surface);
  border: 1px solid var(--line); border-radius: var(--radius); padding: var(--s2) var(--s3);
  min-width: 260px;
}
.filter input:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.panel { margin: var(--s6) var(--s6) 0; }
.panel-head {
  display: flex; align-items: baseline; gap: var(--s3);
  border-bottom: 1px solid var(--line); padding-bottom: var(--s2); margin-bottom: var(--s3);
}
.panel-head h2 { font-size: var(--t-md); margin: 0; font-weight: 600; letter-spacing: -0.01em; }
.panel-head .meta { margin-left: auto; }
.wt-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(320px, 100%), 1fr)); gap: var(--s2); }
.wt {
  border: 1px solid var(--line); border-radius: var(--radius); background: var(--surface);
  padding: var(--s3) var(--s4);
  display: flex; flex-wrap: wrap; align-items: center; gap: var(--s1) var(--s3);
}
.wt.branch { border-left: 3px solid var(--accent); }
.wt-branch { font-family: var(--mono); font-size: var(--t-sm); font-weight: 600; overflow-wrap: break-word; flex: 1 1 180px; min-width: 0; }
.wt-path { flex: 1 1 100%; font-family: var(--mono); font-size: var(--t-xs); color: var(--ink-faint); overflow-wrap: normal; word-break: normal; min-width: 0; }
.wt-stat { font-family: var(--mono); font-size: var(--t-xs); color: var(--ink-soft); }
.wt-stat b { font-weight: 600; color: var(--ink); }
.tag {
  display: inline-block; font-size: var(--t-xs); font-family: var(--mono);
  border: 1px solid var(--line); border-radius: 999px; padding: 0 var(--s2); color: var(--ink-soft);
}
.tag.main { border-color: var(--accent); color: var(--accent); }
.tag.dirty { border-color: var(--bad); color: var(--bad); }
.lanes {
  margin: var(--s6) var(--s6) var(--s8);
  display: grid; grid-auto-flow: column; grid-auto-columns: minmax(280px, 1fr);
  gap: var(--s3); overflow-x: scroll; padding-bottom: var(--s3);
  align-items: start;
  scroll-snap-type: x proximity;
  scroll-behavior: smooth;
  overscroll-behavior-x: contain;
}
.lanes::-webkit-scrollbar { height: 12px; }
.lanes::-webkit-scrollbar-track { background: var(--line-soft); border-radius: 999px; }
.lanes::-webkit-scrollbar-thumb { background: var(--ink-faint); border-radius: 999px; }
.lane {
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-lg);
  padding: var(--s3); min-width: 280px;
  scroll-snap-align: start;
}
.lane-head {
  display: flex; align-items: center; gap: var(--s2);
  padding: 0 var(--s1) var(--s3);
}
.lane-head h3 { font-size: var(--t-sm); margin: 0; font-weight: 600; letter-spacing: 0.01em; text-transform: uppercase; color: var(--ink-soft); }
.count {
  font-family: var(--mono); font-size: var(--t-xs); color: var(--ink-faint);
  border: 1px solid var(--line); border-radius: 999px; padding: 0 var(--s2);
}
.lane-body { display: flex; flex-direction: column; gap: var(--s2); }
.card {
  border: 1px solid var(--line); border-radius: var(--radius); background: var(--bg);
  padding: var(--s3); display: grid; gap: var(--s2);
}
.card-top { display: flex; align-items: center; gap: var(--s2); }
.card-id { font-family: var(--mono); font-size: var(--t-xs); font-weight: 700; color: var(--accent); }
.card-task { font-size: var(--t-md); line-height: 1.35; margin: 0; font-weight: 550; }
.card-meta { display: flex; flex-wrap: wrap; gap: var(--s2); align-items: center; }
.chip {
  font-size: var(--t-xs); font-family: var(--mono); border-radius: 999px;
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
.card-kv { display: grid; grid-template-columns: auto 1fr; gap: 0 var(--s2); font-size: var(--t-xs); }
.card-kv dt { color: var(--ink-faint); font-family: var(--mono); }
.card-kv dd { margin: 0; color: var(--ink-soft); font-family: var(--mono); overflow-wrap: normal; word-break: normal; min-width: 0; }
.empty { font-size: var(--t-xs); color: var(--ink-faint); padding: var(--s2) var(--s1); }
footer { padding: 0 var(--s6) var(--s8); color: var(--ink-faint); font-size: var(--t-xs); font-family: var(--mono); }
.hidden { display: none !important; }
"""

JS = """
(function () {
  var input = document.getElementById("filter");
  if (!input) { return; }
  function apply() {
    var q = input.value.trim().toLowerCase();
    var lanes = document.querySelectorAll(".lane");
    for (var i = 0; i < lanes.length; i++) {
      var lane = lanes[i];
      var cards = lane.querySelectorAll(".card");
      var shown = 0;
      for (var j = 0; j < cards.length; j++) {
        var hit = !q || cards[j].textContent.toLowerCase().indexOf(q) !== -1;
        cards[j].classList.toggle("hidden", !hit);
        if (hit) { shown++; }
      }
      var empty = lane.querySelector(".empty");
      if (empty) { empty.classList.toggle("hidden", shown !== 0); }
    }
  }
  input.addEventListener("input", apply);
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


def render_card(row):
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
    return (
        '<article class="card">'
        '<div class="card-top"><span class="card-id">%s</span></div>'
        '<p class="card-task">%s</p>'
        '<div class="card-meta">'
        '<span class="chip type">%s</span>'
        '<span class="chip prio">%s</span>'
        '%s'
        '</div>'
        '%s'
        '</article>'
    ) % (
        esc(row["ID"]),
        esc(clean_text(row["Task"])),
        esc(clean_text(row["Type"])),
        esc(clean_text(row["Priority"])),
        render_risk(row["Risk"]),
        ("<dl class=\"card-kv\">%s</dl>" % kv) if kv else "",
    )


def render_lane(lane, rows):
    cards = []
    for row in rows:
        if row["Status"] == lane:
            cards.append(render_card(row))
    body = "".join(cards) if cards else '<p class="empty">Nothing in this lane.</p>'
    return (
        '<section class="lane" data-lane="%s">'
        '<div class="lane-head"><h3>%s</h3><span class="count">%d</span></div>'
        '<div class="lane-body">%s</div>'
        '</section>'
    ) % (esc(lane), esc(lane), len(cards), body)


def build_html(rows, lanes, worktrees, generated_at, error, refresh):
    board_counts = {lane: len(lanes.get(lane, [])) for lane in LANES}
    total = len(rows)
    lane_html = "\n".join(render_lane(lane, rows) for lane in LANES)
    wt_html = "".join(render_worktree(wt) for wt in worktrees)
    if not wt_html:
        wt_html = '<p class="empty">No git worktrees found.</p>'
    banner = ""
    if error:
        banner = '<p class="banner">%s</p>' % esc(error)
    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta http-equiv="refresh" content="%d">'
        "<title>Live board</title>"
        "<style>%s</style></head><body>\n"
        "<header>\n"
        "<div><h1>Live board</h1>\n"
        '<p class="sub">Lanes and worktrees, read from the board file on every request.</p></div>\n'
        '<div class="spacer"></div>\n'
        '<div class="meta">generated %s &middot; refresh %ds</div>\n'
        "</header>\n"
        "%s\n"
        '<div class="filter"><label class="meta" for="filter">Filter cards</label>\n'
        '<input id="filter" type="search" placeholder="task, id, branch" autocomplete="off"></div>\n'
        '<section class="panel">\n'
        '<div class="panel-head"><h2>Live worktrees</h2>\n'
        '<span class="meta">%d worktree(s)</span></div>\n'
        '<div class="wt-list">%s</div>\n'
        "</section>\n"
        '<section class="lanes">\n%s\n</section>\n'
        '<footer>%d card(s) on the board &middot; %s</footer>\n'
        "<script>%s</script>\n"
        "</body></html>"
    ) % (
        refresh,
        CSS,
        esc(generated_at),
        refresh,
        banner,
        len(worktrees),
        wt_html,
        lane_html,
        total,
        esc(", ".join("%s %d" % (lane, board_counts[lane]) for lane in LANES)),
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


def build_payloads(board, worktree, path, root):
    def board_payload():
        rows, error = read_rows(board, path)
        lanes = lane_map(rows)
        return {
            "rows": rows,
            "lanes": lanes,
            "counts": {lane: len(lanes.get(lane, [])) for lane in LANES},
            "generated_at": now(),
            "error": error,
        }

    def worktree_payload():
        try:
            return worktree_state(worktree, root)
        except Exception:
            return []

    def html_page():
        try:
            rows, error = read_rows(board, path)
            lanes = lane_map(rows)
            state = worktree_state(worktree, root)
        except Exception as exc:
            rows, lanes, state = [], lane_map([]), []
            error = "could not read the board: %s" % exc
        return build_html(rows, lanes, state, now(), error, Handler.state["refresh"])

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
    path = board_file(args.file, root)

    board_payload, worktree_payload, html_page = build_payloads(board, worktree, path, root)
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
    print("board:   %s" % path)
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
