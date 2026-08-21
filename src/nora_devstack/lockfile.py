"""Lockfile loading and component commit SHA validation for NORA devstack."""

import re
import subprocess
from pathlib import Path
from typing import Any
import yaml

from nora_devstack.environment import EXPECTED_PACKAGES, get_devstack_dir, get_monorepo_root, log_event

HEX_SHA_REGEX = re.compile(r"^[0-9a-fA-F]{40}$")


def get_default_lockfile_path() -> Path:
    """Return default path to components.lock.yaml."""
    return get_devstack_dir() / "components.lock.yaml"


def load_lockfile(lockfile_path: Path | str | None = None) -> dict[str, Any]:
    """Load and parse components.lock.yaml file."""
    path = Path(lockfile_path) if lockfile_path else get_default_lockfile_path()
    if not path.exists():
        raise FileNotFoundError(f"Lockfile not found at {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid lockfile format at {path}: must be a YAML object")

    return data


def validate_lockfile(
    lockfile_path: Path | str | None = None, verify_git: bool = False
) -> tuple[bool, list[str]]:
    """Validate components.lock.yaml format, completeness for all 13 repos, and optionally git SHAs.
    
    Returns:
        (is_valid, list_of_errors)
    """
    path = Path(lockfile_path) if lockfile_path else get_default_lockfile_path()
    errors: list[str] = []

    if not path.exists():
        return False, [f"Lockfile does not exist at {path}"]

    try:
        data = load_lockfile(path)
    except Exception as e:
        return False, [f"Failed to parse lockfile: {e}"]

    components = data.get("components")
    if not isinstance(components, dict):
        return False, ["Lockfile missing 'components' dictionary"]

    expected_repo_names = [repo for repo, _ in EXPECTED_PACKAGES]
    for repo_name in expected_repo_names:
        if repo_name not in components:
            errors.append(f"Missing required component '{repo_name}' in lockfile")
            continue

        entry = components[repo_name]
        if not isinstance(entry, dict):
            errors.append(f"Component '{repo_name}' entry must be a dictionary")
            continue

        commit = entry.get("commit")
        if not commit or not isinstance(commit, str):
            errors.append(f"Component '{repo_name}' missing string 'commit' SHA")
            continue

        if not HEX_SHA_REGEX.match(commit.strip()):
            errors.append(f"Component '{repo_name}' commit SHA '{commit}' is not a valid 40-char hex string")

    if verify_git and not errors:
        monorepo = get_monorepo_root()
        for repo_name in expected_repo_names:
            repo_path = monorepo / repo_name
            if (repo_path / ".git").exists():
                try:
                    res = subprocess.run(
                        ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    actual_sha = res.stdout.strip()
                    pinned_sha = components[repo_name]["commit"].strip()
                    if actual_sha != pinned_sha:
                        errors.append(
                            f"Git SHA mismatch for '{repo_name}': pinned={pinned_sha}, actual={actual_sha}"
                        )
                except Exception as e:
                    log_event(f"Git check skipped for {repo_name}: {e}")

    is_valid = len(errors) == 0
    log_event(f"Lockfile validation at {path}: {'VALID' if is_valid else f'INVALID ({len(errors)} errors)'}")
    return is_valid, errors
