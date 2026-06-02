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
Analytics are managed directly in the Wagtail Admin:
1. Log in to your Wagtail Admin (`/admin`).
2. Go to **Settings -> Script Settings**.
3. In the **Custom Scripts** section, click **Add**.
4. Give it a name (e.g., "Umami").
5. Paste the tracking code provided by Umami into the **Code** field.
   It should look something like this:
   ```html
   <script defer src="http://stats.your-domain.com/script.js" data-website-id="your-website-id"></script>
   ```
6. Set the **Location** to "Inside <head>".
7. Click **Save**.

The settings take effect immediately.

## 4. Access via Nginx (Subdomain)
For security and convenience, Umami is configured on a separate subdomain:
*   Login address: `http://stats.your-domain.com`
*   Tracker script is available at: `http://stats.your-domain.com/script.js`

## 5. Technical Information
*   **Database:** Umami uses a separate database named `umami` inside your shared PostgreSQL container.
*   **Initialization:** The database is created automatically by the `deploy/umami/init-db.sh` script.
*   **Manual Management:** If you need to create the database manually, use the `make db-init-umami` command.
*   **Tracker:** The tracking script is inserted into pages via the **Custom Scripts** system in **Script Settings**.

## 6. Troubleshooting
*   **Data not appearing:** Check if AdBlock is disabled for your site in the browser.
*   **404 Error for script.js:** Ensure the `umami` container is running and accessible. Check the `src` URL in your custom script code.
*   **Resetting Data:** If you need to completely clear statistics, you can delete the `umami` database and recreate it.
