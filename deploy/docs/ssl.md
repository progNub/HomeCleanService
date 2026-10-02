# HTTPS certificates

The production Nginx serves HTTP-01 challenges from the shared `webroot` volume.
Point every name in `CERTBOT_DOMAINS` to this host and allow inbound TCP 80/443.
The default names are `homecleanservice.by`, `www.homecleanservice.by`,
`stats.homecleanservice.by`, and `logs.homecleanservice.by`; remove unused names
before issuance. Set `CERTBOT_EMAIL` and optionally comma-separated
`CERTBOT_DOMAINS` in the production `.env` (simple values, optionally quoted).

## First issuance and renewal

Start production Nginx, then run:

```bash
bash deploy/certbot/cert-manage.sh init
bash deploy/certbot/cert-manage.sh dry-run
```

`init` obtains/expands the named lineage. `renew` only renews an existing lineage;
it fails if renewal metadata is absent. `dry-run` uses Certbot's staging renewal
test and does not reload Nginx. Normal renewal:

```bash
bash deploy/certbot/cert-manage.sh renew
```

Scripts discover the checkout root, use `.runtime/cert.lock` to avoid overlapping
runs and default to project `homeservice-prod`. For another installation export
`COMPOSE_PROJECT_NAME` and an absolute `HOMESERVICE_ENV_FILE`. Keep the same project
name used to create the existing certificate volumes.

Bootstrap self-signed certificates are stored separately at
`/etc/letsencrypt/bootstrap/homecleanservice.by`. Nginx uses a runtime symlink
`/run/homeservice-tls` to either bootstrap files or the existing real lineage
`/etc/letsencrypt/live/homecleanservice.by`. Refresh switches the symlink, tests
the Nginx configuration and only then reloads; a failed test restores the previous
symlink. The running Nginx process keeps its loaded certificate if renewal fails.

## Existing dummy or damaged lineages

The scripts never delete `live`, `archive`, or `renewal` files. If an old version
put dummy certificates into `live/homecleanservice.by` without renewal metadata,
`init` stops rather than guessing. Back up the entire certificate volume first,
inspect certificate subject/issuer/dates and the renewal metadata, and check
`certbot certificates`. For a confirmed old dummy only, move the conflicting
directory to a timestamped recovery location inside the volume before retrying
`init`. Preserve all real or uncertain lineages, including `-0001` suffixed ones;
repair them from the backup or select their correct metadata manually. Never
delete a lineage to resolve an issuance error.

## Optional schedule

The files in `deploy/systemd/` are templates, not automatically installed.
Adjust `/opt/homeservice` in the services to the deployment checkout and create
root-owned `/etc/homeservice/operations.env` with mode `0600`:

```dotenv
COMPOSE_PROJECT_NAME=homeservice-prod
HOMESERVICE_ENV_FILE=/opt/homeservice/.env
```

After a successful manual `dry-run`, install the certificate service/timer into
`/etc/systemd/system`, run `systemctl daemon-reload`, then enable
`homeservice-cert-renew.timer`. It runs twice daily with random delay and catches
missed runs after reboot. Monitor service failures and certificate expiry through
your existing monitoring; a timer alone does not notify an operator. Inspect
`journalctl -u homeservice-cert-renew.service` and `systemctl list-timers`.
