#!/usr/bin/env python3
"""Minimal repo-local quick validator for Codex skill metadata."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ALLOWED_FRONTMATTER_KEYS = {"name", "description"}
NAME_PATTERN = re.compile(r"^[a-z0-9-]{1,63}$")


def parse_frontmatter(text: str, path: Path) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise SystemExit(f"{path}: missing opening YAML frontmatter delimiter")
    try:
        end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        raise SystemExit(f"{path}: missing closing YAML frontmatter delimiter")

    frontmatter: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        if ":" not in line:
            raise SystemExit(f"{path}: unsupported frontmatter line: {line!r}")
        key, value = line.split(":", 1)
        key = key.strip()
        if key not in ALLOWED_FRONTMATTER_KEYS:
            raise SystemExit(f"{path}: unsupported frontmatter key: {key}")
        frontmatter[key] = value.strip().strip("'\"")
    return frontmatter


def validate(skill_dir: Path) -> list[str]:
    failures: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [f"{skill_dir}: missing SKILL.md"]

    text = skill_md.read_text(encoding="utf-8-sig")
    frontmatter = parse_frontmatter(text, skill_md)
    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")

    if not name:
        failures.append("frontmatter missing name")
    elif not NAME_PATTERN.fullmatch(name):
        failures.append(f"name is not lowercase hyphen-case under 64 chars: {name}")
    elif skill_dir.name != name:
        failures.append(f"skill folder name {skill_dir.name!r} does not match frontmatter name {name!r}")

    if not description:
        failures.append("frontmatter missing description")
    elif len(description) > 800:
        failures.append(f"description too long for quick validation: {len(description)} chars")

    if len(text.splitlines()) > 500:
        failures.append("SKILL.md exceeds 500 lines")

    openai_yaml = skill_dir / "agents" / "openai.yaml"
    if openai_yaml.exists() and f"${name}" not in openai_yaml.read_text(encoding="utf-8-sig"):
        failures.append(f"agents/openai.yaml default prompt should mention ${name}")

    return failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_dir", type=Path)
    args = parser.parse_args()

    failures = validate(args.skill_dir)
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        raise SystemExit(1)
    print(f"OK: {args.skill_dir}")


if __name__ == "__main__":
    main()
