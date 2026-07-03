# Coder Batch Report Template

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
- state `not needed` only if the active handoff already captured the exact behavior and no ambiguity arose during coding

### Tests And Fixtures Updated

- exact tests, fixtures, or proof artifacts added or updated
- state `none` if no test or fixture change was needed and explain why in the next section if proof was still required

### Commands And Checks Run

- list every command or check run exactly
- include failed or blocked commands that matter to the completion state

### Completion State

- one of the shared protocol states:
  `verified complete`
  `implemented pending verification`
  `blocked on environment`
  `blocked on contract`
  `blocked on conflicting workspace state`

### Missing Proof Or Blockers

- exact missing proof, failing prerequisite, or ambiguity still open
- next required verification step when the state is `implemented pending verification`
- state `none` only when the completion state is fully supported

### Docs Updated

- migration or agent docs updated because observable scope changed
- state `none` if no docs changed

### Next Live Backlog State

- summary of the scanner result after the batch
- whether the next owner is the Coder again, the Feature Scaffolder, the Architect, or a human escalation path

## Example Skeleton

```md
## Slice
- Legacy mobile auth bootstrap response

## TODO Batch Closed
- removed `TODO (Codex): implement ...`

## Files Touched
- `apps/api/src/...`: implemented compat response
- `apps/api/tests/...`: added parity coverage

## Source Of Truth Rechecked
- `MyFlightbook.Web/AppCode/WebService.cs`
- Method: `SomeExactMethod`

## Tests And Fixtures Updated
- `apps/api/tests/test_legacy_mobile_compat.py`

## Commands And Checks Run
- `.\apps\api\.venv\Scripts\python.exe -m pytest apps/api/tests/test_legacy_mobile_compat.py`

## Completion State
- `verified complete`

## Missing Proof Or Blockers
- none

## Docs Updated
- none

## Next Live Backlog State
- scanner still shows one TODO in `apps/api/src/...`
- next owner: Coder
```
