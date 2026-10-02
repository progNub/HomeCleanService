"""Operations behavior checks with fake Docker; never contact production."""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class OperationsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("deploy/scripts", "deploy/certbot", "bin", "media"):
            (self.root / name).mkdir(parents=True)
        for name in ("backup.sh", "restore.sh"):
            shutil.copy(ROOT / "deploy/scripts" / name, self.root / "deploy/scripts" / name)
        shutil.copy(ROOT / "deploy/certbot/cert-manage.sh", self.root / "deploy/certbot")
        (self.root / ".env").write_text("CERTBOT_EMAIL=ops@example.test\n")
        (self.root / "media/photo.txt").write_text("fixture media")
        self.log = self.root / "docker.log"
        docker = self.root / "bin/docker"
        docker.write_text(
            "#!/bin/bash\n"
            'printf "%s\\n" "$*" >> "$DOCKER_LOG"\n'
            'case "$*" in\n'
            '  *pg_dump*) [[ "${FAIL_DUMP:-0}" != 1 ]] || exit 1; printf "PGDMPfixture";;\n'
            '  *createdb*) [[ "${DB_EXISTS:-0}" != 1 ]] || exit 1;;\n'
            '  *pg_restore*) cat >/dev/null; [[ "${FAIL_RESTORE:-0}" != 1 ]] || exit 1;;\n'
            '  *"certbot renew"*) [[ "${FAIL_RENEW:-0}" != 1 ]] || exit 1;;\n'
            '  *"test -f /etc/letsencrypt"*) [[ "${NO_LINEAGE:-0}" != 1 ]] || exit 1;;\n'
            "esac\n"
        )
        docker.chmod(0o755)
        self.env = os.environ.copy()
        for name in ("BACKUP_GPG_RECIPIENT", "BACKUP_REMOTE_DIR", "HOMESERVICE_ENV_FILE", "MEDIA_DIR", "BACKUP_DIR"):
            self.env.pop(name, None)
        self.env.update(PATH=f"{self.root / 'bin'}:{self.env['PATH']}", DOCKER_LOG=str(self.log))

    def run_script(self, name, *args, **env):
        return subprocess.run(
            ["bash", str(self.root / "deploy" / name), *map(str, args)],
            cwd="/tmp",
            env=self.env | env,
            capture_output=True,
            text=True,
            check=False,
        )

    def backup(self):
        result = self.run_script("scripts/backup.sh", "--local")
        self.assertEqual(result.returncode, 0, result.stderr)
        return next((self.root / "backups").glob("homeservice-*"))

    def test_backup_contains_both_databases_media_and_checksums(self):
        bundle = self.backup()
        self.assertEqual(bundle.stat().st_mode & 0o777, 0o700)
        self.assertEqual((bundle / "db.dump").read_text(), "PGDMPfixture")
        self.assertTrue((bundle / "umami.dump").is_file())
        result = subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=bundle, capture_output=True)
        self.assertEqual(result.returncode, 0)

    def test_scheduled_backup_requires_encrypted_offsite(self):
        result = self.run_script("scripts/backup.sh")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.log.exists())

    def test_dump_failure_is_not_published(self):
        result = self.run_script("scripts/backup.sh", "--local", FAIL_DUMP="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list((self.root / "backups").glob("homeservice-*")), [])

    def install_transfer_stubs(self):
        gpg = self.root / "bin/gpg"
        gpg.write_text(
            '#!/bin/bash\n[[ "${FAIL_GPG:-0}" != 1 ]] || exit 1\n'
            'while [[ $# -gt 0 ]]; do if [[ "$1" == --output ]]; then output=$2; shift; fi; shift; done\n'
            'cat >"$output"\n'
        )
        gpg.chmod(0o755)
        scp = self.root / "bin/scp"
        scp.write_text('#!/bin/bash\n[[ "${FAIL_SCP:-0}" != 1 ]]\n')
        scp.chmod(0o755)

    def test_encryption_failure_is_not_published(self):
        self.install_transfer_stubs()
        result = self.run_script(
            "scripts/backup.sh",
            BACKUP_GPG_RECIPIENT="fixture",
            BACKUP_REMOTE_DIR="backup@example.test:/backups",
            FAIL_GPG="1",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list((self.root / "backups").glob("homeservice-*")), [])

    def test_upload_failure_is_not_published(self):
        self.install_transfer_stubs()
        result = self.run_script(
            "scripts/backup.sh",
            BACKUP_GPG_RECIPIENT="fixture",
            BACKUP_REMOTE_DIR="backup@example.test:/backups",
            FAIL_SCP="1",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list((self.root / "backups").glob("homeservice-*")), [])

    def test_successful_encrypted_upload_publishes_bundle(self):
        self.install_transfer_stubs()
        result = self.run_script(
            "scripts/backup.sh",
            BACKUP_GPG_RECIPIENT="fixture",
            BACKUP_REMOTE_DIR="backup@example.test:/backups",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        bundle = next((self.root / "backups").glob("homeservice-*"))
        self.assertTrue((bundle / "backup.tar.gz.gpg").is_file())

    def test_restore_verifies_checksums_before_database_access(self):
        bundle = self.backup()
        (bundle / "db.dump").write_text("corrupt")
        self.log.unlink()
        result = self.run_script("scripts/restore.sh", "--backup", bundle, "--database", "restore_drill")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.log.exists())

    def test_restore_does_not_touch_existing_database(self):
        bundle = self.backup()
        self.log.unlink()
        result = self.run_script("scripts/restore.sh", "--backup", bundle, "--database", "existing", DB_EXISTS="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("pg_restore", self.log.read_text())

    def test_restore_rejects_manifest_filename_lookalikes(self):
        bundle = self.backup()
        shutil.copy(bundle / "db.dump", bundle / "dbXdump")
        manifest = bundle / "SHA256SUMS"
        manifest.write_text(manifest.read_text().replace("db.dump", "dbXdump"))
        (bundle / "db.dump").write_text("unverified altered dump")
        self.log.unlink()
        result = self.run_script("scripts/restore.sh", "--backup", bundle, "--database", "restore_drill")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.log.exists())

    def test_restore_to_new_database_and_empty_media(self):
        bundle = self.backup()
        target = self.root / "restored-media"
        result = self.run_script(
            "scripts/restore.sh", "--backup", bundle, "--database", "restore_drill", "--media-dir", target
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((target / "photo.txt").read_text(), "fixture media")
        self.assertIn("--single-transaction", self.log.read_text())

    def test_restore_refuses_nonempty_media_before_database_access(self):
        bundle = self.backup()
        self.log.unlink()
        result = self.run_script(
            "scripts/restore.sh", "--backup", bundle, "--database", "restore_drill", "--media-dir", self.root / "media"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.log.exists())

    def test_failed_renewal_does_not_reload_nginx(self):
        result = self.run_script("certbot/cert-manage.sh", "renew", FAIL_RENEW="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("--refresh-certificates", self.log.read_text())

    def test_missing_lineage_does_not_attempt_renewal(self):
        result = self.run_script("certbot/cert-manage.sh", "renew", NO_LINEAGE="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("certbot renew", self.log.read_text())

    def test_dry_run_never_reloads_nginx(self):
        result = self.run_script("certbot/cert-manage.sh", "dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--dry-run", self.log.read_text())
        self.assertNotIn("--refresh-certificates", self.log.read_text())

    def test_nginx_rejects_bad_config_before_reload_and_restores_symlink(self):
        tls = self.root / "letsencrypt/live/homecleanservice.by"
        tls.mkdir(parents=True)
        (tls / "fullchain.pem").write_text("certificate fixture")
        (tls / "privkey.pem").write_text("key fixture")
        runtime = self.root / "run"
        runtime.mkdir()
        active = runtime / "homeservice-tls"
        previous = self.root / "old-certificate"
        active.symlink_to(previous)
        entrypoint = self.root / "deploy/nginx-entrypoint.sh"
        entrypoint.write_text(
            (ROOT / "deploy/nginx/entrypoint/entrypoint.sh")
            .read_text()
            .replace("/etc/letsencrypt", str(self.root / "letsencrypt"))
            .replace("/run/homeservice-tls", str(active))
        )
        nginx = self.root / "bin/nginx"
        nginx.write_text('#!/bin/bash\nprintf "%s\\n" "$*" >> "$DOCKER_LOG"\n[[ "$1" != -t ]]\n')
        nginx.chmod(0o755)
        result = self.run_script("nginx-entrypoint.sh", "--refresh-certificates")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(active.readlink(), previous)
        self.assertNotIn("reload", self.log.read_text())


if __name__ == "__main__":
    unittest.main()
