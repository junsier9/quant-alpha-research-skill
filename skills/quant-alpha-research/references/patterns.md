# Crypto Quant Repo Patterns

Use this reference when working inside a crypto quant research repo with `docs/quant_research` and `artifacts/quant_research` style evidence. Verify current docs before relying on any example below; candidate names and parent status drift quickly.

## Current-source rule

Read current artifacts before deciding. In a typical repo, start from the most
recent files matching these roles rather than hard-coded filenames:

- stage map or next-research-mainline document
- data utilization or provider roadmap
- factor audit trail or promotion history
- candidate-specific Stage 0 reports under `docs/quant_research/`
- current reports under `artifacts/quant_research/`
- promotion/falsification scripts and their latest output

Do not anchor on stale "active" labels without checking the latest roadmap and promotion guard.

## Durable lessons

- Compare candidates to the current canonical parent or control for the same horizon, not legacy winners.
- Treat data fill and research revalidation as separate layers.
- Treat provider coverage and provider concordance as separate gates.
- A full backfill is not proof that a provider is trustworthy.
- Sparse event/state information often belongs in selection-layer rules, not smooth global score overlays.
- Good landing shapes include boundary activation, short veto, delayed entry, replacement, sleeve activation, and capacity haircut.
- Positive Stage 0 evidence opens a falsification queue; it is not promotion evidence.
- Pairwise uplift, attractive Sharpe, or IC alone is not enough without out-of-sample and falsification support.
- If strict concordance or data provenance fails, stop fail-closed instead of rescuing the result with assumptions.
- A new horizon can use old-horizon lessons as mechanism inspiration, but must not inherit or mutate promotion state without an explicit bridge.

## Research lane archetypes

Use these as patterns, not as proof:

- **Canonical-parent challenger**: compare directly against the current parent with fixed-set evidence and falsification.
- **Sparse boundary activation**: use rare state variables to change selection, not to perturb a global score.
- **Provider unlock**: first prove coverage, then prove concordance, then rerun alpha.
- **Parallel horizon lane**: keep a 1h or intraday lane research-only until it earns its own evidence card.
- **External mechanism note**: translate an article into repo-native hypotheses before coding.

## Read-only validation mode

When the user prohibits source-repo modification:

1. Run `git status --short` and `git status --short --ignored` before reading.
2. Snapshot the specific docs, artifacts, or reports you will inspect by path, size, and mtime.
3. Read docs and artifacts with targeted commands.
4. Write no files under the source repo, including ignored files, cache dirs, generated reports, or helper logs.
5. Put temporary eval inputs only under the skill repo or an OS temp directory, and delete them when they are no longer needed.
6. Finish with the same git-status checks and path snapshot. Treat any source-root change as a blocker until explained.

## Agent proposal lane

When working on an agent-proposal pipeline:

- Keep selector/compiler stages distinct.
- Require JSON-only responses when the repo contract requires them.
- Enforce request-body budgets deterministically.
- Do not let proposal generation run backtests, mutate manifests, or bypass governance.
- Treat the proposal lane as idea generation; deterministic evaluation owns promotion.

## External-source conversion

When a market article, X thread, or outside claim is introduced:

1. Record source claims separately from repo-verified facts.
2. Translate claims into mechanisms and data requirements.
3. Pick the smallest Stage 0 slice.
4. Specify what would falsify the idea.
5. Do not write promotion language until repo evidence exists.

## Reporting style

Use hard decision labels:

- `no-go`: evidence failed or is insufficient.
- `watch`: mechanism is plausible but evidence is incomplete or sparse.
- `blocked`: data, provider, or pipeline trust is not yet adequate.
- `research-only`: useful for future hypotheses but not tradable/promotable.
- `go`: only after the repo's explicit gates pass.

If the honest answer is "no credible alpha yet", say that and name the next best rejection test.
