"""Validate real Compose merging with synthetic settings, without a Docker daemon."""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("docker"), "Docker CLI is required for Compose config checks")
class ComposeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "deploy/certbot").mkdir(parents=True)
        for name in ("docker-compose.yml", "docker-compose.dev.yml", "docker-compose.prod.yml"):
            shutil.copy(ROOT / "deploy" / name, self.root / "deploy" / name)
        shutil.copy(ROOT / "deploy/certbot/docker-compose.yml", self.root / "deploy/certbot")
        # Never resolve the real project's .env, including service env_file entries.
        (self.root / ".env").write_text("APP_ONLY_SENTINEL=not-for-log-viewer\n")
        self.env = {key: os.environ[key] for key in ("PATH", "HOME", "DOCKER_CONFIG") if key in os.environ}
        self.env["HOMESERVICE_ENV_FILE"] = str(self.root / ".env")

    def config(self, mode, *, project=None, secrets=True, all_profiles=True, check=True):
        env = self.env.copy()
        if secrets:
            env.update(
                APP_IMAGE="example.test/app@sha256:" + "a" * 64,
                DB_PASSWORD="synthetic-password",
                UMAMI_APP_SECRET="synthetic-umami-key",
            )
        command = ["docker", "compose", "--env-file", str(self.root / ".env")]
        if project:
            command += ["-p", project]
        command += [
            "-f",
            str(self.root / "deploy/docker-compose.yml"),
            "-f",
            str(self.root / f"deploy/docker-compose.{mode}.yml"),
        ]
        if all_profiles:
            command += ["--profile", "*"]
        command += ["config", "--format", "json"]
        result = subprocess.run(command, env=env, cwd=self.root, capture_output=True, text=True)
        if not check:
            return result
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_dev_starts_only_database_and_redis_without_production_secrets(self):
        config = self.config("dev", secrets=False, all_profiles=False)
        self.assertEqual(set(config["services"]), {"db", "redis"})
        self.assertEqual(config["name"], "homeservice-dev")
        self.assertEqual(config["services"]["db"]["environment"]["POSTGRES_PASSWORD"], "homeservice_pass")

    def test_dev_volumes_ports_and_network_preserve_existing_data_targets(self):
        for project in ("homeservice-dev", "custom-development"):
            with self.subTest(project=project):
                config = self.config("dev", project=project)
                self.assertEqual(config["volumes"]["postgres_data_dev"]["name"], f"{project}_postgres_data_dev")
                self.assertEqual(config["volumes"]["dozzle_data_dev"]["name"], f"{project}_dozzle_data_dev")
                self.assertEqual(set(config["networks"]), {"default"})
                self.assertEqual(config["networks"]["default"]["name"], "homeservice_dev_network")
                for service in config["services"].values():
                    self.assertEqual(set(service["networks"]), {"default"})
                for service, target, source in (
                    ("db", "/var/lib/postgresql/data", "postgres_data_dev"),
                    ("dozzle", "/data", "dozzle_data_dev"),
                ):
                    mounts = [v for v in config["services"][service]["volumes"] if v["target"] == target]
                    self.assertEqual(len(mounts), 1)
                    self.assertEqual(mounts[0]["source"], source)
                for service, port in (("db", "5433"), ("redis", "6380"), ("umami", "3000"), ("dozzle", "8081")):
                    ports = config["services"][service]["ports"]
                    self.assertEqual(len(ports), 1)
                    self.assertEqual((ports[0]["host_ip"], ports[0]["published"]), ("127.0.0.1", port))

    def test_prod_has_no_dev_ports_mounts_builds_or_profiles(self):
        config = self.config("prod", all_profiles=False)
        self.assertEqual(set(config["services"]), {"db", "redis", "web", "worker", "nginx", "umami"})
        for name in ("db", "redis", "web", "worker", "umami"):
            service = config["services"][name]
            self.assertFalse(service.get("ports"))
            self.assertNotIn("build", service)
            self.assertNotIn("container_name", service)
            self.assertNotIn("profiles", service)
        self.assertEqual(config["services"]["web"]["environment"]["DJANGO_SETTINGS_MODULE"], "settings.production")
        self.assertEqual(config["volumes"]["postgres_data"]["name"], "homeservice-prod_postgres_data")
        self.assertEqual(config["networks"]["homeservice_network"]["name"], "homeservice_prod_network")
        self.assertEqual({p["published"] for p in config["services"]["nginx"]["ports"]}, {"80", "443"})

    def test_prod_still_requires_explicit_image_and_secrets(self):
        for missing in ("APP_IMAGE", "DB_PASSWORD", "UMAMI_APP_SECRET"):
            with self.subTest(missing=missing):
                self.env.update(APP_IMAGE="homeservice:fixture", DB_PASSWORD="synthetic", UMAMI_APP_SECRET="synthetic")
                self.env.pop(missing)
                result = self.config("prod", secrets=False, check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(missing, result.stderr)

    def test_shared_infrastructure_is_pinned_and_logs_are_bounded(self):
        dev, prod = self.config("dev"), self.config("prod")
        for name in ("db", "redis", "umami", "dozzle"):
            self.assertEqual(dev["services"][name]["image"], prod["services"][name]["image"])
            self.assertIn("@sha256:", dev["services"][name]["image"])
            self.assertEqual(dev["services"][name]["logging"]["options"]["max-size"], "10m")
        for config in (dev, prod):
            dozzle = config["services"]["dozzle"]["environment"]
            self.assertEqual(dozzle["DOZZLE_AUTH_PROVIDER"], "simple")
            self.assertEqual(dozzle["DOZZLE_ENABLE_ACTIONS"], "false")
            self.assertEqual(dozzle["DOZZLE_ENABLE_SHELL"], "false")
            self.assertNotIn("APP_ONLY_SENTINEL", dozzle)

    def test_certbot_reuses_production_certificate_volumes_and_network(self):
        prod = self.config("prod")
        result = subprocess.run(
            [
                "docker",
                "compose",
                "--env-file",
                str(self.root / ".env"),
                "-p",
                "homeservice-prod",
                "-f",
                str(self.root / "deploy/certbot/docker-compose.yml"),
                "config",
                "--format",
                "json",
            ],
            cwd=self.root,
            env=self.env,
            capture_output=True,
            text=True,
            check=True,
        )
        ssl = json.loads(result.stdout)
        for name in ("certbot-etc", "certbot-var", "webroot"):
            self.assertEqual(ssl["volumes"][name]["name"], prod["volumes"][name]["name"])
        self.assertEqual(
            ssl["networks"]["homeservice_network"]["name"], prod["networks"]["homeservice_network"]["name"]
        )

    def test_make_commands_combine_base_and_environment_and_build_directly(self):
        for target, expected in (("dev-start", "docker-compose.dev.yml"), ("prod-logs", "docker-compose.prod.yml")):
            result = subprocess.run(["make", "-n", target], cwd=ROOT, capture_output=True, text=True, check=True)
            self.assertIn("-f deploy/docker-compose.yml -f deploy/" + expected, result.stdout)
        result = subprocess.run(["make", "-n", "prod-build"], cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertIn("docker build --build-arg RELEASE_REVISION=", result.stdout)
        self.assertNotIn("docker compose", result.stdout)
