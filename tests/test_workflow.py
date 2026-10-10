"""Static checks for the intentionally small release workflow."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/deploy.yml").read_text()


class WorkflowTests(unittest.TestCase):
    def test_full_checks_run_only_for_dev_pushes(self):
        trigger = WORKFLOW.split("permissions:", 1)[0]
        push_trigger = trigger.split("  push:", 1)[1].split("  workflow_dispatch:", 1)[0]
        checks = WORKFLOW.split("\n  checks:\n", 1)[1].split("\n  image:\n", 1)[0]

        self.assertIn("branches: [dev]", push_trigger)
        self.assertNotIn("pull_request:", trigger)
        self.assertNotIn("master", push_trigger)
        self.assertIn("github.event_name == 'push'", checks)
        self.assertIn("refs/heads/dev", checks)

    def test_manual_master_release_builds_without_repeating_full_suite(self):
        image = WORKFLOW.split("\n  image:\n", 1)[1].split("\n  deploy:\n", 1)[0]

        self.assertIn("github.event_name == 'workflow_dispatch'", image)
        self.assertIn("refs/heads/master", image)
        self.assertNotIn("needs: checks", image)
        self.assertNotIn("manage.py test", image)
        self.assertIn("tests/container-smoke.sh", image)

    def test_ci_checks_every_certificate_script(self):
        self.assertIn("bash -n deploy/scripts/*.sh deploy/certbot/*.sh", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
