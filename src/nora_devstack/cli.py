"""CLI entry point and command router for nora-dev."""

import argparse
import json
import sys
import subprocess
from typing import Sequence

from nora_devstack.demo import run_demo
from nora_devstack.environment import (
    get_devstack_dir,
    run_bootstrap,
    run_doctor,
    setup_monorepo_pythonpath,
)
from nora_devstack.lockfile import validate_lockfile
from nora_devstack.services import (
    get_logs,
    reset_services,
    seed_services,
    start_services,
    stop_services,
)


def handle_doctor(args: argparse.Namespace) -> int:
    """Handle nora-dev doctor subcommand."""
    checks = run_doctor()
    print("NORA devstack diagnostic check:")
    print("--------------------------------")
    all_ok = True
    for name, (ok, msg) in checks.items():
        status_tag = "[OK]" if ok else "[FAIL]"
        print(f"  {status_tag:7s} {name:12s}: {msg}")
        if not ok:
            all_ok = False

    # Also validate components.lock.yaml
    lockfile_ok, errors = validate_lockfile(verify_git=False)
    lock_tag = "[OK]" if lockfile_ok else "[FAIL]"
    if lockfile_ok:
        print(f"  {lock_tag:7s} lockfile    : components.lock.yaml valid for all 13 components")
    else:
        print(f"  {lock_tag:7s} lockfile    : Invalid components.lock.yaml ({'; '.join(errors)})")
        all_ok = False

    return 0 if all_ok else 1


def handle_bootstrap(args: argparse.Namespace) -> int:
    """Handle nora-dev bootstrap subcommand."""
    print("Bootstrapping NORA devstack environment...")
    result = run_bootstrap()
    if result["success"]:
        print(f"[OK] Devstack bootstrapped successfully. Managed state dir: {result['state_dir']}")
        print("Verified imports for all 13 component packages.")
        return 0
    else:
        print("[FAIL] Bootstrap failed for one or more components:")
        for pkg, status in result["packages"].items():
            if status != "OK":
                print(f"  - {pkg}: {status}")
        return 1


def handle_up(args: argparse.Namespace) -> int:
    """Handle nora-dev up subcommand."""
    print("Starting local devstack services...")
    status = start_services()
    print(f"[OK] Services status: {status['status']}")
    print(json.dumps(status, indent=2))
    return 0


def handle_down(args: argparse.Namespace) -> int:
    """Handle nora-dev down subcommand."""
    print("Stopping local devstack services...")
    status = stop_services()
    print(f"[OK] Services status: {status['status']}")
    return 0


def handle_reset(args: argparse.Namespace) -> int:
    """Handle nora-dev reset subcommand."""
    print("Resetting local devstack state & database files...")
    res = reset_services()
    print(f"[OK] Devstack state reset cleanly. Cleared databases: {res['cleared_databases']}")
    return 0


def handle_seed(args: argparse.Namespace) -> int:
    """Handle nora-dev seed subcommand."""
    print("Seeding synthetic demo corpus and sample exhibits...")
    res = seed_services()
    print(f"[OK] Seeded {len(res['seeded_files'])} synthetic corpus items into {res['seed_dir']}")
    return 0


def handle_demo(args: argparse.Namespace) -> int:
    """Handle nora-dev demo subcommand."""
    try:
        run_demo(verbose=True)
        return 0
    except Exception as e:
        print(f"\n[FAIL] Demo execution failed: {e}", file=sys.stderr)
        return 1


def handle_test(args: argparse.Namespace) -> int:
    """Handle nora-dev test subcommand."""
    setup_monorepo_pythonpath()
    devstack_dir = get_devstack_dir()
    print("Running devstack integrated test suite...")
    cmd = [sys.executable, "-m", "pytest", str(devstack_dir / "tests")]
    if args.extra_args:
        cmd.extend(args.extra_args)
    res = subprocess.run(cmd)
    return res.returncode


def handle_logs(args: argparse.Namespace) -> int:
    """Handle nora-dev logs subcommand."""
    lines = get_logs(args.lines)
    print(f"--- NORA Devstack Log Tail ({len(lines)} lines) ---")
    for line in lines:
        print(line)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="nora-dev",
        description="NORA One-Command Devstack Orchestration CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # doctor
    subparsers.add_parser("doctor", help="Check system requisites and lockfile validity")

    # bootstrap
    subparsers.add_parser("bootstrap", help="Setup managed environment and verify package imports")

    # up
    subparsers.add_parser("up", help="Start local stack services (SQLite / file store)")

    # down
    subparsers.add_parser("down", help="Stop local stack services")

    # reset
    subparsers.add_parser("reset", help="Clear local state & reset database files cleanly")

    # seed
    subparsers.add_parser("seed", help="Seed synthetic demo corpus and sample exhibits")

    # demo
    subparsers.add_parser("demo", help="Execute full synthetic local workflow end-to-end")

    # test
    test_parser = subparsers.add_parser("test", help="Run integrated test suite")
    test_parser.add_argument("extra_args", nargs=argparse.REMAINDER, help="Extra pytest arguments")

    # logs
    logs_parser = subparsers.add_parser("logs", help="View devstack service/operation log tail")
    logs_parser.add_argument("-n", "--lines", type=int, default=50, help="Number of log lines to show")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Main CLI entrypoint."""
    setup_monorepo_pythonpath()
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    handlers = {
        "doctor": handle_doctor,
        "bootstrap": handle_bootstrap,
        "up": handle_up,
        "down": handle_down,
        "reset": handle_reset,
        "seed": handle_seed,
        "demo": handle_demo,
        "test": handle_test,
        "logs": handle_logs,
    }

    handler = handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
