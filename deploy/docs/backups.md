# Backups and recovery

`deploy/scripts/backup.sh` creates PostgreSQL custom-format dumps for the app and
Umami, a media archive and a SHA-256 manifest. It requires Docker Compose, Bash,
`flock`, GNU tar/coreutils, GnuPG and OpenSSH on the host. Database credentials are
read inside the existing database container, never printed or passed on argv.

By default the command requires encryption **and** off-host delivery. Import and
verify the backup recipient's public key in the service user's GnuPG keyring;
keep the matching private key on the recovery machine, not just this server.
Establish trusted SSH host keys and a restricted backup account/key beforehand.
Create the remote destination directory before running a backup. Configure these
variables in the service environment (the application `.env` is not sourced):

```dotenv
COMPOSE_PROJECT_NAME=homeservice-prod
HOMESERVICE_ENV_FILE=/opt/homeservice/.env
BACKUP_DIR=/var/backups/homeservice
BACKUP_GPG_RECIPIENT=VERIFIED_RECIPIENT_KEY_FINGERPRINT
BACKUP_REMOTE_DIR=backup@backup-host:/srv/backups/homeservice
```

Run `bash deploy/scripts/backup.sh`. SSH host verification is strict, scp is
non-interactive and an encryption/upload failure returns a nonzero exit status.
Set `BACKUP_UMAMI=0` only when that database is intentionally absent. `MEDIA_DIR`
defaults to the checkout's `media/`; align it with the deployed bind mount.
Set `GNUPGHOME` when using a dedicated keyring. A `--local` invocation permits
a local-only pre-release snapshot without offsite configuration; it is not a
disaster-recovery backup. If encryption/offsite variables are configured,
`--local` still encrypts and uploads.

Local bundles, including unencrypted dumps, remain on the host with directory
mode `0700` and restrictive file permissions. Failed jobs leave `.incomplete-*`
directories for diagnosis, never a successful bundle name. The default directory
is checkout `backups/`; production should use an external directory so a checkout
replacement does not lose the snapshots. A lock prevents overlapping backups.
PostgreSQL dumps are internally consistent, but DB/media and the two databases
are captured sequentially. For a coordinated restore point, pause application
writes and workers while taking the snapshot (release deployment does this).

## Schedule and retention

Adapt `deploy/systemd/homeservice-backup.service` to your checkout and provision
root-owned mode-0600 `/etc/homeservice/operations.env` using the variables above.
Test the command manually, then install the service/timer in `/etc/systemd/system`
and enable the timer after `systemctl daemon-reload`. The template runs daily;
no service/timer is installed by this repository. Configure failure notification
for the service, monitor backup age/disk space and verify remote receipt. A failed
timer must not silently pass as a successful backup.

Choose retention on the backup host (for example 14 daily and 8 weekly copies)
and restrict the upload key so it cannot delete older copies. Prune local bundles
only after confirming usable offsite copies; this script never deletes backups.
Record the last successful restore drill. Database dumps do not include the TLS
volume, `.env`, Docker registry credentials or SSH keys: keep those separately in
your encrypted operational recovery inventory.

## Restore drill

At least monthly, download an encrypted backup on a recovery host, decrypt into
a fresh private directory, and verify/extract the trusted bundle:

```bash
umask 077
mkdir recovery-bundle
gpg --output recovery.tar.gz --decrypt homeservice-TIMESTAMP.tar.gz.gpg
tar -xzf recovery.tar.gz -C recovery-bundle
bash deploy/scripts/restore.sh --backup /absolute/path/recovery-bundle \
  --database homeservice_restore_drill --media-dir /absolute/path/restored-media
```

The restore script verifies the manifest before contacting Docker, creates only
a **new** explicitly named database and refuses a nonempty media destination.
An existing database makes `createdb` fail without restoring anything. Restore
uses one transaction and stops on SQL errors; a failed new database is retained
for inspection. For Umami, use another new database name and `--umami`.

Point an isolated application instance at the restored database/media, run Django
checks and inspect pages, uploaded images, Wagtail login and representative data.
Disable outgoing notifications on the drill instance. Record backup timestamp,
row counts, tested pages and elapsed recovery time. Script tests alone do not
prove a real restore works.

For production recovery, first stop writers, preserve the current database/media,
restore into new targets, validate them, and explicitly switch application
configuration to those targets. This script deliberately does not drop, rename,
replace or automatically promote the production database. Restart web/workers
only after review of the restored state and configuration.
