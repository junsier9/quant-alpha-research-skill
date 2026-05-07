# Output Templates

Use these templates only when the user needs a decision-grade report. Keep chat answers shorter when the task is small.

## Alpha decision

```text
decision: no-go | watch | blocked | research-only | go
candidate:
parent_or_control:
horizon:
landing_shape:
data_sources:
data_trust:
stage0_evidence:
falsification_status:
promotion_status:
main_blockers:
next_executable_step:
artifacts_checked:
commands_run:
```

Rules:

- Put the decision first.
- Use `go` only if the repo's promotion gate is actually satisfied.
- Use `blocked` when data trust or pipeline state prevents an honest result.
- Use `research-only` for useful mechanisms that should not touch live or canonical state.

## Provider/data decision

```text
decision: alpha_rerun_allowed = true | false
provider:
coverage_status:
concordance_status:
symbols_or_fields_failed:
closed_bar_handling:
provenance_status:
research_unlocked:
research_blocked:
next_data_step:
```

Rules:

- Never treat coverage as concordance.
- List suspicious symbols or fields explicitly.
- Prefer closed-bar-aware comparisons and symbol-level failures.

## External-source conversion

```text
source_claims:
repo_verified_facts:
mechanism:
candidate_landing_shapes:
minimum_data_needed:
stage0_design:
falsification_tests:
promotion_boundary:
```

Rules:

- Keep source claims separate from repo evidence.
- Translate commentary into a testable state variable or selection rule.
- Name the first falsification test before naming a candidate winner.

## Roadmap execution closeout

```text
roadmap_item:
work_done:
artifacts_created_or_checked:
tests_or_runs:
decision:
remaining_blockers:
next_item:
source_repo_write_status:
```

Rules:

- If the task was read-only, `source_repo_write_status` must state that no source-repo writes were made.
- If a roadmap item is blocked, identify the first unblocker instead of broadening the plan.
