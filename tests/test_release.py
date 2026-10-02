"""Release and external smoke contract tests using isolated command stubs."""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISION = "a" * 40
IMAGE = "registry.example.test/app@sha256:" + "b" * 64


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "deploy/scripts").mkdir(parents=True)
        (self.root / "bin").mkdir()
        for name in ("release.sh", "smoke.sh"):
            shutil.copy(ROOT / "deploy/scripts" / name, self.root / "deploy/scripts" / name)
        (self.root / ".env").write_text("SITE_URL=https://example.test\n")
        (self.root / "deploy/scripts/backup.sh").write_text(
            '#!/bin/bash\necho backup >> "$COMMAND_LOG"\n[[ "${FAIL_BACKUP:-0}" != 1 ]]\n'
        )
        self.log = self.root / "commands.log"
        self.write_stub(
            "docker",
            """#!/bin/bash
printf 'docker %s\\n' "$*" >> "$COMMAND_LOG"
if [[ -n "${FAIL_DOCKER_MATCH:-}" && "$*" == *"$FAIL_DOCKER_MATCH"* ]]; then exit 19; fi
case "$*" in
  'image inspect --format '*) echo "$IMAGE_REVISION";;
  'inspect --format '*) echo 'registry.example.test/app:previous';;
  *'ps -q web'*) echo 'old-web-id';;
esac
""",
        )
        self.write_stub("git", '#!/bin/bash\necho "$CHECKOUT_REVISION"\n')
        self.write_stub(
            "curl",
            """#!/bin/bash
printf 'curl %s\\n' "$*" >> "$COMMAND_LOG"
if [[ -n "${FAIL_CURL_MATCH:-}" && "$*" == *"$FAIL_CURL_MATCH"* ]]; then exit 22; fi
if [[ "$*" == *'/ready/'* ]]; then
    printf '{"status":"%s","revision":"%s"}' "${READY_STATUS:-ok}" "$CURL_REVISION"
fi
""",
        )
        self.env = os.environ.copy()
        for name in ("ALLOW_LOCAL_IMAGE", "ROLLBACK_DB_COMPATIBLE", "SMOKE_URL", "HOMESERVICE_ENV_FILE"):
            self.env.pop(name, None)
        self.env.update(
            PATH=f"{self.root / 'bin'}:{self.env['PATH']}",
            COMMAND_LOG=str(self.log),
            APP_IMAGE=IMAGE,
            IMAGE_REVISION=REVISION,
            CHECKOUT_REVISION=REVISION,
            RELEASE_REVISION=REVISION,
            CURL_REVISION=REVISION,
            SITE_URL="https://example.test",
        )

    def write_stub(self, name, content):
        path = self.root / "bin" / name
        path.write_text(content)
        path.chmod(0o755)

    def run_script(self, script="release.sh", *args, **env):
        return subprocess.run(
            ["bash", str(self.root / "deploy/scripts" / script), *args],
            cwd="/tmp",
            env=self.env | env,
            text=True,
            capture_output=True,
            check=False,
        )

    def commands(self):
        return self.log.read_text() if self.log.exists() else ""

    def test_success_orders_checks_stop_backup_migrate_start_smoke(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        commands = self.commands()
        markers = [
            "manage.py check --deploy",
            "stop web worker",
            "backup\n",
            "run --rm --no-deps release\n",
            "up -d --no-deps --wait",
            "nginx -t",
            "nginx -s reload",
            "/ready/",
        ]
        positions = [commands.index(marker) for marker in markers]
        self.assertEqual(positions, sorted(positions))
        state = self.root / "deploy/.release"
        self.assertEqual((state / "current-image").read_text().strip(), IMAGE)
        self.assertEqual((state / "current-revision").read_text().strip(), REVISION)

    def test_mismatched_image_revision_stops_before_database_changes(self):
        result = self.run_script(IMAGE_REVISION="c" * 40)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("up -d", self.commands())
        self.assertNotIn("run --rm", self.commands())

    def test_mutable_tag_is_rejected(self):
        result = self.run_script(APP_IMAGE="registry.example.test/app:latest")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.commands(), "")

    def test_expected_revision_cannot_hide_a_different_checkout(self):
        result = self.run_script(CHECKOUT_REVISION="c" * 40)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("up -d", self.commands())
        self.assertNotIn("run --rm", self.commands())

    def test_preflight_failure_does_not_stop_writers_or_migrate(self):
        result = self.run_script(FAIL_DOCKER_MATCH="manage.py check --deploy")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("stop web worker", self.commands())
        self.assertNotIn("run --rm --no-deps release\n", self.commands())

    def test_backup_failure_restarts_previous_writers_without_migration(self):
        result = self.run_script(FAIL_BACKUP="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("start web worker", self.commands())
        self.assertNotIn("run --rm --no-deps release\n", self.commands())
        self.assertFalse((self.root / "deploy/.release/current-image").exists())

    def test_migration_failure_does_not_restart_old_code_or_report_success(self):
        result = self.run_script(FAIL_DOCKER_MATCH="run --rm --no-deps release")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("start web worker", self.commands())
        self.assertNotIn("up -d --no-deps --wait", self.commands())
        self.assertFalse((self.root / "deploy/.release/current-image").exists())

    def test_nginx_validation_failure_never_reloads_or_records_success(self):
        result = self.run_script(FAIL_DOCKER_MATCH="nginx -t")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("nginx -s reload", self.commands())
        self.assertFalse((self.root / "deploy/.release/current-image").exists())

    def test_stale_external_revision_fails_release(self):
        result = self.run_script(CURL_REVISION="c" * 40)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "deploy/.release/current-image").exists())

    def test_failed_asset_fetch_fails_release(self):
        result = self.run_script(FAIL_CURL_MATCH="main.css")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "deploy/.release/current-image").exists())

    def test_rollback_requires_explicit_schema_gate(self):
        result = self.run_script("release.sh", "rollback")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("stop web worker", self.commands())

    def test_authorized_rollback_snapshots_without_running_migrations(self):
        result = self.run_script("release.sh", "rollback", ROLLBACK_DB_COMPATIBLE="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("backup\n", self.commands())
        self.assertIn("cp -R /opt/homeservice/static/", self.commands())
        self.assertNotIn("run --rm --no-deps release\n", self.commands())

    def test_initialization_omits_backup_and_public_tls_smoke(self):
        result = self.run_script("release.sh", "init")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("backup\n", self.commands())
        self.assertNotIn("curl ", self.commands())

    def test_smoke_rejects_http(self):
        result = self.run_script("smoke.sh", SITE_URL="http://example.test")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.commands(), "")

    def test_smoke_rejects_unavailable_dependencies(self):
        result = self.run_script("smoke.sh", READY_STATUS="unavailable")
        self.assertNotEqual(result.returncode, 0)

    def test_python_optimization_cannot_bypass_revision_validation(self):
        result = self.run_script(
            "smoke.sh",
            EXPECTED_REVISION=REVISION,
            CURL_REVISION="c" * 40,
            PYTHONOPTIMIZE="1",
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
