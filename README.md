# quant-alpha-research

[![skill-validate](https://github.com/junsier9/quant-alpha-research-skill/actions/workflows/skill-validate.yml/badge.svg)](https://github.com/junsier9/quant-alpha-research-skill/actions)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)

A fail-closed Codex / Claude Code skill for crypto quant alpha research. It
turns "find me an alpha" into a falsifiable Stage 0 contract instead of an
optimistic Sharpe story: repo-native, governance-aware, and unwilling to call a
candidate `promotable` without falsification evidence.

This skill is for the moment when a strategy idea sounds exciting and you want
the agent to slow down, read the evidence, and try to kill the idea before it
starts decorating itself with backtest glow.

> **Who this is for**: quant researchers using Codex or Claude Code on a repo
> with `docs/quant_research/` or `artifacts/quant_research/` style evidence.

## Research Stance

`$quant-alpha-research` turns crypto quant ideas, roadmaps, provider-data
questions, and market commentary into repo-native research work with a hard bias
toward:

- current artifacts over memory
- Stage 0 evidence before optimization
- provider concordance before alpha reruns
- falsification before promotion language
- explicit `go`, `no-go`, `blocked`, `watch`, or `research-only` decisions

It is not an alpha generator, a trading bot, or a promotion shortcut. The core
promise is narrower and more useful: make the research assistant harder to fool.

## What It Changes

Recorded evals compare fresh-agent baseline answers against the same prompts
with `$quant-alpha-research` loaded.

| Prompt | Without the skill | With the skill |
| --- | --- | --- |
| `Provider coverage passed. Can we rerun alpha now?` | "Coverage passed + quality/concordance passed = rerun alpha allowed. Coverage passed but quality/concordance not passed = do not rerun yet." | "Decision: blocked. Provider coverage passing is not enough to rerun alpha. Coverage only says the provider surface is populated; it does not prove the data is trustworthy for research reruns." |

The baseline is friendly and mostly sensible. The skill adds the release-grade
shape: decision label, separate trust gates, Stage 0 state, falsification state,
promotion state, and the next repo-native action.

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

Install directly from GitHub; no marketplace account or delivery is required.
These instructions cover local Codex CLI / IDE and Claude Code installations.
Install the host application separately and have Git and Python 3.10+ available
(`python3` on macOS/Linux; `python` on Windows). The bundled Python scripts use
only the standard library.

### Choose the host and scope

Each location below contains a **whole** `quant-alpha-research` directory:

| Host | Personal (all local projects) | Project (under the target repository root) | Invoke inside the host |
| --- | --- | --- | --- |
| Codex | `~/.agents/skills/quant-alpha-research/` | `.agents/skills/quant-alpha-research/` | `$quant-alpha-research` or `/skills` |
| Claude Code | `~/.claude/skills/quant-alpha-research/` | `.claude/skills/quant-alpha-research/` | `/quant-alpha-research` |

On native Windows, `~` means your user home (`$HOME` in PowerShell, normally
`C:\Users\<user>`). For WSL, run the macOS/Linux commands inside WSL and use
that Linux user's home, rather than the Windows home. Install into the
environment where the host actually runs. These local personal directories do
not install the skill into hosted/cloud sessions.

Codex's current documented personal path is `~/.agents/skills/`; the old
`$CODEX_HOME/skills/` command is not used here. If migrating an existing copy,
back it up outside all skill discovery directories and remove that old copy
after verifying the new installation. Prefer one scope per host to avoid
duplicate names or a personal skill shadowing a project copy.

Official references: [Codex skills](https://developers.openai.com/codex/skills/)
and [Claude Code skills](https://code.claude.com/docs/en/skills).

### macOS / Linux (Bash or Zsh)

**1. Clone once** into a source checkout kept separate from installed skills:

```sh
mkdir -p "$HOME/src"
git clone https://github.com/junsier9/quant-alpha-research-skill.git "$HOME/src/quant-alpha-research-skill"
```

If you already have this checkout, skip cloning and use the update instructions
below. Do not clone the repository root directly into a skill directory: the
manifest is at `skills/quant-alpha-research/SKILL.md`, not the repository root.

**2. Choose exactly one destination assignment**, then run step 3. For a project
installation, first `cd` to the target quant repository root (not this package's
source checkout):

```sh
# Codex: personal
skill_dest="$HOME/.agents/skills/quant-alpha-research"
```

```sh
# Codex: project
skill_dest="$PWD/.agents/skills/quant-alpha-research"
```

```sh
# Claude Code: personal
skill_dest="$HOME/.claude/skills/quant-alpha-research"
```

```sh
# Claude Code: project
skill_dest="$PWD/.claude/skills/quant-alpha-research"
```

**3. Copy and verify the complete package.** This also works for updates; an
existing installation is moved to a unique backup outside discovery paths.
Keep the printed backup path if you need to restore local edits.

```sh
(
  set -eu
  : "${skill_dest:?Run one destination assignment above first}"
  repo_dir="$HOME/src/quant-alpha-research-skill"
  test -f "$repo_dir/skills/quant-alpha-research/SKILL.md"
  test -f "$repo_dir/LICENSE"
  mkdir -p "$(dirname "$skill_dest")"
  if [ -e "$skill_dest" ] || [ -L "$skill_dest" ]; then
    mkdir -p "$HOME/skill-backups"
    backup_dir=$(mktemp -d "$HOME/skill-backups/quant-alpha-research.XXXXXX")
    mv "$skill_dest" "$backup_dir/quant-alpha-research"
    printf 'Previous installation: %s\n' "$backup_dir/quant-alpha-research"
  fi
  cp -R "$repo_dir/skills/quant-alpha-research" "$skill_dest"
  cp "$repo_dir/LICENSE" "$skill_dest/LICENSE"
  test -f "$skill_dest/agents/openai.yaml"
  test -f "$skill_dest/references/patterns.md"
  test -f "$skill_dest/scripts/score_eval_cases.py"
  python3 "$repo_dir/scripts/quick_validate.py" "$skill_dest"
  python3 "$skill_dest/scripts/validate_skill_package.py"
)
```

To install for the other host too, choose its destination and repeat step 3.
`cp -R` copies the entire skill directory, including its dotfiles; copying only
`SKILL.md` would omit required references and bundled tools.

### Windows (PowerShell)

**1. Clone once** (skip this if the checkout already exists):

```powershell
New-Item -ItemType Directory -Force -Path (Join-Path $HOME 'src') | Out-Null
git clone https://github.com/junsier9/quant-alpha-research-skill.git (Join-Path $HOME 'src/quant-alpha-research-skill')
if ($LASTEXITCODE -ne 0) { throw 'Clone failed; stop before installing.' }
```

**2. Choose exactly one destination assignment.** For project scope, first
`Set-Location` to the target quant repository root:

```powershell
# Codex: personal
$skillDest = Join-Path $HOME '.agents/skills/quant-alpha-research'
```

```powershell
# Codex: project
$skillDest = Join-Path (Get-Location).Path '.agents/skills/quant-alpha-research'
```

```powershell
# Claude Code: personal
$skillDest = Join-Path $HOME '.claude/skills/quant-alpha-research'
```

```powershell
# Claude Code: project
$skillDest = Join-Path (Get-Location).Path '.claude/skills/quant-alpha-research'
```

**3. Copy and verify the complete package**, including hidden files. Existing
installations are backed up outside skill discovery paths before replacement:

```powershell
& {
    $ErrorActionPreference = 'Stop'
    if (-not $skillDest) { throw 'Choose a destination above first.' }
    $repoDir = Join-Path $HOME 'src/quant-alpha-research-skill'
    $skillSource = Join-Path $repoDir 'skills/quant-alpha-research'
    if (-not (Test-Path -LiteralPath (Join-Path $skillSource 'SKILL.md') -PathType Leaf)) { throw 'Skill source is missing.' }
    if (-not (Test-Path -LiteralPath (Join-Path $repoDir 'LICENSE') -PathType Leaf)) { throw 'LICENSE is missing.' }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $skillDest) | Out-Null
    if (Test-Path -LiteralPath $skillDest) {
        $backupDir = Join-Path $HOME ('skill-backups/' + [guid]::NewGuid().ToString())
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
        Move-Item -LiteralPath $skillDest -Destination $backupDir
        Write-Output "Previous installation: $backupDir/quant-alpha-research"
    }
    Copy-Item -LiteralPath $skillSource -Destination $skillDest -Recurse -Force
    Copy-Item -LiteralPath (Join-Path $repoDir 'LICENSE') -Destination (Join-Path $skillDest 'LICENSE') -Force
    foreach ($relative in @('agents/openai.yaml', 'references/patterns.md', 'scripts/score_eval_cases.py')) {
        if (-not (Test-Path -LiteralPath (Join-Path $skillDest $relative) -PathType Leaf)) { throw "Missing: $relative" }
    }
    python (Join-Path $repoDir 'scripts/quick_validate.py') $skillDest
    if ($LASTEXITCODE -ne 0) { throw 'Metadata validation failed.' }
    python (Join-Path $skillDest 'scripts/validate_skill_package.py')
    if ($LASTEXITCODE -ne 0) { throw 'Package validation failed.' }
}
```

To install for the other host too, choose its destination and repeat step 3.

### Confirm discovery and use

The commands above validate the files on disk; they do not prove that your host
has loaded the skill. Open the target research repository in the host:

- **Codex:** run `/skills` and look for `quant-alpha-research`, then invoke
  `$quant-alpha-research`. Codex detects changes automatically; restart it if
  the skill or update does not appear.
- **Claude Code:** check the `/` menu or ask `What skills are available?`, then
  invoke `/quant-alpha-research`. Current versions watch skill directories;
  run `/reload-skills` if the top-level skills directory was created after the
  session started, or restart the session if needed.

For example, ask the host to use the skill to assess whether provider coverage
alone permits an alpha rerun. Check that it loads this installed `SKILL.md` and
can read `references/patterns.md`; a `blocked` research result can be correct
when your research repository lacks evidence. The `agents/openai.yaml` file
provides Codex metadata; Claude Code uses the same `SKILL.md` and supporting
files without needing that metadata.

### Update an installed copy

First update the separate GitHub source checkout. Stop if Git fails; do not
overwrite local changes or install a stale checkout after a failed pull.

macOS / Linux:

```sh
git -C "$HOME/src/quant-alpha-research-skill" pull --ff-only origin main
```

Windows PowerShell:

```powershell
git -C (Join-Path $HOME 'src/quant-alpha-research-skill') pull --ff-only origin main
if ($LASTEXITCODE -ne 0) { throw 'Update failed; stop before reinstalling.' }
```

After a successful pull, reselect the same destination in step 2 and rerun
step 3 for each installed host/scope, then repeat the discovery check. Pulling
the source checkout alone does **not** update copied installations. Replacement
from a fresh directory avoids stale deleted files and accidental nested
`quant-alpha-research/quant-alpha-research` directories. Local installed edits
remain in the printed backup; reapply only the edits you still need. Keep
backups outside `.agents/skills/` and `.claude/skills/`.

### GitHub license

The version distributed from this GitHub repository is licensed under
**Apache-2.0**; see [LICENSE](LICENSE) for its permissions, conditions, and
disclaimers. The commands above preserve the license in each installed copy.
Keep applicable license and attribution notices when redistributing. Direct
GitHub installation does not require an Agensi listing or account.


## Use It

In Codex, use `$quant-alpha-research` as shown below. In Claude Code, use
`/quant-alpha-research` followed by the same request.

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

## Limits And Known Gaps

- Recorded release coverage is currently 3 must-trigger prompts, not the full
  trigger matrix.
- The public recorded evals are generic-repo tests; a second independent quant
  repo forward-test is still future work.
- The scorer still supports illustrative fixtures, but only when they are
  explicitly marked `hand_authored` and run with `--allow-illustrative`.
- The skill cannot enforce read-only behavior by itself; it gives Codex a
  contract and validators, but runtime discipline still matters.

Chinese search terms: 量化研究, 加密货币, alpha 研究, Codex skill, Claude Code skill.

## Public Boundary

Before publishing, verify that no API keys, private artifact dumps, raw backtest
outputs, machine-local paths, private project names, or personal identifiers are
present outside ignored local state. This package is meant to ship reusable
research discipline, not private research residue.
