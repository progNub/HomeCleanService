# SSL Configuration Guide (HTTPS)

Now SSL setup is as simple as possible. The entire Nginx configuration already supports HTTPS, and a single command in the `Makefile` is used to obtain certificates.

## 1. Preparation

Ensure that:
1. Your server is accessible from the internet.
2. The domains `homecleanservice.by`, `www.homecleanservice.by`, and `stats.homecleanservice.by` are pointed to your server's IP.
3. Your email is specified in the `.env` file: `CERTBOT_EMAIL=your-email@example.com`.

## 2. Initializing Certificates

To obtain certificates for the first time, run a single command from the project root:

```bash
make cert
```

**What this command does:**
1. Checks if certificates already exist.
2. If not, it runs Certbot to obtain real certificates from Let's Encrypt via HTTP-01 challenge.
3. If certificates exist, it attempts to renew them.
4. Reloads Nginx to apply the certificates.

**Important:** Nginx is configured to automatically create temporary (self-signed) certificates on the first run if real ones haven't been obtained yet. This allows the server to always start successfully and correctly handle Certbot validation requests.

## 3. Manual Renewal

You can renew certificates at any time by running the same command:

```bash
make cert
```

Automatic renewal via Cron was not configured as per preference for manual control.

## 4. How It Works (Technical Details)

*   **Single Config:** We use only one file `deploy/nginx/default.conf`. This prevents conflicts during `git pull`.
*   **Security:** All traffic is automatically redirected from HTTP to HTTPS.
*   **Files:**
    *   `deploy/certbot/docker-compose.yml`: Certbot service configuration.
    *   `deploy/certbot/cert-manage.sh`: Logic for certificate acquisition and renewal.
*   **Logs:** You can check Certbot's output during execution in the console.
