# Eval Design

Use this developer note when improving or forward-testing `quant-alpha-research`.
Do not copy it into the skill folder; it is release/process material, not task
knowledge for downstream Codex agents.

## Industrial Skill Checklist

- Keep the skill `description` focused on realistic user triggers and negative boundaries.
- Keep `SKILL.md` as the entry point, with detailed methods in `references/`.
- Keep deterministic repeated checks in `scripts/`.
- Validate trigger behavior, side-effect boundaries, and answer quality on realistic prompts.
- Prefer recorded fresh-run transcripts over hand-authored examples.

## Trigger Eval Prompts

These should trigger the skill:

- "Find a new alpha and validate it against the current parent."
- "Read this quant roadmap and execute the next Stage 0 slice."
- "Is this candidate promotable or should we fail it closed?"
- "Turn this market article into repo-native alpha hypotheses."
- "Provider coverage passed. Can we rerun alpha now?"
- "Rank the next quant research mainline from current docs."
- "Design Stage 0.5 falsification for this positive Stage 0 result."
- "The run looks stuck. Is it still progressing normally?"

These should not trigger the skill unless extra quant context is present:

- "Summarize this general finance article."
- "Make a simple chart from this CSV."
- "Explain what alpha means in investing."
- "Create a GitHub PR for unrelated frontend changes."

## Transcript Provenance

Every eval case must declare one of:

- `recorded_run`: output captured from an actual fresh agent or baseline run.
- `hand_authored`: illustrative fixture only; useful for scorer smoke tests, not
  release evidence.

`scripts/score_eval_cases.py` refuses `hand_authored` cases unless
`--allow-illustrative` is passed. Release evidence should use `recorded_run`
transcripts and should preserve the raw prompt, output, commands, and source-repo
write status.

## Quality Rubric

Score each test from observed baseline and skill transcripts, not manually supplied grades:

- 0-2: misses the task or gives unsafe promotion claims.
- 3-4: discusses the idea but lacks repo-native evidence or falsification.
- 5-6: usable, but misses one important blocker or artifact field.
- 7-8: good fail-closed workflow with clear current-source checks.
- 9-10: produces a concrete, minimal, testable slice and a decision-grade report.

Minimum release bar:

- every must-trigger recorded case scores at least 7
- average must-trigger recorded score is at least 7.5
- average recorded skill delta versus baseline is at least 1 point
- no non-trigger case invokes the skill
- no read-only case changes source-repo status or lists changed files
- CI must score `recorded_eval_cases.json` without `--allow-illustrative`; keep
  `sample_eval_cases.json --allow-illustrative` as smoke-only coverage.

## Suggested Eval JSON

Use `scripts/score_eval_cases.py` with JSON shaped like:

```json
[
  {
    "case_id": "new-alpha",
    "transcript_provenance": "recorded_run",
    "prompt": "Find a new alpha and validate it against the current parent.",
    "must_trigger": true,
    "read_only": true,
    "checks": {
      "skill_must_contain": ["canonical parent", "Stage 0", "falsification"],
      "skill_must_not_contain": ["promotable"]
    },
    "baseline": {
      "output": "Actual baseline transcript text.",
      "commands_run": [],
      "files_changed": [],
      "source_repo_status_before": "",
      "source_repo_status_after": ""
    },
    "skill": {
      "invoked": true,
      "output": "Actual transcript after invoking $quant-alpha-research.",
      "commands_run": ["git status --short"],
      "files_changed": [],
      "source_repo_status_before": "",
      "source_repo_status_after": ""
    }
  }
]
```

The scorer rejects legacy self-certified fields such as `triggered`,
`baseline_score`, and `skill_score`.
