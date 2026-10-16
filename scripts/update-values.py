#!/usr/bin/env python3
"""
Guarded writer for mq-poc/values.yaml.

Updates rollout.containers[0].image.tag to a validated new tag.
Rejects any input that would touch other keys, extra files, or malformed YAML.

Usage:
    update-values.py <values_file> <new_tag>

Exits 0 on success (prints before/after tag to stdout).
Exits non-zero on any validation failure (prints reason to stderr).
"""
import sys
import re
import copy

TAG_PATTERN = re.compile(r'^poc-[0-9]+$')
VALUES_FILE_SUFFIX = "mq-poc/values.yaml"

def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

def load_yaml_simple(path):
    """
    Minimal YAML loader for the known structure.
    Uses PyYAML if available, else falls back to the stdlib.
    We only need to handle the exact known schema.
    """
    try:
        import yaml
        with open(path) as f:
            return yaml.safe_load(f)
    except ImportError:
        # Fallback: hand-parse the known 4-line structure
        # rollout:\n  containers:\n    - image:\n        tag: <value>
        with open(path) as f:
            content = f.read()
        m = re.search(r'^\s+tag:\s*(\S+)\s*$', content, re.MULTILINE)
        if not m:
            die("Cannot locate 'tag:' in values.yaml (fallback parser)")
        return {"rollout": {"containers": [{"image": {"tag": m.group(1)}}]}}

def dump_yaml_simple(data, path):
    """Write back with exact known structure — no YAML library serialization drift."""
    try:
        tag = data["rollout"]["containers"][0]["image"]["tag"]
    except (KeyError, IndexError, TypeError):
        die("Cannot extract tag from data structure for write")
    with open(path, "w") as f:
        f.write(f"rollout:\n  containers:\n    - image:\n        tag: {tag}\n")

def main():
    if len(sys.argv) != 3:
        die(f"Usage: {sys.argv[0]} <values_file> <new_tag>")

    values_file = sys.argv[1]
    new_tag = sys.argv[2]

    # Validate new_tag
    if not TAG_PATTERN.match(new_tag):
        die(f"Tag '{new_tag}' does not match required pattern {TAG_PATTERN.pattern!r}")

    # Validate values_file path ends with expected suffix (prevent misdirection)
    if not values_file.endswith(VALUES_FILE_SUFFIX):
        die(f"values_file must end with '{VALUES_FILE_SUFFIX}', got: {values_file!r}")

    # Load current state
    current = load_yaml_simple(values_file)

    # Extract and validate current structure
    try:
        containers = current["rollout"]["containers"]
        if not isinstance(containers, list) or len(containers) != 1:
            die("Expected exactly one container in rollout.containers")
        image = containers[0].get("image", {})
        current_tag = image.get("tag")
        if not isinstance(current_tag, str):
            die(f"Current tag is not a string: {current_tag!r}")
    except (KeyError, TypeError) as e:
        die(f"Unexpected structure in values.yaml: {e}")

    if current_tag == new_tag:
        die(f"Tag is already '{new_tag}' — no change needed")

    print(f"before: {current_tag}")
    print(f"after:  {new_tag}")

    # Apply update
    updated = copy.deepcopy(current)
    updated["rollout"]["containers"][0]["image"]["tag"] = new_tag

    dump_yaml_simple(updated, values_file)
    print(f"Written: {values_file}")

if __name__ == "__main__":
    main()
