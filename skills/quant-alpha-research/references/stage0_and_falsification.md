# Stage 0 And Falsification Contract

Use this reference when designing or reviewing an alpha validation slice.

## Stage 0 report fields

Include these fields whenever possible:

- `research_id`
- `question`
- `mechanism`
- `parent_or_control`
- `horizon`
- `landing_shape`
- `data_sources_and_coverage`
- `provider_trust_status`
- `feature_definitions`
- `event_count_by_symbol`
- `event_count_by_liquidity_bucket`
- `changed_rows_or_timestamps`
- `forward_return_table`
- `strategy_interaction`
- `funding_drag_summary`
- `cost_or_slippage_proxy`
- `capacity_proxy`
- `shuffle_tests`
- `symbol_holdout`
- `liquidity_bucket_consistency`
- `delay_robustness`
- `pass_fail_decision`
- `next_landing_shape`

If a field is not applicable, state why. If it is missing because the repo lacks data, mark the result `blocked` or `watch`, not `passed`.

## Minimum pass logic

Require all of the following before moving from Stage 0 to a stronger test:

- enough events or changed rows for at least two symbols and preferably two liquidity buckets
- directionally correct edge at the natural horizon
- comparison against the current parent/control
- no single symbol or period dominates the result
- costs, funding, or slippage do not reverse the conclusion
- data provenance is known and point-in-time safe
- newest incomplete bars are excluded or audited

## Falsification matrix

Run the relevant subset:

- Delay: +1 bar/day, plus natural execution delays for the horizon.
- Time shuffle: state timestamps are shifted or permuted.
- Label shuffle: forward returns are randomized.
- Same-timestamp feature shuffle: cross-sectional labels are permuted inside timestamp.
- Symbol holdout: remove each high-contribution symbol.
- Liquidity bucket consistency: require directionally consistent effect across executable buckets.
- Cost/funding stress: double costs or apply conservative funding/slippage assumptions.
- Capacity stress: enforce participation and OI limits.
- Provider sensitivity: rerun without suspect provider rows or compare against a trusted baseline.
- Tail-bar audit: remove newest incomplete bars and live-tail windows.

If any key falsification test reproduces or beats the observed edge, fail closed.

## Promotion blockers

Do not call a candidate promotable when:

- it has only Stage 0 evidence
- it improves pairwise metrics but fails shuffle or holdout checks
- it is driven by one symbol, one liquidity bucket, or one short period
- provider concordance is unresolved
- it has no cost/funding/capacity stress
- the parent comparator is stale
- it changes a manifest or live boundary without a repo-native promotion gate

## Anti-patterns

- "Coverage passed, so data is trustworthy."
- "Sharpe improved, so alpha exists."
- "The mechanism makes sense, so it deserves a manifest A/B."
- "The candidate passed validation, so it passed falsification."
- "A sidecar horizon can inherit another horizon's promotion status."
- "External commentary is evidence without repo validation."

Use these phrases as warning signs and correct them in the report.
