"""Regression coverage for description parsing and private-key detection."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validator", ROOT / "skills/quant-alpha-research/scripts/validate_skill_package.py"
)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class DescriptionTests(unittest.TestCase):
    def parse(self, value):
        return validator.parse_skill_description(f"---\ndescription: {value}\n---\n")

    def test_double_quoted_unicode_and_escapes(self):
        value = 'Stage 0: 寻找新alpha, "quoted", backslash \\ and newline\n'
        self.assertEqual(self.parse(json.dumps(value)), value)

    def test_yaml_single_quotes_preserve_apostrophes_and_backslashes(self):
        self.assertEqual(self.parse("'researcher''s Stage 0'"), "researcher's Stage 0")
        self.assertEqual(self.parse(r"'literal \n and \u0041'"), r"literal \n and \u0041")

    def test_malformed_and_unsupported_scalars_fail_closed(self):
        for value in ['"unclosed', "'unclosed", "'bad'quote'", '"x" "y"', r'"bad\q"', '|', '>']:
            with self.subTest(value=value):
                self.assertEqual(self.parse(value), "")

    def test_plain_description(self):
        self.assertEqual(self.parse('Stage 0 and falsification'), 'Stage 0 and falsification')

    def test_current_description_is_preserved(self):
        text = (validator.SKILL_DIR / 'SKILL.md').read_text(encoding='utf-8')
        raw = next(line.split(':', 1)[1].strip() for line in text.splitlines() if line.startswith('description:'))
        self.assertEqual(validator.parse_skill_description(text), json.loads(raw))


class SecretScanTests(unittest.TestCase):
    def scan_label(self, label):
        # Synthetic headers only: never embed real private-key material in tests.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'fixture.txt').write_text(f'-----BEGIN {label}-----\n', encoding='utf-8')
            with patch.object(validator, 'run_external_secret_scan', return_value=([], {})):
                failures, _ = validator.validate_skill_files(False, scan_root=root, allow_patterns=[])
            return [item for item in failures if item.startswith('private_key_block')]

    def test_private_key_headers_are_detected_without_key_body(self):
        for label in ['PRIVATE KEY', 'RSA PRIVATE KEY', 'EC PRIVATE KEY', 'DSA PRIVATE KEY',
                      'OPENSSH PRIVATE KEY', 'ENCRYPTED PRIVATE KEY', 'X25519 PRIVATE KEY',
                      'ML-KEM-768 PRIVATE KEY',
                      'RSA PRIVATE KEY----- then -----BEGIN CERTIFICATE']:
            with self.subTest(label=label):
                self.assertEqual(self.scan_label(label), ['private_key_block found in fixture.txt'])

    def test_public_pem_headers_are_not_private_keys(self):
        for label in ['CERTIFICATE', 'PUBLIC KEY', 'RSA PUBLIC KEY', 'CERTIFICATE REQUEST']:
            with self.subTest(label=label):
                self.assertEqual(self.scan_label(label), [])


if __name__ == '__main__':
    unittest.main()
