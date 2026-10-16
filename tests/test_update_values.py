#!/usr/bin/env python3
"""
Unit tests for scripts/update-values.py logic.
Run with: python3 tests/test_update_values.py
"""
import sys
import os
import tempfile
import textwrap
import unittest

# Add scripts/ to path so we can import the module logic
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# We can't directly import update-values.py due to the hyphen in its name,
# so we test by subprocess invocation which also covers the CLI contract.
import subprocess

SCRIPT = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'update-values.py')
VALID_SUFFIX = 'mq-poc/values.yaml'

VALID_YAML = textwrap.dedent("""\
    rollout:
      containers:
        - image:
            tag: poc-1
""")

def run(yaml_content, tag, suffix=VALID_SUFFIX):
    """Write yaml_content to a temp file matching suffix, invoke script, return (rc, stdout, stderr)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Recreate the path suffix inside tmp
        parts = suffix.split('/')
        dirpath = os.path.join(tmpdir, *parts[:-1])
        os.makedirs(dirpath, exist_ok=True)
        fpath = os.path.join(tmpdir, *parts)
        with open(fpath, 'w') as f:
            f.write(yaml_content)
        result = subprocess.run(
            [sys.executable, SCRIPT, fpath, tag],
            capture_output=True, text=True
        )
        # Read back file if success
        if result.returncode == 0:
            with open(fpath) as f:
                written = f.read()
        else:
            written = None
        return result.returncode, result.stdout, result.stderr, written

class TestUpdateValues(unittest.TestCase):

    def test_valid_update(self):
        rc, out, err, written = run(VALID_YAML, 'poc-2')
        self.assertEqual(rc, 0, f"Expected success, got: {err}")
        self.assertIn('poc-1', out)
        self.assertIn('poc-2', out)
        self.assertIn('tag: poc-2', written)

    def test_invalid_tag_letters(self):
        rc, out, err, _ = run(VALID_YAML, 'poc-abc')
        self.assertNotEqual(rc, 0)
        self.assertIn('pattern', err.lower())

    def test_invalid_tag_no_prefix(self):
        rc, out, err, _ = run(VALID_YAML, '123')
        self.assertNotEqual(rc, 0)

    def test_invalid_tag_injection_attempt(self):
        rc, out, err, _ = run(VALID_YAML, 'poc-1; rm -rf /')
        self.assertNotEqual(rc, 0)

    def test_same_tag_rejected(self):
        rc, out, err, _ = run(VALID_YAML, 'poc-1')
        self.assertNotEqual(rc, 0)
        self.assertIn('already', err.lower())

    def test_wrong_file_suffix_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = os.path.join(tmpdir, 'other.yaml')
            with open(fpath, 'w') as f:
                f.write(VALID_YAML)
            result = subprocess.run(
                [sys.executable, SCRIPT, fpath, 'poc-2'],
                capture_output=True, text=True
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('mq-poc/values.yaml', result.stderr)

    def test_missing_file(self):
        result = subprocess.run(
            [sys.executable, SCRIPT, '/nonexistent/mq-poc/values.yaml', 'poc-2'],
            capture_output=True, text=True
        )
        self.assertNotEqual(result.returncode, 0)

    def test_no_args(self):
        result = subprocess.run(
            [sys.executable, SCRIPT],
            capture_output=True, text=True
        )
        self.assertNotEqual(result.returncode, 0)

if __name__ == '__main__':
    unittest.main(verbosity=2)
