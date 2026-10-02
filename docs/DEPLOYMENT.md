# Deployment and rollback

The production stack runs on one Docker host: Nginx, web, task worker, PostgreSQL,
Redis and Umami. Web/worker run the same prebuilt image as UID 1000. Node, Sass,
dependency resolution and collectstatic run during image creation; migrations and
publishing static files run once per release.

## Server prerequisites

Install Docker with Compose v2 (up --wait support), Git, Make, Bash, Python 3,
curl and flock. Backups additionally use tar, GnuPG and OpenSSH. The deployment
account needs Docker access and a writable checkout. Keep the existing Compose
project name (homeservice-prod by default) so its database/certificate volumes
remain attached.

Copy deploy/production.env.example to server .env and restrict it to mode 0600.
Supply a strong random DJANGO_SECRET_KEY (at least 50 characters), database
password and UMAMI_APP_SECRET; use a URL-safe database password because Umami
embeds it in DATABASE_URL. Set explicit allowed hosts, HTTPS SITE_URL, HTTPS CSRF
origins and certificate email/domains. Telegram settings are optional unless
notifications are required. Never commit this file or include it in images.

The supplied Nginx configuration and certificate lineage target
homecleanservice.by, www.homecleanservice.by and stats.homecleanservice.by.
For another domain, change Nginx and certificate scripts together; SITE_URL alone
does not reconfigure them. Point every requested certificate name to this host and
expose ports 80/443. The old logs.* host now returns 404; omit it from
CERTBOT_DOMAINS when no longer used.

Create bind-mounted media/ and staticfiles/ directories before deploying. They
must be writable by container UID/GID 1000. On an existing installation, inspect
ownership and adjust only those exact directories and their contents; keep a
backup of uploads first. For a fresh checkout:

```bash
sudo install -d -o 1000 -g 1000 -m 0755 media staticfiles
```

Set the image explicitly for the following operations:

```bash
export APP_IMAGE=ghcr.io/OWNER/REPOSITORY@sha256:IMAGE_DIGEST
```

Use the actual lower-case registry path and full digest from the successful build.
Also record the digest as APP_IMAGE in server .env, so scheduled/manual Compose
commands can resolve it. release.sh requires the exported value; it deliberately
does not execute .env as a shell script. For another env file, export its absolute
path as HOMESERVICE_ENV_FILE.

Start just infrastructure to discover its network:

```bash
docker compose --env-file .env -p homeservice-prod -f deploy/docker-compose.yml up -d --wait db redis
docker network inspect homeservice_prod_network --format '{{range .IPAM.Config}}{{println .Subnet}}{{end}}'
```

Put the actual subnet(s), comma-separated, into TRUSTED_PROXY_CIDRS. Do not trust
all private networks or 0.0.0.0/0: Django accepts forwarded client IPs only from
these peers. Recheck after recreating the Docker network. Nginx overwrites incoming
forwarded headers, and the web port is not published to the host.

## First installation

Check out the exact Git commit used to build the image. Its
org.opencontainers.image.revision label must match checkout HEAD.

```bash
make prod-init
docker compose --env-file .env -p homeservice-prod -f deploy/docker-compose.yml exec web python manage.py init_site
make prod-superuser
make cert-init
make cert-dry-run
make prod-smoke
```

prod-init is for an empty installation: it runs migrations and starts the stack,
but skips pre-release backup and external HTTPS smoke because content/TLS may not
exist yet. init_site explicitly seeds content/settings; inspect its defaults
before invoking it. If SUPERUSER_* already created an administrator, skip
prod-superuser. Review the Wagtail Site hostname, seeded pages and navigation.

Nginx can initially use a separate self-signed bootstrap certificate. cert-init
issues the trusted certificate and switches Nginx after a config test. The site
is ready only after final HTTPS smoke succeeds.

## Migration from server-side builds

Before the first new release, back up database, media, .env and certificate volume.
Preserve deployment path, Compose project name and existing volumes; do not use
down -v. Fill newly required env values, check directory ownership and proxy CIDR,
and provision image registry access before the maintenance window.

Existing valid certificates remain in their current lineage. If an old bootstrap
left a dummy live/homecleanservice.by directory without renewal metadata, issuance
stops. Back up the certificate volume, inspect subject/issuer/dates and certbot
certificates, then move only the confirmed dummy directory to a recovery location
before retrying. Preserve real or uncertain lineages; see
[certificate recovery](../deploy/docs/ssl.md).

## CI and registry setup

The workflow runs checks for pull requests and pushes to dev/master. Checks cover
PostgreSQL tests, Python style, npm assets and the production image. An isolated
container smoke also checks migrations, Nginx bootstrap HTTPS, DB/Redis readiness,
public HTML and static assets without real credentials or external providers. Publishing
to GHCR and SSH deployment require an explicit workflow_dispatch run on master
with deploy=true; ordinary pushes and PR checks do not publish or deploy.
Enable Actions package-write permissions for that manual run. For a
private package, provision registry login on the server under the deployment
account with pull-only read:packages access. Keep credentials outside Git and
verify trusted SSH host keys and repository read access separately.

Configure these GitHub secrets: SSH_HOST, SSH_USER, SSH_KEY, SSH_FINGERPRINT.
Set repository variable DEPLOY_PATH to the absolute server checkout path (for
example /home/deploy/HomeCleanService, not a tilde-relative path). Configure the
production GitHub environment; optional required reviewers are an operator choice.

After provisioning these settings, open the workflow's Run workflow action,
select master and enable the deploy input for an intended production release.

The deployment fetches master, checks the tracked tree is clean, checks out the
exact workflow commit in detached mode, and passes APP_IMAGE digest plus
RELEASE_REVISION to release.sh. The image label must agree with that revision.
No server-side build or moving branch tip selects the deployed application.

Do not mix the old git-pull/build procedure with the new flow: prod-start already
performs the single release step. Keep the previous tested image and matching
source revision available for rollback. Record an initial image digest in server
.env for standalone certificate/backup Compose commands.

## Normal release

With a clean checkout at the image's exact commit and APP_IMAGE exported:

```bash
make prod-start
```

The script locks releases, checks image revision, configuration, database/Redis
readiness and directory ownership. It stops web/worker, creates a local
DB/media snapshot, runs migrations, copies precompiled assets and clears cache.
Web/worker start again; Nginx reloads its upstream and external HTTPS checks verify
readiness/revision, homepage and assets. prod-up does the same then follows logs.
Expect a short maintenance window; Nginx may return 502 while web is stopped.

The snapshot is local unless offsite backup variables are configured. Set
BACKUP_GPG_RECIPIENT and BACKUP_REMOTE_DIR in the process/service environment for
encrypted off-host delivery. prod-db-backup requires both; the explicit
prod-backup-local permits a local snapshot. See
[backups and restore drills](../deploy/docs/backups.md) for schedules and recovery.

init_site never runs on regular releases. prod-migrate manually runs the release
job and is not a second required deployment step; stop writers and back up first.
Do not prune previous release images immediately after deployment.

## Failure and rollback

Read the release error and prod-logs-web. Failures before migrations may restart
the existing web/worker. After migration execution begins, the script does not
automatically revert code/schema: inspect database state before restarting or
deploying another image. A failed smoke leaves the new release running for
inspection. deploy/.release/ records the last successful current and previous
image references, not a transactional rollback of the database.

Rollback requires proving the old application works with the current schema.
Check out its matching revision and use its retained digest:

```bash
export APP_IMAGE=ghcr.io/OWNER/REPOSITORY@sha256:PREVIOUS_IMAGE_DIGEST
ROLLBACK_DB_COMPATIBLE=1 make prod-rollback
```

Rollback backs up current state, restores that image's assets, clears cache and
restarts/verifies services. It never reverses migrations or restores old data.
For incompatible schema/data changes, restore into new targets and validate them
before switching production configuration.

## Local image testing and operations

make prod-build builds homeservice:local with the checkout revision label.
ALLOW_LOCAL_IMAGE=1 APP_IMAGE=homeservice:local make prod-start explicitly allows
a local tag; this skips digest/revision enforcement and is not the CI production
path. An empty local installation uses prod-init first and still needs production
env/permissions; normal release smoke requires trusted HTTPS.

Install backup/certificate timers only after manual tests and adjusting paths in
deploy/systemd/. No timers are installed automatically. Monitor failed jobs,
certificate expiry, backup age and disk space; periodically restore a backup.
Dozzle is optional and private: [SSH access instructions](LOGS.md).

The main site's CSP enforces basic framing/object restrictions; its detailed
resource policy is Report-Only while CMS analytics and Wagtail flows are checked.
Inspect browser CSP messages/configured scripts before enforcing it fully.
