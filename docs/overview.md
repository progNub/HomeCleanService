# HomeService overview

HomeService is a small Django/Wagtail website for home-care services. Wagtail
pages and StreamField blocks own content; Django templates render HTML.
Bootstrap, SCSS and a few JavaScript files provide responsive UI and interactions.
There is no separate frontend application or production Node process.

PostgreSQL stores content, submissions and database-backed background tasks.
The task worker sends notifications. Redis provides production caching; local
development uses an in-memory cache. Nginx terminates HTTPS and serves static and
uploaded files. Umami is a separate analytics container on the same Docker host.

| Area | Location |
| --- | --- |
| Pages, blocks and settings | cms/models/, cms/blocks/ |
| Forms and request validation | cms/forms.py, cms/views.py, cms/models/pages/forms/ |
| Integrations and queued logging | cms/services/, cms/logging/ |
| Templates, SCSS and JS | cms/templates/, cms/static/cms/ |
| Asset build | scripts/build-assets.mjs, package-lock.json |
| Runtime configuration | settings/ |
| Production and operations | deploy/ |

Dependencies install from uv.lock and package-lock.json. The image contains
precompiled/collected static files. Startup launches only its process; deployment
runs migrations once, and init_site explicitly initializes content on first
installation. Production uses an image digest plus matching Git revision, a short
maintenance window, backup and HTTPS checks.

- [Development and checks](../README.md)
- [Deployment and rollback](DEPLOYMENT.md)
- [Backups and recovery](../deploy/docs/backups.md)
- [Certificates](../deploy/docs/ssl.md)
- [Private log viewer](LOGS.md)
- [Analytics](../deploy/docs/umami.md)
- [Localization](../locale/README.md)
- [Robots.txt](ROBOTS_TXT.md)
