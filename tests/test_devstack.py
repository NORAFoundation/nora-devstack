"""Unit and subprocess tests for nora-devstack orchestration and lockfile validation."""

import os
import subprocess
import sys
import unittest
import tempfile
from pathlib import Path

from nora_devstack.environment import (
    check_disk_space,
    check_git,
    check_python,
    check_sqlite,
    get_devstack_dir,
    run_bootstrap,
    run_doctor,
)
from nora_devstack.lockfile import (
    load_lockfile,
    validate_lockfile,
)
from nora_devstack.services import (
    get_logs,
    reset_services,
    start_services,
    stop_services,
)

DEVSTACK_DIR = get_devstack_dir()


class TestDevstackEnvironment(unittest.TestCase):
    def test_python_check(self):
        ok, msg = check_python()
        self.assertTrue(ok)
        self.assertIn("Python", msg)

    def test_git_check(self):
        ok, msg = check_git()
        self.assertTrue(ok)
        self.assertIn("git", msg.lower())

    def test_sqlite_check(self):
        ok, msg = check_sqlite()
        self.assertTrue(ok)
        self.assertIn("SQLite", msg)

    def test_disk_space_check(self):
        ok, msg = check_disk_space(min_mb=10)
        self.assertTrue(ok)

    def test_run_doctor(self):
        checks = run_doctor()
        self.assertIn("python", checks)
        self.assertIn("git", checks)
        self.assertIn("sqlite", checks)
        self.assertIn("disk_space", checks)
        self.assertTrue(checks["python"][0])

    def test_run_bootstrap(self):
        res = run_bootstrap()
        self.assertTrue(res["success"])
        self.assertEqual(len(res["packages"]), 12)
        for pkg, status in res["packages"].items():
            self.assertEqual(status, "OK")


class TestLockfileValidation(unittest.TestCase):
    def test_lockfile_exists_and_loads(self):
        lock_file = DEVSTACK_DIR / "components.lock.yaml"
        self.assertTrue(lock_file.exists())
        data = load_lockfile(lock_file)
        self.assertIn("components", data)
        self.assertEqual(len(data["components"]), 13)

    def test_validate_lockfile_valid(self):
        is_valid, errors = validate_lockfile(verify_git=False)
        self.assertTrue(is_valid, f"Lockfile validation failed: {errors}")
        self.assertEqual(len(errors), 0)

    def test_validate_lockfile_missing_file(self):
        is_valid, errors = validate_lockfile(lockfile_path="/tmp/nonexistent_lockfile.yaml")
        self.assertFalse(is_valid)
        self.assertTrue(any("does not exist" in e for e in errors))

    def test_validate_lockfile_invalid_sha(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tmp:
            tmp.write("""
schema_version: 1
components:
  nora-basis:
    commit: "invalid_short_sha"
""")
            tmp_path = tmp.name

        try:
            is_valid, errors = validate_lockfile(lockfile_path=tmp_path)
            self.assertFalse(is_valid)
            self.assertTrue(any("Missing required component" in e or "not a valid 40-char hex" in e for e in errors))
        finally:
            Path(tmp_path).unlink(missing_ok=True)


class TestServicesLifecycle(unittest.TestCase):
    def test_services_start_stop_reset(self):
        up_res = start_services()
        self.assertEqual(up_res["status"], "running")
        self.assertIn("evidence", up_res["services"]["sqlite_databases"])

        logs = get_logs(lines=5)
        self.assertIsInstance(logs, list)

        down_res = stop_services()
        self.assertEqual(down_res["status"], "stopped")

        reset_res = reset_services()
        self.assertEqual(reset_res["status"], "reset")


class TestSubprocessCLI(unittest.TestCase):
    def test_cli_doctor_subprocess(self):
        cmd = [sys.executable, "-m", "nora_devstack.cli", "doctor"]
        env = dict(os.environ)
        env["PYTHONPATH"] = ":".join(sys.path)
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=DEVSTACK_DIR, env=env)
        self.assertEqual(res.returncode, 0, f"Doctor subprocess failed: {res.stderr}")
        self.assertIn("[OK]", res.stdout)
        self.assertIn("lockfile", res.stdout)

    def test_cli_bootstrap_subprocess(self):
        cmd = [sys.executable, "-m", "nora_devstack.cli", "bootstrap"]
        env = dict(os.environ)
        env["PYTHONPATH"] = ":".join(sys.path)
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=DEVSTACK_DIR, env=env)
        self.assertEqual(res.returncode, 0, f"Bootstrap subprocess failed: {res.stderr}")
        self.assertIn("Devstack bootstrapped successfully", res.stdout)
    def test_script_nora_dev_doctor(self):
        script = DEVSTACK_DIR / "scripts" / "nora-dev"
        res = subprocess.run([str(script), "doctor"], capture_output=True, text=True, cwd=DEVSTACK_DIR)
        self.assertEqual(res.returncode, 0, f"nora-dev doctor failed: {res.stderr}")
        self.assertIn("NORA devstack diagnostic check", res.stdout)


if __name__ == "__main__":
    unittest.main()
