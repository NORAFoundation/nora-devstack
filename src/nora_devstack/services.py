"""Service lifecycle, state management, and seeding for NORA devstack."""

import json
import shutil
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from nora_devstack.environment import (
    check_docker,
    get_devstack_dir,
    get_log_file,
    get_logs_dir,
    get_state_dir,
    log_event,
)


def get_status_file() -> Path:
    """Return Path to service_status.json."""
    return get_state_dir() / "service_status.json"


def get_filestore_dir() -> Path:
    """Return Path to local filestore directory."""
    d = get_state_dir() / "filestore"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_seed_dir() -> Path:
    """Return Path to local managed seed directory."""
    d = get_state_dir() / "seed"
    d.mkdir(parents=True, exist_ok=True)
    return d


def init_sqlite_databases() -> dict[str, str]:
    """Initialize SQLite database files with schemas for local services."""
    state_dir = get_state_dir()
    db_paths = {
        "evidence": state_dir / "evidence.db",
        "retrieval": state_dir / "retrieval.db",
        "devstack": state_dir / "devstack.db",
    }

    # Evidence DB schema
    with sqlite3.connect(db_paths["evidence"]) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                artifact_id TEXT PRIMARY KEY,
                sha256 TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                content_type TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS custody_records (
                record_id TEXT PRIMARY KEY,
                artifact_id TEXT NOT NULL,
                action TEXT NOT NULL,
                actor TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                record_hash TEXT NOT NULL
            )
        """)

    # Retrieval DB schema
    with sqlite3.connect(db_paths["retrieval"]) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ledger_entries (
                entry_id TEXT PRIMARY KEY,
                ledger_id TEXT NOT NULL,
                scope_id TEXT NOT NULL,
                query TEXT NOT NULL,
                strategy TEXT NOT NULL,
                candidate_ids TEXT NOT NULL,
                executed_at TEXT NOT NULL
            )
        """)

    # Devstack status DB schema
    with sqlite3.connect(db_paths["devstack"]) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS status_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                details TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    return {k: str(v) for k, v in db_paths.items()}


def start_services() -> dict[str, Any]:
    """Start local stack services (SQLite / file store / optional containers)."""
    log_event("Starting local stack services")
    db_paths = init_sqlite_databases()
    filestore = str(get_filestore_dir())

    docker_ok, docker_msg = check_docker()
    compose_file = get_devstack_dir() / "compose" / "docker-compose.yml"
    docker_started = False

    if "Docker available" in docker_msg and compose_file.exists():
        try:
            res = subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "up", "-d"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if res.returncode == 0:
                docker_started = True
                log_event("Docker compose services started successfully")
        except Exception as e:
            log_event(f"Docker compose start skipped/failed: {e}")

    status_data = {
        "status": "running",
        "services": {
            "sqlite_databases": db_paths,
            "filestore": filestore,
            "docker_compose": "running" if docker_started else "disabled_or_optional",
        },
    }

    with open(get_status_file(), "w", encoding="utf-8") as f:
        json.dump(status_data, f, indent=2)

    log_event("Local stack services are running")
    return status_data


def stop_services() -> dict[str, Any]:
    """Stop local stack services."""
    log_event("Stopping local stack services")
    compose_file = get_devstack_dir() / "compose" / "docker-compose.yml"
    docker_ok, docker_msg = check_docker()

    if "Docker available" in docker_msg and compose_file.exists():
        try:
            subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "down"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            log_event("Docker compose services stopped")
        except Exception as e:
            log_event(f"Docker compose stop skipped/failed: {e}")

    status_data = {"status": "stopped", "services": {}}
    with open(get_status_file(), "w", encoding="utf-8") as f:
        json.dump(status_data, f, indent=2)

    log_event("Local stack services stopped cleanly")
    return status_data


def reset_services() -> dict[str, Any]:
    """Clear local state & reset database files cleanly."""
    log_event("Resetting local stack services and state")
    stop_services()

    state_dir = get_state_dir()
    for db_file in state_dir.glob("*.db"):
        try:
            db_file.unlink()
            log_event(f"Removed database file {db_file.name}")
        except Exception as e:
            log_event(f"Could not remove {db_file.name}: {e}")

    filestore = state_dir / "filestore"
    if filestore.exists():
        shutil.rmtree(filestore, ignore_errors=True)
        filestore.mkdir(parents=True, exist_ok=True)

    seed_dir = state_dir / "seed"
    if seed_dir.exists():
        shutil.rmtree(seed_dir, ignore_errors=True)

    # Re-initialize clean databases
    db_paths = init_sqlite_databases()

    reset_status = {
        "status": "reset",
        "cleared_databases": list(db_paths.keys()),
        "state_dir": str(state_dir),
    }
    log_event("Local state and database files reset cleanly")
    return reset_status


def seed_services() -> dict[str, Any]:
    """Seed synthetic demo corpus and sample exhibits."""
    log_event("Seeding synthetic demo corpus and sample exhibits")
    seed_dir = get_seed_dir()

    # Source synthetic matter file from nora-devstack/seed/synthetic_matter.json if available
    source_seed = get_devstack_dir() / "seed" / "synthetic_matter.json"
    if source_seed.exists():
        shutil.copy(source_seed, seed_dir / "synthetic_matter.json")

    # Create synthetic legal exhibit & contract files
    exhibit_1 = seed_dir / "exhibit_alpha.txt"
    exhibit_1.write_text(
        "CONFIDENTIALITY AND SECURITY AGREEMENT\n"
        "Section 4.1: Acme Corp shall maintain strict data confidentiality in accordance with ISO 27001 standards.\n"
        "Section 4.2: Audit records must be retained in an immutable custody ledger for 7 years.\n",
        encoding="utf-8",
    )

    exhibit_2 = seed_dir / "case_opinion_beta.txt"
    exhibit_2.write_text(
        "IN THE UNITED STATES COURT OF APPEALS FOR THE NINTH CIRCUIT\n"
        "Smith v. Jones, 500 F.3d 123 (9th Cir. 2020)\n"
        "Held: Verification of custody chains requires explicit hashing and provenance validation.\n",
        encoding="utf-8",
    )

    seeded_files = [str(f.name) for f in seed_dir.glob("*")]
    log_event(f"Seeded {len(seeded_files)} synthetic corpus items")
    return {
        "status": "seeded",
        "seed_dir": str(seed_dir),
        "seeded_files": seeded_files,
    }


def get_logs(lines: int = 50) -> list[str]:
    """Retrieve tail of devstack log file."""
    log_file = get_log_file()
    if not log_file.exists():
        return ["No log file found."]

    with open(log_file, "r", encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()

    return [line.rstrip("\r\n") for line in all_lines[-lines:]]
