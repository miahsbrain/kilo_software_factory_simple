# The live board becomes a factory console

The board viewer showed cards in a vertical accordion. It answered "what is in a lane" but not
"what shape is the flow, what is blocked, and what does this row actually need". A row's Notes
acceptance checklist was raw markdown, and filtering meant reading every lane.

The console keeps the same read-only, server-rendered, offline contract and the same JSON
endpoints. It adds:

- an app bar with the refresh clock, pause and manual refresh;
- an active-lane pipeline that doubles as the status filter;
- a toolbar with search (`/`), type and priority filters, and URL state;
- cards whose Notes checklist is parsed into checked/open items with proof lines;
- a worktrees table with branch copy;
- `j`/`k`/`Enter`/`Esc` navigation, system/light/dark theme and comfortable/compact density.

The change also fixes a Python precedence bug in `render_pipeline()`: the `%` tuple was applied
to the result of `parts.append(...)` rather than to the button string, so building `GET /` raised
`TypeError` and returned an empty reply even though the health and JSON endpoints worked.
