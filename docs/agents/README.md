# Flight Logbook Autonomous Agent Team

This directory defines three execution agents — Architect, Feature Scaffolder, and Coder — plus a PM intake guide. The PM (project manager, human) is the top tier. Agents do not run autonomously above the Architect.

## Role Summary

| Tier | Who | What they do |
| --- | --- | --- |
| 1 | PM (you) | Approve features, direct row selection, unblock blocked rows |
| 2 | Architect | Receive PM brief, plan one row, produce decision-complete handoff |
| 3 | Feature Scaffolder | Receive Architect handoff, scaffold structure, plant TODOs |
| 4 | Coder | Receive Feature handoff, close TODOs, run proofs |

## PM Intake

When you have a new feature: fill out `docs/changes/change-proposal-template.md` and persist it as `docs/changes/proposals/<change-id>/proposal.md`. Record it in `docs/changes/approved-change-register.md` when approved. Hand the proposal to the Architect.

When you want parity ledger work to continue: give the Architect a short directive — "next row" or a named `slice_id`.

When you want a single planning conversation followed by an autonomous pass to completion: use the PM Assistant first to clear any known `blocked on contract` rows in scope. The Architect should receive only an autonomy-ready scope.

See [agent-discussion.md](agent-discussion.md) for the full PM intake guide.

## Execution Path

1. the active role start prompt under `docs/agents/`
2. the active role doc under `docs/agents/`
3. the active role template when producing or validating a handoff or batch report
4. the PM brief or approved proposal
5. `docs/migration/parity-status-ledger.md`
6. the slice folder under `docs/migration/handoffs/<slice-id>/` when it exists
7. the exact source-of-truth artifact and current-stack files for the row

Start prompts:

- Architect: [architect-start-prompt.md](architect-start-prompt.md)
- Feature Scaffolder: [feature-start-prompt.md](feature-start-prompt.md)
- Coder: [coder-start-prompt.md](coder-start-prompt.md)

Fixed templates:

- [../changes/change-proposal-template.md](../changes/change-proposal-template.md)
- [architect-handoff-template.md](architect-handoff-template.md)
- [feature-scaffold-handoff-template.md](feature-scaffold-handoff-template.md)
- [coder-batch-report-template.md](coder-batch-report-template.md)

The change-intake docs are authoritative for:

- discussion outcomes
- approval state
- contract deltas
- rowization gates
- the rule that discussion does not mutate execution state

The shared execution protocol is authoritative for:

- automatic handoff behavior after a change is approved and rowized
- authority boundaries
- escalation triggers
- verification policy
- completion states
- dirty-tree handling

## Roles

**[PM Intake Guide](agent-discussion.md)** — human tier, not an agent
   - The PM structures new feature requests using `docs/changes/change-proposal-template.md` or gives a short row directive for parity work.
   - No agent runs here. The PM produces the input that goes to the Architect.

**[Architect](agent-architect.md)** — senior developer
   - Receives the PM brief, selects or confirms one ledger row, plans the exact contract boundary and proof strategy from a narrow evidence budget.
   - Launch: [architect-start-prompt.md](architect-start-prompt.md)
   - Output: [architect-handoff-template.md](architect-handoff-template.md) stored in the slice folder
   - Hands off to: Feature Scaffolder

**[Feature Scaffolder](agent-feature.md)** — junior developer
   - Receives the Architect handoff, makes the minimum structural preparation, and seeds `TODO (Codex)[slice_id]:` comments next to implementation points.
   - Launch: [feature-start-prompt.md](feature-start-prompt.md)
   - Output: [feature-scaffold-handoff-template.md](feature-scaffold-handoff-template.md) stored in the slice folder
   - Hands off to: Coder

**[Coder](agent-coder.md)** — implementer
   - Receives the Feature handoff, closes one TODO batch at a time, proves the work with the smallest relevant checks, removes completed TODOs.
   - Launch: [coder-start-prompt.md](coder-start-prompt.md)
   - Output: [coder-batch-report-template.md](coder-batch-report-template.md) stored in the slice folder
   - Hands off to: next Coder batch, or back to Architect/Feature if blocked

## Automatic Handoff Rules

- PM to Architect: PM delivers an approved proposal or a row directive. Execution begins only after the Architect rowizes the work into exact ledger rows.
- Architect to Feature: only when the stored handoff matches `architect-handoff-template.md`, covers exactly one concrete surface, and names the exact legacy source, target code areas, acceptance criteria, fixture strategy, environment choice, and escalation risks.
- Feature to Coder: only when the stored scaffold matches `feature-scaffold-handoff-template.md`, structural preparation is complete, and the active TODO batch exists directly in `apps/`.
- Coder to next owner: only when the current TODO batch is closed with a protocol completion state or blocked by a named escalation trigger, and the stored report matches `coder-batch-report-template.md`.

Additional handoff rule:

- PM Assistant to Architect for run-to-completion: only after known contract blockers in scope have explicit `## Contract Resolution` notes and the scope is autonomy-ready under `docs/migration/repo-completion-protocol.md`.

## Validation And Rejection Rules

- Architect must reject freeform feature descriptions that have not been structured as an approved proposal.
- Feature must reject any Architect handoff that does not match `architect-handoff-template.md` or that covers more than one concrete surface.
- Coder must reject any Architect handoff that does not match `architect-handoff-template.md` or that covers more than one concrete surface.
- Coder must reject any Feature handoff that does not match `feature-scaffold-handoff-template.md`.
- No role may infer missing structure from chat, memory, stale prompts, or scanner output when a required upstream artifact is invalid.

## General Team Directives

- Keep feature-discussion and contract-change artifacts under `docs/changes/`.
- Keep the live implementation backlog in inline `TODO (Codex):` comments under `apps/`.
- Keep the canonical repo state in `docs/migration/parity-status-ledger.md`.
- Keep the canonical slice artifacts in `docs/migration/handoffs/<slice-id>/`.
- On Windows, prefer `powershell -ExecutionPolicy Bypass -File .\scripts\find-codex-todos.ps1` when scanning the current code-adjacent backlog.
- Do not trust TODO names from prior runs; always ground live state first.
- Persist decisions in repo markdown, change proposals, the change register, and slice artifacts rather than relying on chat history.
- If repo-wide autonomous completion is the goal, clear known `blocked on contract` rows before starting the Architect pass.
- Extend fixtures and parity tests when the slice changes observable behavior.
- The Architect is the most constrained execution role. Broad repo exploration and multi-slice planning are anti-patterns there.
- Feature and Coder are template-driven roles. If an upstream handoff is invalid, reject it instead of trying to repair it implicitly.
