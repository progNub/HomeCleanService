# Umami Analytics Guide

This project uses **Umami**, an open-source, self-hosted analytics system. All statistics are stored in your own PostgreSQL database.

## 1. Accessing the Dashboard
The dashboard is available at:
*   **Development (dev):** `http://stats.localhost`
*   **Production (prod):** `http://stats.your-domain.com`

**Initial login credentials:**
*   **Login:** `admin`
*   **Password:** `umami`

> **Important:** Immediately after your first login, go to **Settings -> Users** and change the administrator password.

## 2. Setting Up a New Website
To start collecting data, follow these steps:
1.  Log in to Umami.
2.  Go to **Settings -> Websites**.
3.  Click **Add website**.
4.  In the **Name** field, enter a name (e.g., `HomeService`).
5.  In the **Domain** field, enter the site domain (for local development, use `localhost` or `127.0.0.1`).
6.  Click **Save**.
7.  Click the **Edit** button (or the `</>` code icon) next to the created site and copy the **Website ID**.

## 3. Connecting to Django
Analytics are managed directly in the Wagtail Admin, supporting multiple sites:
1. Log in to your Wagtail Admin (`/admin`).
2. Go to **Settings -> Analytics Settings**.
3. Select the site you want to configure (if you have multiple sites).
4. Enter your **Umami Website ID** (copied from Umami dashboard).
5. Enter the **Umami Server URL** (e.g., `http://stats.localhost` or `http://stats.your-domain.com`).
6. You can also add any other tracking scripts (like Google Analytics or Yandex.Metrica) in the **Custom Scripts** field.
7. Click **Save**.

The settings take effect immediately without restarting the server. Each site in your Wagtail instance can have its own unique tracking ID.

## 4. Access via Nginx (Subdomain)
For security and convenience, Umami is configured on a separate subdomain:
*   Login address: `http://stats.your-domain.com`
*   Tracker script is available at: `http://stats.your-domain.com/script.js`
This setup is much cleaner than using subfolders and avoids asset path issues.

## 5. Technical Information
*   **Database:** Umami uses a separate database named `umami` inside your shared PostgreSQL container.
*   **Initialization:** The database is created automatically by the `deploy/umami/init-db.sh` script.
*   **Manual Management:** If you need to create the database manually, use the `make db-init-umami` command.
*   **Tracker:** The tracking script is automatically inserted into all pages via the base template `cms/templates/base.html`.

## 6. Troubleshooting
*   **Data not appearing:** Check if AdBlock is disabled for your site in the browser.
*   **404 Error for script.js:** Ensure the `umami` container is running and accessible at the address specified in `UMAMI_SERVER_URL` in Django settings.
*   **Resetting Data:** If you need to completely clear statistics, you can delete the `umami` database and recreate it.
