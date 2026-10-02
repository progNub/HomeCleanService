from unittest.mock import patch

from django.test import SimpleTestCase, TestCase


class HealthTests(SimpleTestCase):
    def test_liveness_has_no_database_dependency_and_is_not_cached(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(response.json()["status"], "ok")

    @patch("cms.health.connection")
    def test_readiness_fails_without_leaking_errors(self, connection):
        connection.cursor.side_effect = RuntimeError("secret-connection-string")
        response = self.client.get("/ready/")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b"secret", response.content)
        self.assertIn("no-store", response["Cache-Control"])


class ReadyTests(TestCase):
    def test_readiness_checks_available_dependencies(self):
        self.assertEqual(self.client.get("/ready/").status_code, 200)

    @patch("cms.health.cache.get", side_effect=ConnectionError("cache-password"))
    def test_readiness_fails_when_cache_is_unavailable(self, _cache):
        self.assertEqual(self.client.get("/ready/").status_code, 503)
