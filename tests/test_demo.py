"""Unit and subprocess tests for nora-devstack seed and demo workflow execution."""

import subprocess
import sys
import unittest

from nora_devstack.demo import run_demo
from nora_devstack.environment import get_devstack_dir
from nora_devstack.services import seed_services

DEVSTACK_DIR = get_devstack_dir()


class TestDemoWorkflow(unittest.TestCase):
    def test_seed_services(self):
        res = seed_services()
        self.assertEqual(res["status"], "seeded")
        self.assertGreater(len(res["seeded_files"]), 0)

    def test_run_demo_unit(self):
        summary = run_demo(verbose=False)
        self.assertEqual(summary["status"], "SUCCESS")
        self.assertEqual(summary["total_steps"], 14)
        self.assertEqual(len(summary["results"]), 14)
        for step in summary["results"]:
            self.assertEqual(step["status"], "OK")

    def test_demo_subprocess_cli(self):
        cmd = [sys.executable, "-m", "nora_devstack.cli", "demo"]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=DEVSTACK_DIR)
        self.assertEqual(res.returncode, 0, f"CLI demo subprocess failed: {res.stderr}")
        self.assertIn("NORA_DEMO_OK=1", res.stdout)

    def test_script_nora_dev_demo(self):
        script = DEVSTACK_DIR / "scripts" / "nora-dev"
        res = subprocess.run([str(script), "demo"], capture_output=True, text=True, cwd=DEVSTACK_DIR)
        self.assertEqual(res.returncode, 0, f"nora-dev demo script failed: {res.stderr}")
        self.assertIn("NORA_DEMO_OK=1", res.stdout)


if __name__ == "__main__":
    unittest.main()
