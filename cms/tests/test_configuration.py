import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase


class ProductionConfigurationTests(SimpleTestCase):
    def check_configuration(self, overrides=None):
        env = {
            "PATH": os.defpath,
            "DJANGO_LOAD_DOTENV": "0",
            "DJANGO_SETTINGS_MODULE": "settings.production",
            "DJANGO_SECRET_KEY": "configuration-test-0123456789-abcdefghijklmnopqrstuvwxyz-ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            "ALLOWED_HOSTS": "example.com,localhost",
            "SITE_URL": "https://example.com",
            "DB_NAME": "test",
            "DB_USER": "test",
            "DB_PASSWORD": "test-only",
            "DB_HOST": "127.0.0.1",
            "REDIS_URL": "redis://127.0.0.1:6379/0",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        env.update(overrides or {})
        return subprocess.run(
            [sys.executable, "manage.py", "check", "--deploy", "--fail-level", "WARNING"],
            cwd=Path(__file__).resolve().parents[2],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_secure_production_defaults_pass_deployment_checks(self):
        result = self.check_configuration()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_secret_fails_without_printing_other_secrets(self):
        result = self.check_configuration({"DJANGO_SECRET_KEY": "", "DB_PASSWORD": "do-not-print-this"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY is required", result.stderr)
        self.assertNotIn("do-not-print-this", result.stderr)

    def test_weak_secret_fails(self):
        result = self.check_configuration({"DJANGO_SECRET_KEY": "weak"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("strong random production secret", result.stderr)

    def test_wildcard_host_fails(self):
        result = self.check_configuration({"ALLOWED_HOSTS": "*"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("explicit production hosts", result.stderr)

    def test_invalid_proxy_range_fails(self):
        result = self.check_configuration({"TRUSTED_PROXY_CIDRS": "not-a-network"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid network", result.stderr)
