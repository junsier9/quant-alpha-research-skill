#!/usr/bin/env python3
"""Validate the quant-alpha-research skill package and optional evidence repo."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import re
import shutil
import subprocess
from pathlib import Path
from typing import Iterable


SCRIPT_PATH = Path(__file__).resolve()
SKILL_DIR = SCRIPT_PATH.parents[1]
DEFAULT_SCAN_ROOT = SKILL_DIR
MAX_SCAN_BYTES = 5_000_000
MAX_EVIDENCE_DOCS = 16
COMMON_EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "node_modules",
    "artifacts",
    "reports",
    "dist",
    "build",
}

SECRET_PATTERNS = {
    "private_windows_user_path": re.compile(r"\b[A-Z]:[\\/]+Users[\\/]+[^\\/\s\"']+", re.IGNORECASE),
    "private_unix_user_path": re.compile(r"(?<!\w)/(?:Users|home)/[A-Za-z0-9._-]+(?:/[^\s\"']*)?", re.IGNORECASE),
    "email_address": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "openai_api_key": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    "github_token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b|\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
    "aws_access_key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "private_key_block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "secret_assignment": re.compile(
        r"(?im)^\s*(?:export\s+)?[A-Z0-9_]*(?:API[_-]?KEY|TOKEN|SECRET|PASSWORD|PRIVATE[_-]?KEY|ACCESS[_-]?KEY)[A-Z0-9_]*\s*[:=]\s*['\"]?[^'\"\s#]{12,}"
    ),
}
TOKEN_CANDIDATE = re.compile(r"(?<![A-Za-z0-9_/+=-])[A-Za-z0-9_/+=-]{32,}(?![A-Za-z0-9_/+=-])")
CHINESE_TRIGGER_MARKERS = {
    "find_new_alpha": ("寻找新alpha",),
    "validate_this_alpha": ("验证这个alpha",),
    "execute_quant_roadmap": ("执行量化研究路线图",),
}

EVIDENCE_PROFILES = {
    "generic": [],
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def rel(path: Path, root: Path = DEFAULT_SCAN_ROOT) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def load_evidence_profiles(profile_dir: Path | None = None) -> dict[str, list[str]]:
    profiles = {name: list(docs) for name, docs in EVIDENCE_PROFILES.items()}
    candidate_dirs = []
    if profile_dir is not None:
        candidate_dirs.append(profile_dir)
    local_profile_dir = SKILL_DIR / "profiles"
    if local_profile_dir.exists():
        candidate_dirs.append(local_profile_dir)

    for directory in candidate_dirs:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.json")):
            data = json.loads(read_text(path))
            name = str(data.get("name") or path.stem).strip()
            docs = data.get("required_docs", data.get("docs", []))
            if not name:
                raise SystemExit(f"profile {path} missing name")
            if not isinstance(docs, list) or not all(isinstance(item, str) for item in docs):
                raise SystemExit(f"profile {path} must define required_docs as a list of strings")
            profiles[name] = docs
    return profiles


def parse_skill_description(skill_md_text: str) -> str:
    # Project convention: a single-line YAML description, preferably double-quoted.
    # This supports raw UTF-8 and YAML-style \uXXXX escapes. Block scalars are not
    # supported; switch to a YAML parser if the frontmatter grows beyond this shape.
    lines = skill_md_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    try:
        end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        return ""

    for line in lines[1:end]:
        if not line.startswith("description:"):
            continue
        raw = line.split(":", 1)[1].strip()
        if not raw:
            return ""
        if raw[0] in {"'", '"'} and raw[-1:] == raw[0]:
            try:
                parsed = ast.literal_eval(raw)
            except (SyntaxError, ValueError):
                return raw.strip("'\"")
            return parsed if isinstance(parsed, str) else str(parsed)
        return raw
    return ""


def load_excluded_dirs(scan_root: Path) -> set[str]:
    excluded = set(COMMON_EXCLUDED_DIRS)
    gitignore = scan_root / ".gitignore"
    if not gitignore.exists():
        return excluded
    for line in read_text(gitignore).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("!"):
            continue
        if not stripped.endswith("/"):
            continue
        clean = stripped.rstrip("/")
        if clean and "/" not in clean and not re.search(r"[*?\[\]]", clean):
            excluded.add(clean)
    return excluded


def should_scan_file(path: Path, scan_root: Path, excluded_dirs: set[str]) -> bool:
    try:
        parts = path.relative_to(scan_root).parts
    except ValueError:
        return False
    if any(part in excluded_dirs for part in parts[:-1]):
        return False
    return path.suffix != ".pyc"


def load_allowed_secret_patterns(extra_patterns: list[str]) -> list[re.Pattern[str]]:
    expressions: list[str] = []
    ignore_file = SKILL_DIR / ".skillignore-secrets"
    if ignore_file.exists():
        expressions.extend(
            line.strip()
            for line in read_text(ignore_file).splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    expressions.extend(extra_patterns)
    return [re.compile(expression) for expression in expressions]


def line_at(content: str, position: int) -> str:
    line_start = content.rfind("\n", 0, position) + 1
    line_end = content.find("\n", position)
    if line_end == -1:
        line_end = len(content)
    return content[line_start:line_end]


def is_allowed_secret_match(
    path: Path,
    content: str,
    position: int,
    pattern_name: str,
    scan_root: Path,
    allowed_patterns: list[re.Pattern[str]],
) -> bool:
    if not allowed_patterns:
        return False
    payload = f"{rel(path, scan_root)}:{pattern_name}:{line_at(content, position)}"
    return any(pattern.search(payload) for pattern in allowed_patterns)


def redact_path(path: Path, verbose: bool) -> str:
    resolved = path.resolve()
    if verbose:
        return str(resolved)
    return f"<redacted:{resolved.name}>"


def scan_text(path: Path, scan_root: Path) -> tuple[str | None, str | None]:
    try:
        data = path.read_bytes()
    except OSError as exc:
        return None, f"could not read {rel(path, scan_root)}: {exc}"
    if len(data) > MAX_SCAN_BYTES:
        return None, f"skipped oversized file {rel(path, scan_root)}"
    if b"\x00" in data[:4096]:
        return None, None
    return data.decode("utf-8-sig", errors="replace"), None


def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = {char: value.count(char) for char in set(value)}
    total = len(value)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def high_entropy_tokens(text: str) -> list[str]:
    matches = []
    for token in TOKEN_CANDIDATE.findall(text):
        if "/" in token or "\\" in token:
            continue
        if len(set(token)) < 12:
            continue
        if shannon_entropy(token) >= 4.4:
            matches.append(token[:8] + "...redacted")
    return matches


def is_detector_definition(path: Path, content: str, position: int) -> bool:
    if path.resolve() != SCRIPT_PATH:
        return False
    line = line_at(content, position)
    if "allowed_secret_patterns" in line or "load_allowed_secret_patterns" in line:
        return True
    return "re.compile" in line or line.strip().startswith("r\"") or line.strip().startswith("r'")


def run_external_secret_scan(required: bool, scan_root: Path) -> tuple[list[str], dict]:
    failures: list[str] = []
    details = {"requested": required, "scanner": None, "available": False, "passed": None}
    gitleaks = shutil.which("gitleaks")
    if not gitleaks:
        if required:
            failures.append("required external secret scanner not found: gitleaks")
        return failures, details

    details["scanner"] = "gitleaks"
    details["available"] = True
    result = subprocess.run(
        [gitleaks, "detect", "--no-git", "--source", str(scan_root), "--redact", "--exit-code", "1"],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    details["passed"] = result.returncode == 0
    if result.returncode != 0:
        failures.append("gitleaks detected potential secrets")
        details["stderr_tail"] = result.stderr[-1000:]
        details["stdout_tail"] = result.stdout[-1000:]
    return failures, details


def git_status(path: Path, *, ignored: bool = False) -> str | None:
    command = ["git", "status", "--short"]
    if ignored:
        command.append("--ignored")
    try:
        result = subprocess.run(
            command,
            cwd=path,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout


def summarize_git_status(status: str | None) -> dict:
    if status is None:
        return {"available": False}
    lines = [line for line in status.splitlines() if line.strip()]
    counts: dict[str, int] = {}
    for line in lines:
        code = line[:2].strip() or "tracked"
        counts[code] = counts.get(code, 0) + 1
    digest = hashlib.sha256(status.encode("utf-8")).hexdigest() if status else None
    return {"available": True, "line_count": len(lines), "counts": counts, "digest": digest}


def path_state(paths: Iterable[Path], *, verbose: bool) -> dict[str, dict[str, int | str | bool]]:
    state: dict[str, dict[str, int | str | bool]] = {}
    for path in paths:
        key = redact_path(path, verbose)
        try:
            stat = path.stat()
        except OSError:
            state[key] = {"exists": False}
            continue
        state[key] = {"exists": True, "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
    return state


def select_evidence_docs(
    root: Path,
    profile: str,
    requested_docs: list[str],
    profiles: dict[str, list[str]],
) -> tuple[list[Path], list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    docs_root = root / "docs" / "quant_research"
    if not docs_root.exists():
        if not (root / "artifacts" / "quant_research").exists():
            failures.append("evidence root lacks docs/quant_research and artifacts/quant_research")
        return [], failures, warnings

    required = list(profiles[profile])
    required.extend(requested_docs)
    selected: list[Path] = []
    if required:
        for doc in required:
            path = docs_root / doc
            if path.exists():
                selected.append(path)
            else:
                failures.append(f"missing requested quant doc: {doc}")
        return selected, failures, warnings

    name_pattern = re.compile(r"(alpha|roadmap|factor|stage|provider|falsification|concordance)", re.IGNORECASE)
    selected = [
        path
        for path in sorted(docs_root.glob("*.md"))
        if name_pattern.search(path.name)
    ][:MAX_EVIDENCE_DOCS]
    if not selected:
        warnings.append("no high-signal quant docs matched generic evidence patterns")
        selected = sorted(docs_root.glob("*.md"))[:MAX_EVIDENCE_DOCS]
    if not selected:
        failures.append("evidence root has docs/quant_research but no markdown docs")
    return selected, failures, warnings


def validate_skill_files(
    require_external_secret_scan: bool,
    *,
    scan_root: Path,
    allow_patterns: list[str],
) -> tuple[list[str], dict]:
    failures: list[str] = []
    details: dict = {}

    skill_md = SKILL_DIR / "SKILL.md"
    if not skill_md.exists():
        return ["missing SKILL.md"], details

    text = read_text(skill_md)
    details["skill_md_lines"] = len(text.splitlines())
    if details["skill_md_lines"] > 500:
        failures.append("SKILL.md exceeds 500 lines")

    if not text.startswith("---"):
        failures.append("SKILL.md missing YAML frontmatter")
    if "name: quant-alpha-research" not in text:
        failures.append("SKILL.md frontmatter missing expected name")
    if "description:" not in text:
        failures.append("SKILL.md frontmatter missing description")

    description = parse_skill_description(text)
    details["description_chars"] = len(description)
    for phrase in ["alpha", "Stage 0", "falsification", "concordance", "Do not use"]:
        if phrase.lower() not in description.lower():
            failures.append(f"description missing trigger/boundary phrase: {phrase}")
    for name, markers in CHINESE_TRIGGER_MARKERS.items():
        if not any(marker in description for marker in markers):
            failures.append(f"description missing Chinese trigger marker: {name}")

    linked_refs = sorted(set(re.findall(r"`(references/[^`]+\.md)`", text)))
    details["linked_references"] = linked_refs
    for ref in linked_refs:
        if not (SKILL_DIR / ref).exists():
            failures.append(f"missing linked reference: {ref}")

    openai_yaml = SKILL_DIR / "agents" / "openai.yaml"
    if not openai_yaml.exists():
        failures.append("missing agents/openai.yaml")
    elif "$quant-alpha-research" not in read_text(openai_yaml):
        failures.append("openai.yaml default_prompt must mention $quant-alpha-research")

    excluded_dirs = load_excluded_dirs(scan_root)
    allowed_secret_patterns = load_allowed_secret_patterns(allow_patterns)
    scanned_files = [
        path
        for path in scan_root.rglob("*")
        if path.is_file()
        and should_scan_file(path, scan_root, excluded_dirs)
    ]
    details["scanned_file_count"] = len(scanned_files)
    details["scan_scope"] = "skill" if scan_root.resolve() == SKILL_DIR.resolve() else "explicit_repo_root"
    details["excluded_dirs"] = sorted(excluded_dirs)
    skipped_files: list[str] = []
    for path in scanned_files:
        content, warning = scan_text(path, scan_root)
        if warning:
            skipped_files.append(warning)
        if content is None:
            continue
        placeholder_marker = "TO" + "DO"
        if placeholder_marker in content:
            failures.append(f"placeholder marker remains in {rel(path, scan_root)}")
        for name, pattern in SECRET_PATTERNS.items():
            for match in pattern.finditer(content):
                if is_detector_definition(path, content, match.start()):
                    continue
                if is_allowed_secret_match(path, content, match.start(), name, scan_root, allowed_secret_patterns):
                    continue
                failures.append(f"{name} found in {rel(path, scan_root)}")
                break
        entropy_hits = high_entropy_tokens(content)
        if entropy_hits:
            failures.append(
                f"high_entropy_token candidates found in {rel(path, scan_root)}: {', '.join(entropy_hits[:3])}"
            )
    details["scan_warnings"] = skipped_files

    external_failures, external_details = run_external_secret_scan(require_external_secret_scan, scan_root)
    failures.extend(external_failures)
    details["external_secret_scan"] = external_details

    return failures, details


def probe_evidence_root(
    evidence_root: Path,
    *,
    profile: str,
    requested_docs: list[str],
    profiles: dict[str, list[str]],
    verbose: bool,
) -> tuple[list[str], dict]:
    failures: list[str] = []
    root = evidence_root.resolve()
    details: dict = {"evidence_root": redact_path(root, verbose), "profile": profile}

    if not root.exists():
        return [f"evidence root does not exist: {redact_path(root, verbose)}"], details

    before = git_status(root)
    before_ignored = git_status(root, ignored=True)
    docs, doc_failures, warnings = select_evidence_docs(root, profile, requested_docs, profiles)
    failures.extend(doc_failures)
    details["warnings"] = warnings
    details["docs_checked"] = [path.name for path in docs]

    state_before = path_state(docs, verbose=verbose)
    extracted: dict[str, dict[str, object]] = {}
    for path in docs:
        content = read_text(path)
        extracted[path.name] = {
            "chars": len(content),
            "mentions_canonical_parent": "canonical parent" in content.lower(),
            "mentions_falsification": "falsification" in content.lower(),
            "mentions_stage0": "stage0" in content.lower() or "stage 0" in content.lower(),
            "mentions_concordance": "concordance" in content.lower(),
        }

    state_after = path_state(docs, verbose=verbose)
    after = git_status(root)
    after_ignored = git_status(root, ignored=True)
    details["doc_signal_summary"] = extracted
    details["read_only_guard"] = {
        "git_status_unchanged": before == after,
        "git_status_with_ignored_unchanged": before_ignored == after_ignored,
        "checked_path_count": len(docs),
        "checked_paths_unchanged": state_before == state_after,
        "git_status_before_summary": summarize_git_status(before),
        "git_status_after_summary": summarize_git_status(after),
        "git_status_ignored_before_summary": summarize_git_status(before_ignored),
        "git_status_ignored_after_summary": summarize_git_status(after_ignored),
    }
    if verbose:
        details["read_only_guard"]["git_status_before"] = before
        details["read_only_guard"]["git_status_after"] = after
        details["read_only_guard"]["git_status_ignored_before"] = before_ignored
        details["read_only_guard"]["git_status_ignored_after"] = after_ignored
        details["read_only_guard"]["path_state_before"] = state_before
        details["read_only_guard"]["path_state_after"] = state_after

    if before != after:
        failures.append("evidence root git status changed during read-only probe")
    if before_ignored != after_ignored:
        failures.append("evidence root ignored-status changed during read-only probe")
    if state_before != state_after:
        failures.append("evidence root checked path state changed during read-only probe")

    return failures, details


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Explicitly widen skill-package scanning beyond the installed skill directory.",
    )
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--evidence-profile", default="generic")
    parser.add_argument("--evidence-doc", action="append", default=[])
    parser.add_argument("--profile-dir", type=Path, help="Directory of local evidence profile JSON files.")
    parser.add_argument("--allow-pattern", action="append", default=[], help="Regex allowlist for a secret-scan hit.")
    parser.add_argument("--require-external-secret-scan", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    scan_root = (args.repo_root or DEFAULT_SCAN_ROOT).resolve()
    profiles = load_evidence_profiles(args.profile_dir)
    if args.evidence_profile not in profiles:
        raise SystemExit(
            f"unknown evidence profile {args.evidence_profile!r}; available profiles: {', '.join(sorted(profiles))}"
        )

    failures, details = validate_skill_files(
        args.require_external_secret_scan,
        scan_root=scan_root,
        allow_patterns=args.allow_pattern,
    )
    evidence_details = None
    if args.evidence_root:
        evidence_failures, evidence_details = probe_evidence_root(
            args.evidence_root,
            profile=args.evidence_profile,
            requested_docs=args.evidence_doc,
            profiles=profiles,
            verbose=args.verbose,
        )
        failures.extend(evidence_failures)

    result = {
        "passed": not failures,
        "failures": failures,
        "skill": details,
        "evidence_probe": evidence_details,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
