# Active risks

- **BOARD-130 is Blocked.** Task-local QA artifacts were approved but the change did not pass its
  three-round review cap. The base branch still carries old review paths. Do not start tasks that
  require task-local browser/reviewer evidence unless the user revises the stop decision.
- **Concurrency is not enforced yet.** The user approved two builders total and one per repository.
  Keep execution within that limit manually until BOARD-133 passes race-safe tests.
- **No factory-tooling builder is available yet.** The architect's current permissions allow only
  six product/QA/docs specialists. BOARD-143 must add the approved `factory-dev` role after exact
  rule/config wording is approved.
- **Project path rules need alignment.** The approved model places project repositories under
  `/projects/<project-id>`, while some current rule/template text describes a local `project/`
  folder or app-only repositories. BOARD-134 must show exact permanent-rule edits and wait for A9
  approval.
- **Board state is clone-local.** Losing the clone can lose its SQLite board. BOARD-139 will rehearse
  a safe backup and restore before relying on a recovery procedure.
- **The factory handover is stale and contains conflict markers.**
  `docs/HANDOVER.md:736-745` needs a focused reconciliation after BOARD-130's evidence-path status
  is settled; do not resolve its conflicting artifact guidance by assumption.
- **The current product scale is local and single-user.** No throughput target or multi-user service
  has been approved. Avoid cloud infrastructure and distributed coordination.

Deferred: code graph engine until core task, repository, concurrency and QA flows are proven.
