# Autonomous Execution Protocol

This document is the authoritative operating system for the execution triad in the Flight Logbook migration workspace: Architect, Feature Scaffolder, and Coder.

The Discussion role does not inherit the scanner-ledger execution loop in this document. Discussion work is governed by `docs/changes/change-intake-protocol.md` until a change is explicitly approved and rowized into exact ledger rows.

Known `blocked on contract` rows are upstream planning work before a run-to-completion pass begins. The triad is designed to execute decision-complete rows, not to absorb repo-level contract cleanup that was already visible before the run started.

## Mission

Advance approved, rowized parity slices mostly autonomously while preserving strict role separation, minimal diff scope, persisted handoffs, and truthful reporting.

In this repo, "perfect code" means:

- contract-accurate behavior
- the smallest change set that closes the current row
- parity-oriented tests or fixtures that prove the change
- no silent scope expansion
- honest completion reporting when full verification is blocked
- ledger and slice-artifact state that stays consistent with the actual work

The Architect is the least free role in this system. Planning quality comes from narrower evidence, smaller slice size, and earlier escalation, not from broader synthesis.

## Mandatory Read Order

1. `docs/migration/repo-completion-protocol.md`
2. `docs/migration/parity-status-ledger.md`
3. `docs/migration/contract-inventory.md`
4. `docs/migration/execution-playbook.md`
5. `docs/infrastructure/local-dev.md`
6. this protocol
7. the active role start prompt when launching a fresh session
8. the active role document
9. `docs/agents/architect-handoff-template.md` when the Architect is active or when validating an Architect handoff
10. `docs/agents/feature-scaffold-handoff-template.md` when the Feature Scaffolder is active or when validating a Feature handoff
11. `docs/agents/coder-batch-report-template.md` when the Coder is active or when validating a Coder report
12. the slice folder under `docs/migration/handoffs/<slice-id>/` when the ledger row already has one
13. the source-of-truth artifact, current scanner output, and current git status

## Default Execution Loop

1. Ground live state.
   Run `git status --short` and `powershell -ExecutionPolicy Bypass -File .\scripts\find-codex-todos.ps1`. If the scanner fails or returns malformed output, fall back to the raw `rg` search documented in `docs/migration/contract-inventory.md`. Do not trust TODO names, slice names, or workspace assumptions from earlier runs.
2. Read the repo-completion docs.
   Use `repo-completion-protocol.md` to confirm whether there is an approved unrowized change before normal row selection and, when a run-to-completion handoff is expected, whether the scope is autonomy-ready. Use `parity-status-ledger.md` only after the work is already rowized.
3. Architect phase.
   Define exactly one concrete source of truth, slice boundary, acceptance criteria, fixture strategy, environment choice, and escalation risks using the fixed Architect handoff template and store it in the slice folder.
4. Feature Scaffolder phase.
   Make only the structural adjustments required to let the Coder work cleanly, then hand off with the fixed Feature scaffold template and precise inline `TODO (Codex):` comments next to the target code.
5. Coder phase.
   Close one TODO batch at a time, remove completed TODOs, run the smallest proving checks that can truthfully validate the batch, and report the result with the fixed Coder batch report template.
6. Re-scan and advance the ledger.
   Run the scanner again. Update the slice folder and the ledger row. If more TODOs remain in the same row, the Coder continues. If the row needs new planning or backlog reseeding, hand back to Architect or Feature. If an escalation trigger fires, stop and report the matching blocked state.

## Authority Boundaries

| Role | Owns | Must not do |
| --- | --- | --- |
| Architect | selecting the next incomplete ledger row, rowizing approved changes, contract boundary, acceptance criteria, fixture strategy, environment choice, risk log, template-based planning docs, contract-inventory changes that belong to an explicitly approved change | implement runtime logic, seed code TODOs in place of the Feature role, silently leave ambiguity unresolved, broaden the evidence search beyond the approved budget |
| Feature Scaffolder | minimal structural preparation, empty or placeholder scaffolding when needed, code-adjacent `TODO (Codex):` items, template-based scaffold handoff, migration-doc alignment, row-state advancement from `architected` to `scaffolded` | implement business logic, close parity gaps through real runtime behavior, expand the row without Architect guidance, infer missing upstream structure |
| Coder | runtime code, tests, fixtures, API-client changes, TODO removal, template-based batch reporting, parity-doc updates for delivered scope except contract-inventory changes, row-state advancement through verification | redefine slice scope, mutate `contract-inventory.md` outside an explicitly approved change path, skip live scanner checks, overclaim verification, overwrite unrelated dirty-tree edits, infer missing upstream structure |

## Architect Hardening Rules

The Architect follows stricter rules than the other roles.

### One-Surface Rule

- The Architect may plan exactly one `WebService.cs` method, one MVC action flow, one telemetry parser, one import or export flow, one domain behavior, one media behavior, one background or worker flow, or one rowized approved feature surface per handoff.
- Domain batches, multi-slice roadmaps, and freeform cluster planning are invalid Architect outputs in the handoff path.

### Approved Evidence Budget

The Architect may rely on:

1. `docs/migration/repo-completion-protocol.md`
2. `docs/migration/parity-status-ledger.md`
3. `docs/migration/contract-inventory.md`
4. `docs/migration/execution-playbook.md`
5. `docs/infrastructure/local-dev.md`
6. current scanner output from `powershell -ExecutionPolicy Bypass -File .\scripts\find-codex-todos.ps1`
7. current `git status --short`
8. the exact source-of-truth artifact for the selected row
9. at most two directly relevant current-stack files needed to identify insertion points

If clarity is still missing after this evidence budget is exhausted, the Architect must escalate instead of widening the search.

### Claim Discipline

- Every behavioral claim in an Architect handoff must be anchored to one of the approved evidence items.
- If a claim cannot be anchored to approved evidence, it must be written as an ambiguity or escalation risk, not as fact.
- Claims framed as "likely", "probably", or similar language are invalid unless they explicitly name the ambiguity and the blocking evidence gap.

### Mandatory Output Shape

- Every Architect handoff must match `docs/agents/architect-handoff-template.md`.
- If a required section is missing, the handoff is invalid.
- If the handoff covers more than one concrete surface, the handoff is invalid.

## Feature And Coder Hardening Rules

### Template-Driven Execution

- Every Feature handoff must match `docs/agents/feature-scaffold-handoff-template.md`.
- Every Coder batch report must match `docs/agents/coder-batch-report-template.md`.
- Fresh Feature sessions must start from `docs/agents/feature-start-prompt.md`.
- Fresh Coder sessions must start from `docs/agents/coder-start-prompt.md`.

### Upstream Validation

- Feature must validate the Architect handoff and the ledger row before preparing structure or writing TODOs.
- Coder must validate both the Architect handoff and the Feature handoff before implementing a TODO batch.
- Downstream roles must reject invalid upstream artifacts instead of inferring missing structure from chat, stale prompts, adjacent code, or scanner output alone.

### Feature Handoff Validity

A Feature handoff is invalid if any of these are true:

- a required template section is missing
- the handoff does not identify the exact target files
- TODOs are not written directly next to target code
- a TODO omits action, scope limit, or proof target
- the handoff includes business logic instead of structural preparation

### Coder Report Validity

A Coder batch report is invalid if any of these are true:

- a required template section is missing
- commands or checks run are not listed exactly
- the completion state is missing or does not match the shared vocabulary
- TODO closure is claimed without matching proof or TODO-state evidence

## Downstream Rejection Rule

- Feature and Coder must treat an Architect handoff as invalid if it fails the fixed template or one-surface rule.
- Coder must treat a Feature handoff as invalid if it fails the fixed scaffold template.
- No downstream role may patch over missing structure by guessing what the previous role probably meant.

## Required Pre-Action Checks

Before any role acts on a row:

- inspect the ledger row in `docs/migration/parity-status-ledger.md`
- inspect the slice folder under `docs/migration/handoffs/<slice-id>/` when it exists
- inspect the exact source-of-truth artifact being replaced or implemented
- inspect current new-stack targets in `apps/`
- run `git status --short`
- run `powershell -ExecutionPolicy Bypass -File .\scripts\find-codex-todos.ps1`
- if the scanner fails, run the raw `rg` fallback documented in `docs/migration/contract-inventory.md`
- choose the environment using `docs/infrastructure/local-dev.md`

Additional rules:

- Use the Windows fast path when the row is docs, API, client, or web work that does not need Redis-backed behavior.
- Use the full container/parity path when the row touches `apps/worker`, Redis-backed jobs, or end-to-end async parity.
- Treat the row as backend-only unless a real `apps/web` replacement flow is required.
- Treat the row as worker-backed only when the behavior is truly async, retryable, or storage-heavy.

## Dirty-Tree Policy

- Preserve unrelated edits.
- Integrate around in-flight changes when the touched files do not conflict materially with the current row.
- If another worker has overlapping edits in the exact write scope and safe integration is not obvious, stop and report `blocked on conflicting workspace state`.
- Never solve dirty-tree uncertainty by resetting or discarding files.

## TODO Lifecycle

- The live code backlog is the inline `TODO (Codex):` set under `apps/`.
- The Feature Scaffolder writes TODOs directly next to the implementation points they target.
- The Coder removes completed TODOs immediately after closing the matching batch.
- If the scanner is empty but the ledger still has incomplete rows, route back to the ledger and select the next row instead of treating the repo as complete.
- If the scanner is empty but the current row still exposes an obvious gap, the Architect and Feature Scaffolder must seed the next TODO batch instead of treating the row as done.
- Hidden backlog in chat is not authoritative.

Preferred TODO shape:

`TODO (Codex)[<slice_id>]: <exact action>, <scope limit>, <proof target>`

The `[<slice_id>]` tag is mandatory. It must match the `slice_id` of the ledger row that owns the work. This lets the scanner attribute every open TODO to its row without reading the surrounding code.

## Blocked Row Resolution

When a row reaches `blocked on contract`, the Architect writes the exact ambiguity into the slice artifact (`architect.md`) under the `Escalation Risks` section and stops. The row stays `blocked on contract` with owner `Architect`.

Resolution path:

1. A Discussion session reads the blocked slice artifact to extract the exact ambiguity — not the full row, just the named blocking question.
2. Discussion works with the human to produce a contract decision. The decision must be explicit and persisted as a resolution note appended to the slice `architect.md` under a `## Contract Resolution` section.
3. If the resolution changes the observable contract, it must also be persisted in `docs/changes/approved-change-register.md` before the Architect re-enters.
4. The Architect re-enters with the resolution note as additional approved evidence, re-architects the row from `blocked on contract` back to `architecting`, and produces a valid handoff.
5. The ledger row status updates from `blocked on contract` to `architected` once the handoff is valid.

Rules:

- Discussion must not invent a resolution; the human must explicitly state the intended behavior.
- The Architect must not re-enter until the resolution note exists in the slice artifact.
- A known blocked row is not a valid starting point for a run-to-completion pass until Discussion has already persisted the resolution note.
- If the resolution note changes more than one row, the Architect must rowize each affected row separately before re-entering any of them.

## Escalation Triggers

Stop autonomous progression and report a blocked state when any of these are true:

- **Contract ambiguity:** multiple plausible legacy behaviors exist and the exact intended output cannot be determined from source, fixtures, or prior repo evidence.
- **Architect evidence exhaustion:** the Architect has exhausted the approved evidence budget and still cannot identify one exact source of truth, one exact surface boundary, or one justified proof path.
- **Environment gap:** the required service, dependency, credential, or local runtime is missing and no smaller truthful proving check exists.
- **Conflicting workspace state:** another worker's dirty-tree edits overlap the same write scope and safe integration is not obvious.
- **Verification ambiguity:** a relevant check fails in the touched scope and the agent cannot determine whether the regression belongs to the current batch or a pre-existing problem.
- **Scope conflict:** the user prompt, contract inventory, ledger row, and live code imply materially different slices.

## Completion States

Every batch or slice handoff must use exactly one of these states.

| State | Meaning | Required evidence |
| --- | --- | --- |
| `verified complete` | The batch or row is implemented and locally proven. | Relevant TODOs removed, smallest relevant checks run and passed, parity docs updated if needed, next gap identified if work remains. |
| `implemented pending verification` | The code is implemented, but the full proving step could not be run locally. | Relevant TODOs removed or narrowed, executed checks listed, exact missing checks listed, blocking reason recorded, next required verification step recorded. |
| `blocked on environment` | Progress or proof is halted by missing services, tools, credentials, or runtime prerequisites. | Attempted command or check recorded, missing dependency identified, smallest remaining verification step named. |
| `blocked on contract` | The exact legacy behavior is too ambiguous to implement safely. | Exact source of ambiguity recorded, candidate interpretations listed, proof gap identified. |
| `blocked on conflicting workspace state` | Safe progress is halted by overlapping in-flight edits or unresolved same-scope failures. | Conflicting files or checks listed, why safe integration is not obvious, next human or role decision needed. |

Rules:

- No role may call work complete without matching the evidence for `verified complete`.
- Best-effort completion is allowed only as `implemented pending verification`.
- `implemented pending verification` must never hide the missing proof step.
- Architect outputs that exhaust the approved evidence budget without clarity must resolve to `blocked on contract`, not to broader search.
- A run-to-completion pass is invalid if known contract blockers were left unresolved before the pass started.
- The repo is complete only when every ledger row reaches `verified complete`.

## Verification Policy

- Run the smallest check that can truthfully validate the current batch.
- Favor parity-oriented tests, fixtures, and targeted route or service checks over broad untargeted runs.
- If no adequate proving check exists for the touched behavior, add the smallest new test or fixture that does.
- Use the existing repo mechanisms when possible:
  - `apps/api/tests/test_legacy_mobile_compat.py`
  - `apps/api/tests/test_telemetry_registry.py`
  - `apps/api/tests/fixtures/`
  - `npm run test --workspace @myflightbook/web`
  - `.\apps\api\.venv\Scripts\python.exe -m pytest`
- Truthful reporting is mandatory. Unrun checks, blocked environments, and partial proof must be stated explicitly.

## Slice Closeout Checklist

Before handing off or reporting a row:

1. current completion state is named explicitly
2. commands and checks run are listed exactly
3. missing checks or blockers are listed exactly
4. completed TODOs were removed
5. the slice artifact in `docs/migration/handoffs/<slice-id>/` was updated
6. the ledger row status, owner, and blocker or note field were updated
7. `contract-inventory.md` or other migration docs were updated if observable scope changed
8. the next owner or next row is clear without guesswork
