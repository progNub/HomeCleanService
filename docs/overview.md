# HomeService Project Overview

This project is a website based on **Django** and **Wagtail CMS** for providing home care services.

### Core Components:
- **Wagtail CMS**: Used for easy content management (pages, images, settings).
- **Bootstrap 5**: The project uses the Bootstrap framework for styling and interface responsiveness.
- **Django I18N**: Internationalization system supporting multiple languages (Russian and English).
- **init_site.py**: A command for automatic initialization of base content and settings.

### Documentation:
The project includes the following guides:
- [Localization Guide](../locale/README.md) — how to change and add translations.
- [Deployment Guide](DEPLOYMENT.md) — how to launch the project in production.
- [Analytics (Umami)](../deploy/docs/umami.md) — setting up the analytics system.
- [Robots.txt](ROBOTS_TXT.md) — managing indexing.
- **Data Models**: Described in `cms/models/` (settings, pages) and `home/models/` (home page).

### How to Start the Project:
1. Install dependencies.
2. Apply migrations: `python manage.py migrate`.
3. Initialize the site: `python manage.py init_site`.
4. Start the server: `python manage.py runserver`.
