"""Environment discovery, system checks, and logger for NORA devstack."""

import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPECTED_PACKAGES = [
    ("nora-basis", "nora_basis"),
    ("nora-capabilities", "nora_capabilities"),
    ("nora-capsules", "nora_capsules"),
    ("nora-cli", "nora_cli"),
    ("nora-conformance", "nora_conformance"),
    ("nora-connectors", "nora_connectors"),
    ("nora-evals", "nora_evals"),
    ("nora-evidence", "nora_evidence"),
    ("nora-jurisdiction-packs", "nora_jurisdiction_packs"),
    ("nora-legal-research", "nora_legal_research"),
    ("nora-retrieval", "nora_retrieval"),
    ("nora-specification", "nora_specification"),
]


def get_devstack_dir() -> Path:
    """Return Path to nora-devstack root directory."""
    curr = Path(__file__).resolve()
    return curr.parents[2]


def get_monorepo_root() -> Path:
    """Return Path to monorepo root directory containing all nora-* repos."""
    return get_devstack_dir().parent


def get_state_dir() -> Path:
    """Return Path to managed local state directory (.devstack)."""
    state_dir = get_devstack_dir() / ".devstack"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def get_components_dir() -> Path:
    """Return Path to managed components directory (.devstack/components)."""
    comp_dir = get_state_dir() / "components"
    comp_dir.mkdir(parents=True, exist_ok=True)
    return comp_dir


def setup_monorepo_pythonpath() -> list[str]:
    """Ensure all nora-*/src directories (sibling or .devstack/components/) are added to sys.path."""
    monorepo = get_monorepo_root()
    devstack_dir = get_devstack_dir()
    components_dir = devstack_dir / ".devstack" / "components"
    added = []

    # 1. Check sibling monorepo directories
    for pkg_dir in sorted(monorepo.glob("nora-*/src")):
        p_str = str(pkg_dir.resolve())
        if p_str not in sys.path:
            sys.path.insert(0, p_str)
            added.append(p_str)

    # 2. Check managed .devstack/components directories
    if components_dir.exists():
        for pkg_dir in sorted(components_dir.glob("nora-*/src")):
            p_str = str(pkg_dir.resolve())
            if p_str not in sys.path:
                sys.path.insert(0, p_str)
                added.append(p_str)

    # 3. Add current devstack src dir if not present
    devstack_src = str((devstack_dir / "src").resolve())
    if devstack_src not in sys.path:
        sys.path.insert(0, devstack_src)
        added.append(devstack_src)

    return added


def get_logs_dir() -> Path:
    """Return Path to logs directory (.devstack/logs)."""
    logs_dir = get_state_dir() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_log_file() -> Path:
    """Return Path to devstack log file."""
    return get_logs_dir() / "devstack.log"


def log_event(message: str) -> None:
    """Write timestamped message to devstack log file."""
    ts = datetime.now(timezone.utc).isoformat()
    log_file = get_log_file()
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {message}\n")


def check_python() -> tuple[bool, str]:
    """Check Python version >= 3.10."""
    v = sys.version_info
    ver_str = f"{v.major}.{v.minor}.{v.micro}"
    if v.major == 3 and v.minor >= 10:
        return True, f"Python {ver_str} (>= 3.10)"
    return False, f"Python {ver_str} (requires >= 3.10)"


def check_git() -> tuple[bool, str]:
    """Check Git binary."""
    git_bin = shutil.which("git")
    if not git_bin:
        return False, "Git executable not found in PATH"
    try:
        res = subprocess.run([git_bin, "--version"], capture_output=True, text=True, check=True)
        return True, res.stdout.strip()
    except Exception as e:
        return False, f"Git check failed: {e}"


def check_docker() -> tuple[bool, str]:
    """Check Docker (optional)."""
    docker_bin = shutil.which("docker")
    if not docker_bin:
        return True, "Docker optional (not found in PATH)"
    try:
        res = subprocess.run([docker_bin, "--version"], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            return True, f"Docker available: {res.stdout.strip()}"
        return True, "Docker optional (daemon not running)"
    except Exception as e:
        return True, f"Docker optional ({e})"


def check_sqlite() -> tuple[bool, str]:
    """Check SQLite python interface."""
    try:
        ver = sqlite3.sqlite_version
        return True, f"SQLite {ver} (sqlite3 python module available)"
    except Exception as e:
        return False, f"SQLite check failed: {e}"


def check_disk_space(min_mb: int = 500) -> tuple[bool, str]:
    """Check disk space for devstack workspace."""
    devstack_dir = get_devstack_dir()
    try:
        usage = shutil.disk_usage(devstack_dir)
        free_mb = usage.free // (1024 * 1024)
        if free_mb >= min_mb:
            return True, f"Disk space {free_mb} MB free (min {min_mb} MB)"
        return False, f"Low disk space: {free_mb} MB free (requires {min_mb} MB)"
    except Exception as e:
        return False, f"Disk space check failed: {e}"


def run_doctor() -> dict[str, tuple[bool, str]]:
    """Execute all doctor diagnostic checks."""
    log_event("Executing nora-dev doctor checks")
    checks = {
        "python": check_python(),
        "git": check_git(),
        "sqlite": check_sqlite(),
        "disk_space": check_disk_space(),
        "docker": check_docker(),
    }
    return checks


def run_bootstrap() -> dict[str, str | bool]:
    """Clone/link component repositories into managed environment and verify package imports."""
    log_event("Executing nora-dev bootstrap")
    setup_monorepo_pythonpath()

    # If running standalone, clone missing components from GitHub into .devstack/components/
    components_dir = get_components_dir()
    monorepo = get_monorepo_root()

    import PyYAML  # YAML parser for lockfile
    import yaml

    lockfile_path = get_devstack_dir() / "components.lock.yaml"
    if lockfile_path.exists():
        with open(lockfile_path, "r", encoding="utf-8") as f:
            lock_data = yaml.safe_load(f) or {}
        components = lock_data.get("components", {})

        for repo_name, meta in components.items():
            if repo_name == "nora-orchestrator":
                continue  # Orchestrator is private

            sibling_path = monorepo / repo_name
            comp_path = components_dir / repo_name

            if not sibling_path.exists() and not comp_path.exists():
                git_url = meta.get("git_url")
                commit_sha = meta.get("commit_sha")
                if git_url:
                    log_event(f"Cloning {repo_name} from {git_url} into {comp_path}")
                    try:
                        subprocess.run(
                            ["git", "clone", git_url, str(comp_path)],
                            check=True,
                            capture_output=True,
                            text=True,
                        )
                        if commit_sha:
                            subprocess.run(
                                ["git", "checkout", commit_sha],
                                cwd=str(comp_path),
                                check=True,
                                capture_output=True,
                                text=True,
                            )
                    except Exception as e:
                        log_event(f"Failed to clone/checkout {repo_name}: {e}")

    # Re-run pythonpath setup to capture newly cloned components
    setup_monorepo_pythonpath()

    import_status = {}
    all_ok = True

    for repo_name, pkg_name in EXPECTED_PACKAGES:
        if repo_name == "nora-orchestrator":
            continue  # Orchestrator is private

        try:
            mod = __import__(pkg_name)
            import_status[pkg_name] = "OK"
        except Exception as e:
            import_status[pkg_name] = f"FAILED: {e}"
            all_ok = False

    log_event(f"Bootstrap import verification complete. Status: {'SUCCESS' if all_ok else 'FAILED'}")
    return {
        "success": all_ok,
        "packages": import_status,
        "state_dir": str(get_state_dir()),
    }
