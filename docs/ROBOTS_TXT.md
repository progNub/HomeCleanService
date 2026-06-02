# Robots.txt Configuration

The project manages the `robots.txt` file through the Wagtail Admin panel.

## How to Configure Exceptions

1. Log in to the admin panel (`/admin`).
2. Go to **Settings** -> **Robots Settings**.
3. Add paths you want to hide from indexing (e.g., `/admin/`, `/private/`, `/search/`).
4. Click **Save**.

## Verification

The file is available at: `yourdomain.com/robots.txt`.
All added rules will be output in the format `Disallow: /path/`.
By default, a link to `sitemap.xml` is also automatically added.
