"""The committed Meridian example must equal a fresh run of the script that generates it."""
import os
import subprocess
import sys
import unittest

from helpers import ROOT


class Meridian(unittest.TestCase):
    def test_committed_example_matches_a_fresh_run(self):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        env.pop("PMF_WORKSPACE", None)
        r = subprocess.run([sys.executable, os.path.join("examples", "run_demo.py"), "--check"], cwd=ROOT, env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_example_workspace_is_valid(self):
        from helpers import run
        ws = os.path.join(ROOT, "examples", "meridian", "workspace")
        old = os.environ.get("PMF_WORKSPACE")
        os.environ["PMF_WORKSPACE"] = ws
        os.environ["PMF_FAKE_NOW"] = "2026-07-03T15:00:00Z"
        try:
            rc, out, err = run(["check"])
            self.assertEqual(rc, 0, out + err)
            self.assertIn("0 error(s)", out)
            rc, out, err = run(["health", "--json"])
            self.assertEqual(rc, 0)
        finally:
            os.environ.pop("PMF_FAKE_NOW", None)
            if old is None:
                os.environ.pop("PMF_WORKSPACE", None)
            else:
                os.environ["PMF_WORKSPACE"] = old


if __name__ == "__main__":
    unittest.main()
