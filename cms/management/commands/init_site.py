from django.core.management.base import BaseCommand
from cms.management.commands.init_site_parts import (
    init_content,
    init_superuser,
    init_reviews,
    init_legal_pages,
    init_portfolio_pages,
    init_navigation_settings,
    init_global_settings,
)

from dotenv import load_dotenv


class Command(BaseCommand):
    help = "Initializes the site: configures HomePage, Site object, superuser and global settings based on .env"

    def add_arguments(self, parser):
        parser.add_argument(
            "--admin-only",
            action="store_true",
            help="Only create superuser",
        )
        parser.add_argument(
            "--content-only",
            action="store_true",
            help="Only create content (HomePage and Site)",
        )
        parser.add_argument(
            "--settings-only",
            action="store_true",
            help="Only initialize global settings (SocialMedia and Contact)",
        )

    def handle(self, *args, **options):
        load_dotenv()

        admin_only = options["admin_only"]
        content_only = options["content_only"]
        settings_only = options["settings_only"]

        # If no flags are provided, run everything
        run_all = not (admin_only or content_only or settings_only)

        if run_all or admin_only:
            init_superuser(self)

        if run_all or settings_only:
            init_global_settings(self)
            init_navigation_settings(self)

        if run_all or content_only:
            init_reviews(self)
            homepage = init_content(self)
            init_legal_pages(self, homepage)
            init_portfolio_pages(self, homepage)

        self.stdout.write(self.style.SUCCESS("Site initialization finished!"))
