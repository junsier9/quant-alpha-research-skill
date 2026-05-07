# Quant Alpha Research Skill

Fail-closed crypto quant alpha research for Codex.

This skill is for the moment when a strategy idea sounds exciting and you want
the agent to slow down, read the evidence, and try to kill the idea before it
starts decorating itself with Sharpe ratios.

It helps Codex turn crypto quant ideas, roadmaps, provider-data questions, and
market commentary into repo-native research work with a hard bias toward:

- current artifacts over memory
- Stage 0 evidence before optimization
- provider concordance before alpha reruns
- falsification before promotion language
- explicit `go`, `no-go`, `blocked`, `watch`, or `research-only` decisions

It is not an alpha generator, a trading bot, or a promotion shortcut. The core
promise is narrower and more useful: make the research assistant harder to fool.

## What It Does

Use `$quant-alpha-research` when Codex needs to:

- find or validate a crypto alpha candidate against the current parent
- execute a quant research roadmap instead of summarizing it
- convert market articles or threads into testable repo-native hypotheses
- separate provider coverage from provider trust/concordance
- design Stage 0 or Stage 0.5 falsification checks
- audit whether a candidate is blocked, research-only, or promotable

The skill lives at:

```text
skills/quant-alpha-research/
```

## What It Refuses

The skill intentionally pushes back when the evidence is not there:

- no "coverage passed, so rerun alpha"
- no "Sharpe improved, so alpha exists"
- no "Stage 0 passed, so it is promotable"
- no hidden live-trading or manifest changes
- no private project profiles bundled into the public package
- no hand-authored evals presented as release evidence

If the repo lacks current artifacts, the correct answer is usually `blocked`
until Codex reads the relevant roadmap, parent definition, candidate report,
provider-trust status, and falsification output.

## Package Contents

```text
skills/quant-alpha-research/
  SKILL.md
  agents/openai.yaml
  references/
    output_templates.md
    patterns.md
    stage0_and_falsification.md
  scripts/
    score_eval_cases.py
    validate_skill_package.py
```

Repo-level files provide release hygiene:

- `recorded_eval_cases.json`: recorded fresh-agent release gate
- `sample_eval_cases.json`: illustrative smoke cases only
- `scripts/quick_validate.py`: repo-local metadata validator
- `.github/workflows/skill-validate.yml`: CI validation
- `dev_docs/eval_design.md`: eval design notes outside the skill folder

## Install

Copy the skill directory into a Codex-discoverable skills path:

```powershell
Copy-Item -Recurse .\skills\quant-alpha-research "$env:CODEX_HOME\skills\quant-alpha-research"
```

```sh
cp -R ./skills/quant-alpha-research "$CODEX_HOME/skills/quant-alpha-research"
```

The bundled scripts require Python and use only the standard library.

## Use It

Example prompts:

```text
Use $quant-alpha-research to find a new alpha and validate it against the current canonical parent.
```

```text
Use $quant-alpha-research to read this roadmap and execute the next Stage 0 slice.
```

```text
Use $quant-alpha-research to decide whether provider coverage is enough to rerun alpha.
```

For a target quant repo, the validator can run a read-only evidence probe:

```powershell
python .\skills\quant-alpha-research\scripts\validate_skill_package.py --evidence-root <path-to-quant-repo>
```

```sh
python ./skills/quant-alpha-research/scripts/validate_skill_package.py --evidence-root <path-to-quant-repo>
```

Project-specific required documents should live in local profile JSON outside
the public repo, or in an ignored profile directory:

```powershell
python .\skills\quant-alpha-research\scripts\validate_skill_package.py --evidence-root <path-to-quant-repo> --profile-dir <path-to-local-profiles> --evidence-profile <profile-name>
```

```sh
python ./skills/quant-alpha-research/scripts/validate_skill_package.py --evidence-root <path-to-quant-repo> --profile-dir <path-to-local-profiles> --evidence-profile <profile-name>
```

## Validate

Windows:

```powershell
python .\scripts\quick_validate.py .\skills\quant-alpha-research
python .\skills\quant-alpha-research\scripts\validate_skill_package.py
python .\skills\quant-alpha-research\scripts\score_eval_cases.py .\recorded_eval_cases.json
python .\skills\quant-alpha-research\scripts\score_eval_cases.py .\sample_eval_cases.json --allow-illustrative
```

Unix:

```sh
python ./scripts/quick_validate.py ./skills/quant-alpha-research
python ./skills/quant-alpha-research/scripts/validate_skill_package.py
python ./skills/quant-alpha-research/scripts/score_eval_cases.py ./recorded_eval_cases.json
python ./skills/quant-alpha-research/scripts/score_eval_cases.py ./sample_eval_cases.json --allow-illustrative
```

`recorded_eval_cases.json` is the release gate and must pass without
`--allow-illustrative`. `sample_eval_cases.json` is smoke coverage and
intentionally requires `--allow-illustrative`.

To scan the full package repo rather than only the installed skill directory:

```powershell
python .\skills\quant-alpha-research\scripts\validate_skill_package.py --repo-root .
```

```sh
python ./skills/quant-alpha-research/scripts/validate_skill_package.py --repo-root .
```

For release-grade secret scanning, install `gitleaks` and run:

```powershell
python .\skills\quant-alpha-research\scripts\validate_skill_package.py --require-external-secret-scan
```

```sh
python ./skills/quant-alpha-research/scripts/validate_skill_package.py --require-external-secret-scan
```

## Release Bar

CI enforces:

- skill metadata validation
- Python syntax checks
- package validation with external secret scanning
- recorded transcript scoring without `--allow-illustrative`
- illustrative smoke scoring with explicit warnings

The release gate is designed to make inflated eval scores harder to sneak in:
hand-authored transcripts must be labeled `hand_authored`, and the scorer
refuses them unless `--allow-illustrative` is passed.

## Public Boundary

Before publishing, verify that no API keys, private artifact dumps, raw backtest
outputs, machine-local paths, private project names, or personal identifiers are
present outside ignored local state. This package is meant to ship reusable
research discipline, not private research residue.
