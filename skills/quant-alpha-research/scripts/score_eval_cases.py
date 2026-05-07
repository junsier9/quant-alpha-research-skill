#!/usr/bin/env python3
"""Score transcript-based eval cases for the quant-alpha-research skill."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import mean
from typing import Any


LEGACY_SELF_SCORE_FIELDS = {"triggered", "baseline_score", "skill_score"}
TRANSCRIPT_PROVENANCE_VALUES = {"hand_authored", "recorded_run"}


def load_cases(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, list):
        raise SystemExit("Eval file must contain a JSON list of case objects.")
    return data


def as_bool(value: object, field: str, case_id: str) -> bool:
    if not isinstance(value, bool):
        raise SystemExit(f"{case_id}: {field} must be boolean.")
    return value


def as_text(value: object, field: str, case_id: str, *, required: bool = True) -> str:
    if value is None and not required:
        return ""
    if not isinstance(value, str):
        raise SystemExit(f"{case_id}: {field} must be a string.")
    if required and not value.strip():
        raise SystemExit(f"{case_id}: {field} must not be empty.")
    return value


def as_str_list(value: object, field: str, case_id: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SystemExit(f"{case_id}: {field} must be a list of strings.")
    return value


def as_run(case: dict[str, Any], key: str, case_id: str) -> dict[str, Any]:
    run = case.get(key)
    if not isinstance(run, dict):
        raise SystemExit(f"{case_id}: {key} must be an object.")
    return run


def as_checks(case: dict[str, Any], case_id: str) -> dict[str, list[str]]:
    checks = case.get("checks")
    if not isinstance(checks, dict):
        raise SystemExit(f"{case_id}: checks must be an object.")
    return {
        "skill_must_contain": as_str_list(
            checks.get("skill_must_contain"), "checks.skill_must_contain", case_id
        ),
        "skill_must_not_contain": as_str_list(
            checks.get("skill_must_not_contain"), "checks.skill_must_not_contain", case_id
        ),
    }


def as_provenance(case: dict[str, Any], case_id: str) -> str:
    value = as_text(case.get("transcript_provenance"), "transcript_provenance", case_id)
    if value not in TRANSCRIPT_PROVENANCE_VALUES:
        raise SystemExit(
            f"{case_id}: transcript_provenance must be one of: "
            + ", ".join(sorted(TRANSCRIPT_PROVENANCE_VALUES))
        )
    return value


def contains_all(output: str, terms: list[str]) -> tuple[list[str], list[str]]:
    output_lower = output.lower()
    matched = [term for term in terms if term.lower() in output_lower]
    missing = [term for term in terms if term.lower() not in output_lower]
    return matched, missing


def forbidden_found(output: str, terms: list[str]) -> list[str]:
    output_lower = output.lower()
    return [term for term in terms if term.lower() in output_lower]


def score_text(output: str, must_contain: list[str], must_not_contain: list[str]) -> dict[str, Any]:
    matched, missing = contains_all(output, must_contain)
    forbidden = forbidden_found(output, must_not_contain)
    if must_contain:
        score = 10.0 * (len(matched) / len(must_contain))
    else:
        score = 10.0
    score = max(0.0, score - (2.5 * len(forbidden)))
    return {
        "score": round(score, 3),
        "matched": matched,
        "missing": missing,
        "forbidden_found": forbidden,
    }


def files_changed(run: dict[str, Any], key: str, case_id: str) -> list[str]:
    return as_str_list(run.get("files_changed"), f"{key}.files_changed", case_id)


def status_unchanged(run: dict[str, Any], key: str, case_id: str) -> bool:
    before = as_text(
        run.get("source_repo_status_before", ""), f"{key}.source_repo_status_before", case_id, required=False
    )
    after = as_text(
        run.get("source_repo_status_after", ""), f"{key}.source_repo_status_after", case_id, required=False
    )
    return before == after


def summarize(
    cases: list[dict[str, Any]],
    min_score: float,
    min_average: float,
    min_delta: float,
    *,
    allow_illustrative: bool,
) -> dict:
    if not cases:
        raise SystemExit("Eval file contains no cases.")

    scored = []
    failures = []
    warnings = []
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            raise SystemExit(f"case-{index}: case must be an object.")
        legacy = sorted(LEGACY_SELF_SCORE_FIELDS.intersection(case))
        if legacy:
            raise SystemExit(
                f"{case.get('case_id') or f'case-{index}'}: legacy self-scored fields are not allowed: "
                + ", ".join(legacy)
            )

        case_id = str(case.get("case_id") or f"case-{index}")
        provenance = as_provenance(case, case_id)
        if provenance == "hand_authored":
            warnings.append(f"{case_id}: illustrative hand-authored transcript; not release evidence")
            if not allow_illustrative:
                failures.append(f"{case_id}: hand_authored transcript requires --allow-illustrative")
        prompt = as_text(case.get("prompt"), "prompt", case_id)
        must_trigger = as_bool(case.get("must_trigger"), "must_trigger", case_id)
        read_only = bool(case.get("read_only", False))
        baseline = as_run(case, "baseline", case_id)
        skill = as_run(case, "skill", case_id)
        checks = as_checks(case, case_id)

        baseline_output = as_text(baseline.get("output"), "baseline.output", case_id)
        skill_invoked = as_bool(skill.get("invoked"), "skill.invoked", case_id)
        skill_output = as_text(skill.get("output"), "skill.output", case_id, required=must_trigger)
        as_str_list(baseline.get("commands_run"), "baseline.commands_run", case_id)
        as_str_list(skill.get("commands_run"), "skill.commands_run", case_id)

        baseline_score = score_text(
            baseline_output,
            checks["skill_must_contain"],
            checks["skill_must_not_contain"],
        )
        if must_trigger:
            skill_score = score_text(
                skill_output,
                checks["skill_must_contain"],
                checks["skill_must_not_contain"],
            )
            if not skill_invoked:
                skill_score["score"] = 0.0
                failures.append(f"{case_id}: expected skill invocation did not happen")
        else:
            skill_score = {
                "score": 10.0 if not skill_invoked and not files_changed(skill, "skill", case_id) else 0.0,
                "matched": [],
                "missing": [],
                "forbidden_found": [],
            }
            if skill_invoked:
                failures.append(f"{case_id}: unexpected skill invocation")

        if read_only:
            for run_key, run in [("baseline", baseline), ("skill", skill)]:
                changed = files_changed(run, run_key, case_id)
                if changed:
                    failures.append(f"{case_id}: {run_key} changed files during read-only eval: {changed}")
                if not status_unchanged(run, run_key, case_id):
                    failures.append(f"{case_id}: {run_key} source repo status changed during read-only eval")

        if must_trigger and skill_score["score"] < min_score:
            failures.append(f"{case_id}: skill_score {skill_score['score']:g} < {min_score:g}")

        scored.append(
            {
                "case_id": case_id,
                "transcript_provenance": provenance,
                "prompt": prompt,
                "must_trigger": must_trigger,
                "read_only": read_only,
                "skill_invoked": skill_invoked,
                "baseline_score": baseline_score["score"],
                "skill_score": skill_score["score"],
                "delta": round(skill_score["score"] - baseline_score["score"], 3),
                "skill_missing": skill_score["missing"],
                "skill_forbidden_found": skill_score["forbidden_found"],
            }
        )

    must_scores = [item["skill_score"] for item in scored if item["must_trigger"]]
    avg_must = mean(must_scores) if must_scores else None
    if avg_must is not None and avg_must < min_average:
        failures.append(f"must-trigger average {avg_must:g} < {min_average:g}")

    deltas = [item["delta"] for item in scored]
    avg_delta = mean(deltas) if deltas else None
    if avg_delta is not None and avg_delta < min_delta:
        failures.append(f"average delta {avg_delta:g} < {min_delta:g}")

    return {
        "case_count": len(scored),
        "must_trigger_count": len(must_scores),
        "average_must_trigger_score": avg_must,
        "average_delta_vs_baseline": avg_delta,
        "passed": not failures,
        "failures": failures,
        "warnings": warnings,
        "cases": scored,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("eval_json", type=Path)
    parser.add_argument("--min-score", type=float, default=7.0)
    parser.add_argument("--min-average", type=float, default=7.5)
    parser.add_argument("--min-delta", type=float, default=1.0)
    parser.add_argument(
        "--allow-illustrative",
        action="store_true",
        help="Allow hand-authored illustrative transcripts to pass scorer smoke tests.",
    )
    args = parser.parse_args()

    summary = summarize(
        load_cases(args.eval_json),
        args.min_score,
        args.min_average,
        args.min_delta,
        allow_illustrative=args.allow_illustrative,
    )
    for warning in summary["warnings"]:
        print(f"WARN: {warning}", file=sys.stderr)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if not summary["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
