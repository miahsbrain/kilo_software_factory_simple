# Factory Rebuild Checklist — 2026-11-23

Comprehensive quality-of-life improvements and agent overhaul.

## Core Philosophy
- Agents do stellar work following best practices
- Human-readable code is mandatory
- Comments only for "why", never for "what"
- Components and abstractions must have clear purpose
- The factory helps, never fights

## Implementation Checklist

### 1. Frontend Agent Overhaul ✓ / ✗
- [ ] Strengthen component library enforcement (shadcn/ui default)
- [ ] Add explicit design system requirements
  - [ ] Spacing scale enforcement (4/8/12/16/24/32/48)
  - [ ] Typography hierarchy rules
  - [ ] Color system enforcement
  - [ ] Consistent border radius
- [ ] Add pre-flight component reuse check
- [ ] Self-verification against design standards before completion
- [ ] Explicit responsive behavior requirements
- [ ] Accessibility as mandatory (not optional)
- [ ] Remove vague "good design" language, add concrete rules

### 2. Backend Agent Overhaul ✓ / ✗
- [ ] Functional core / imperative shell enforcement
- [ ] Explicit dependency injection patterns
- [ ] No hidden state, no global mutations
- [ ] Pure functions return values, never mutate inputs
- [ ] Effects at boundaries only (HTTP, DB, filesystem, time)
- [ ] Error handling patterns (Result types, explicit errors)
- [ ] API contract validation
- [ ] Security patterns (input validation, sanitization)
- [ ] Performance awareness (N+1 queries, caching)

### 3. All Agent Code Quality Standards ✓ / ✗
- [ ] Update frontend-dev.md with code quality rules
- [ ] Update backend-dev.md with code quality rules
- [ ] Update mobile-dev.md with code quality rules
- [ ] Update qa-reviewer.md with verification standards
- [ ] Update ui-critic.md with critique standards
- [ ] Update docs-writer.md with documentation standards
- [ ] Update merge-conflict-resolver.md
- [ ] Add to AGENTS.md root agreement:
  - [ ] Human-readable code is mandatory
  - [ ] Comments only explain "why", never "what"
  - [ ] Clear naming over clever code
  - [ ] Small, focused functions/modules
  - [ ] No premature abstraction
  - [ ] Reuse requires genuine shared behavior

### 4. QA Authentication System ✓ / ✗
- [ ] Create `.kilo/local/` directory structure
- [ ] Add `qa-auth.json` schema documentation
- [ ] Update `.gitignore` to exclude `.kilo/local/`
- [ ] Modify `env.py` to handle auth config
- [ ] Update `browser-review.mjs` to auto-load credentials
- [ ] Add auth config to worktree provisioning
- [ ] Document in QA skill
- [ ] Add example template file
- [ ] Test with real login flow

### 5. Board State Intelligence ✓ / ✗
- [ ] Analyze current board.py state transitions
- [ ] Add "user-approved" state detection
- [ ] Fix agents to respect manual approvals
- [ ] Stop auto-blocking when evidence exists
- [ ] Add explicit approval markers agents can read
- [ ] Update board.py with new state logic
- [ ] Update all agent instructions about board states
- [ ] Document new state handling

### 6. Flexible Worktree Mode ✓ / ✗
- [ ] Design "adaptive" mode logic:
  - [ ] Required: Feature rows
  - [ ] Optional: Fix/Chore/Docs rows
- [ ] Add `--skip-worktree` flag to worktree.py
- [ ] Update mode command with "adaptive" option
- [ ] Modify permission generation for adaptive mode
- [ ] Update all agent instructions about when worktrees matter
- [ ] Add clear error messages for mode violations
- [ ] Document new mode in git-worktree skill
- [ ] Test all three modes (required/optional/adaptive)

### 7. Workflow Streamlining ✓ / ✗
- [ ] Review all skills for redundant steps
- [ ] Simplify overly complex procedures
- [ ] Improve error messages in all scripts
- [ ] Clearer handoff instructions
- [ ] Remove unnecessary approval gates
- [ ] Consolidate related checks
- [ ] Update documentation for clarity

### 8. Documentation Updates ✓ / ✗
- [ ] Update README.md with new features
- [ ] Update AGENTS.md with code quality standards
- [ ] Update all agent markdown files
- [ ] Update git-worktree SKILL.md
- [ ] Update qa-review SKILL.md
- [ ] Update docs/UI-UX.md
- [ ] Add new ADRs for major changes
- [ ] Update CHANGELOG.md

### 9. Testing & Verification ✓ / ✗
- [ ] Run all existing tests (bootstrap, lifecycle, env)
- [ ] Test frontend agent with real component library
- [ ] Test backend agent with real API code
- [ ] Test QA with auth config
- [ ] Test adaptive worktree mode
- [ ] Test board state transitions
- [ ] Verify no regressions in existing functionality
- [ ] Test full workflow end-to-end

### 10. Template Synchronization ✓ / ✗
- [ ] Update templates/project/.gitignore
- [ ] Update templates/project/AGENTS.md
- [ ] Add templates/project/.kilo/local/ structure
- [ ] Ensure bootstrap copies new structure
- [ ] Test fresh project bootstrap
- [ ] Verify restore works with new structure

## Success Criteria

### Frontend Must
- ✓ Agent uses shadcn/ui by default
- ✓ Design system enforced (spacing, type, color)
- ✓ Components built before screens
- ✓ No generic dashboard templates
- ✓ Responsive and accessible by default

### Backend Must
- ✓ Functional core with explicit effects
- ✓ No hidden state or global mutations
- ✓ Clear error handling
- ✓ Security patterns enforced
- ✓ API contracts validated

### Code Quality Must
- ✓ All code is human-readable
- ✓ Comments only for "why"
- ✓ Clear names over clever code
- ✓ Small focused units
- ✓ Genuine reuse only

### QA Must
- ✓ Auth config loads automatically
- ✓ No manual login per test
- ✓ Config stays ignored/secret

### Board Must
- ✓ Respects manual approvals
- ✓ No incorrect blocked states
- ✓ Clear state transitions

### Worktree Must
- ✓ Adaptive mode works
- ✓ Quick edits possible for non-features
- ✓ Clear when worktrees required

## Rollback Plan
If any change breaks existing functionality:
1. Git revert the specific commit
2. Document the issue
3. Fix and re-test before re-applying
4. Keep working changes, only revert broken ones

## Notes
- Maintain backward compatibility where possible
- Test incrementally after each major change
- Keep existing projects working (they're independent)
- Document all breaking changes
