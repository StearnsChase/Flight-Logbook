# Coder Batch Report Template

> Canonical location: `docs/agents/templates/coder-report.md`
> Also referenced as: `docs/agents/coder-batch-report-template.md`

Use this exact structure for every Coder batch report. If any section is missing, if commands or checks are not listed exactly, or if the reported completion state does not match the evidence, the report is invalid.

## Required Structure

### Slice

- one-line name for the exact concrete surface being advanced

### TODO Batch Closed

- exact TODO or TODOs closed in this batch
- state whether each TODO was removed, narrowed, or left in place with a reason

### Files Touched

- exact file paths changed in this batch
- brief reason each file changed

### Source Of Truth Rechecked

- exact source-of-truth artifact re-read for this batch
- exact method, action, parser, or behavior rechecked

### Tests And Fixtures Updated

- exact tests, fixtures, or proof artifacts added or updated
- state `none` if no test or fixture change was needed and explain why

### Commands And Checks Run

- list every command or check run exactly
- include failed or blocked commands that matter to the completion state

### Completion State

Use exactly one:

- `verified complete`
- `implemented pending verification`
- `blocked on environment`
- `blocked on contract`
- `blocked on conflicting workspace state`

### Missing Proof Or Blockers

- exact missing proof, failing prerequisite, or ambiguity still open
- next required verification step when the state is `implemented pending verification`
- state `none` only when the completion state is fully supported

### Docs Updated

- migration or agent docs updated because observable scope changed
- state `none` if no docs changed

### Next Live Backlog State

- summary of the scanner result after the batch
- whether the next owner is Coder, Feature Scaffolder, Architect, or human escalation
