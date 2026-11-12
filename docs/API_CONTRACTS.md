# Factory board dashboard API

The local dashboard uses Python standard-library HTTP on loopback by default (port 15180).
There is no authentication or write endpoint. Requests are read-only; `HEAD` returns the same
status and headers without a body. Responses are JSON with `Cache-Control: no-store`.

The dashboard is a board/worktree monitor, not an OpenCode session console. It has no session
view, agent-dispatch operation, board-mutation route or separate run-history table. Repository
candidate discovery remains metadata-only and does not authorize repository access.

| Method/path | Success | Notes |
|---|---|---|
| `GET /api/board` | `200 {"boards":[{"label":string,"path":string,"rows":[],"lanes":{},"counts":{},"error":string|null}],"generated_at":ISO-8601}` | Existing board shape retained. Labels are `harness` for the factory control repo, `project` for a project control repo or registered project, and the registered ID for other repos. A registered independent Git repo without a SQLite board stays visible with `rows:[]` and `error:"Board not initialized"`; HTTP GET never imports its Markdown or initializes SQLite. |
| `GET /api/worktrees` | `200 [{"path":string,"branch":string,"sha":string|null,"ahead":number|null,"behind":number|null,"dirty":boolean,"main":boolean,"repo":string,"base":string|null}]` | Existing array and fields retained; includes all valid Git repositories registered by ID. Existing failure behavior is an empty array. |
| `GET /api/repo-candidates` | `200 {"candidates":[{"name":string,"relative_path":string}],"scanned_at":ISO-8601}` | Scans only directory-entry metadata and `.git` marker type at `/projects/<repo>` and `/projects/<group>/<repo>`, using no-follow directory handles. A replaced symlink is skipped, never traversed. Sorted by distinct relative path; excludes registered paths. No contents, board, Git command or initialization for candidates. |

Independent registered boards use existing SQLite only. On an active WAL board, SQLite may
change transient metadata in the existing `-shm` file while reading current data. Dashboard
reads must not create a missing board or sidecar, change the database or WAL contents, alter
board rows, or change tracked Git files. Only the board CLI initializes a missing board.

Candidate scan or registry failures return `503 {"error":"Repository candidates unavailable."}`.
No absolute path or exception detail is returned on candidate failures. Registration is a human
edit to `.opencode/repos.json`, not a dashboard API operation.
