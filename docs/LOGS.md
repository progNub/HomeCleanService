# Log Viewer Guide (Dozzle)

The project uses **Dozzle**, a lightweight, real-time log viewer for Docker containers.

## 1. Accessing the Log Viewer

The log viewer is available at:
*   **Development (dev):** `http://localhost:8081`
*   **Production (prod):** `https://logs.homecleanservice.by`

## 2. Features

*   **Real-time streaming:** View logs as they happen without refreshing.
*   **Search:** Filter logs by keyword.
*   **Multiple containers:** View logs from all running containers in the stack (Web, DB, Redis, Umami, Nginx).
*   **Download:** Easily download log files for further analysis.

## 3. Configuration

### Production
In production, Dozzle is protected by Nginx and exposed via a subdomain.
The configuration is located in `deploy/docker-compose.yml` and `deploy/nginx/default.conf`.

### Security
Starting from v10, Dozzle supports several authentication methods. In this project, we use **File-Based User Management** (`simple` provider).

The user configuration is stored in `deploy/dozzle/users.yml`. This file is passed to the container using **Docker Secrets** and is available at `/data/users.yml`.

**Note:** The `deploy/dozzle/users.yml` file is ignored by Git to prevent leaking sensitive credentials. A sample file `deploy/dozzle/users.yml.example` can be found in the repository.

#### Adding/Modifying Users
1.  **Generate a bcrypt password hash** using the Makefile:
    ```bash
    make dozzle-gen-pass USER=admin PASS=your_secure_password
    ```
    *If the `users.yml` file is missing, the system will automatically generate it during the first `make dev-up` or `make prod-up` call using default or provided environment variables.*

2.  **Copy the generated hash** and paste it into `deploy/dozzle/users.yml`.
3.  **Restart the Dozzle container** to apply changes:
    ```bash
    # Prod
    make prod-up
    # Dev
    make dev-up
    ```

Example of `users.yml` structure:
```yaml
users:
  admin:
    name: Admin
    password: $2a$11$9ho4vY2LdJ/WBopFcsAS0uORC0x2vuFHQgT/yBqZyzclhHsoaIkzK # "admin"
    roles: all
```

**Note:** If you don't want authentication (e.g., for local testing), you can set `DOZZLE_AUTH_PROVIDER=none` in the environment variables, but this is strictly forbidden for production.

## 4. Troubleshooting

*   **Logs not showing:** Ensure the Dozzle container has access to `/var/run/docker.sock`.
*   **404/502 Error:** Check if the `dozzle` container is running (`docker ps`) and if Nginx is correctly configured to proxy to it.
