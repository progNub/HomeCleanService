from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from wagtail.models import Site, Page
from cms.models import HomePage
from cms.models import SocialMediaSettings, ContactSettings

import os
from urllib.parse import urlparse
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
            self.init_superuser()

        if run_all or settings_only:
            self.init_global_settings()

        if run_all or content_only:
            self.init_content()

        self.stdout.write(self.style.SUCCESS("Site initialization finished!"))

    def init_superuser(self):
        username = os.getenv("SUPERUSER_USERNAME")
        email = os.getenv("SUPERUSER_EMAIL")
        password = os.getenv("SUPERUSER_PASSWORD")

        if username and password:
            if not User.objects.filter(username=username).exists():
                self.stdout.write(f"Creating superuser {username}...")
                User.objects.create_superuser(
                    username=username, email=email, password=password
                )
                self.stdout.write(self.style.SUCCESS(f"Superuser {username} created!"))
            else:
                self.stdout.write(
                    self.style.WARNING(f"Superuser {username} already exists.")
                )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "SUPERUSER_USERNAME or SUPERUSER_PASSWORD not found in .env"
                )
            )

    def init_global_settings(self):
        self.stdout.write("Initializing global settings (social and contacts)...")

        # Social Media Settings
        social_settings = SocialMediaSettings.load()
        if not any(
            [
                social_settings.facebook,
                social_settings.instagram,
                social_settings.telegram,
            ]
        ):
            # social_settings.telegram = "https://t.me/homeservice"
            social_settings.whatsapp = "https://wa.me/375296023356"
            # social_settings.instagram = "https://instagram.com/homeservice"
            social_settings.save()
            self.stdout.write(self.style.SUCCESS("Social media settings created."))
        else:
            self.stdout.write(
                self.style.WARNING("Social media settings already exist.")
            )

        # Contact Settings
        contact_settings = ContactSettings.load()
        if not contact_settings.phone_number:
            contact_settings.phone_number = "+375296023356"
            # contact_settings.email = "info@homeservice.by"
            contact_settings.address = "Беларусь"
            contact_settings.save()
            self.stdout.write(self.style.SUCCESS("Contact settings created."))
        else:
            # Let's update it if it's the old default
            if contact_settings.phone_number == "+7 (900) 123-45-67":
                contact_settings.phone_number = "+375296023356"
                contact_settings.email = "info@homeservice.by"
                contact_settings.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        "Contact settings updated with new phone number."
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "Contact settings already exist and differ from old default."
                    )
                )

    def init_content(self):
        # 1. Site configuration from env
        site_url_env = os.getenv("SITE_URL", "http://localhost:8000")
        parsed_url = urlparse(site_url_env)
        hostname = parsed_url.hostname or "localhost"
        port = parsed_url.port
        if not port:
            port = 443 if parsed_url.scheme == "https" else 80

        self.stdout.write(
            f"Configuring site for: {hostname}:{port} (from {site_url_env})"
        )

        # 2. Find or create HomePage
        homepage = HomePage.objects.first()
        if not homepage:
            self.stdout.write("HomePage not found, creating...")
            root_page = Page.objects.get(id=1)
            # Remove default "Home" page if it exists
            Page.objects.filter(slug="home").delete()

            homepage = HomePage(
                title="Главная",
                slug="home",
                seo_title="Мойка и покраска крыш в Беларуси - HomeService",
                search_description="Профессиональная мойка и покраска крыш, фасадов и заборов. Работаем по всей Беларуси. Качество, гарантия, доступные цены.",
                live=True,
            )
            root_page.add_child(instance=homepage)
            homepage.save_revision().publish()
            self.stdout.write(self.style.SUCCESS("HomePage created with SEO tags."))
        else:
            self.stdout.write(self.style.WARNING("HomePage already exists."))
            # Update SEO if empty
            updated = False
            if not homepage.seo_title:
                homepage.seo_title = "Мойка и покраска крыш в Беларуси - HomeService"
                updated = True
            if not homepage.search_description:
                homepage.search_description = "Профессиональная мойка и покраска крыш, фасадов и заборов. Работаем по всей Беларуси. Качество, гарантия, доступные цены."
                updated = True

            if updated:
                homepage.save_revision().publish()
                self.stdout.write(self.style.SUCCESS("HomePage SEO tags updated."))

        # 3. Fill with demo content if body is empty or we want to overwrite/extend
        if not homepage.body:
            self.stdout.write("Filling HomePage with demo content...")
            homepage.body = [
                (
                    "hero",
                    {
                        "title": "Мойка и покраска крыш, домов, заборов",
                        "subtitle": "Моем всё! Профессиональная очистка и обновление вашего имущества. Работаем по всей Беларуси.",
                        "cta_text": "Оставить заявку",
                    },
                ),
                (
                    "services",
                    {
                        "title": "Что мы предлагаем",
                        "items": [
                            {
                                "name": "Мойка крыш",
                                "description": "Удаление мха, лишайника и грязи. Возвращаем крыше первоначальный цвет.",
                            },
                            {
                                "name": "Покраска крыш и фасадов",
                                "description": "Качественная покраска специальными составами для долговечной защиты.",
                            },
                            {
                                "name": "Мойка заборов и мощения",
                                "description": "Очистка тротуарной плитки и любых видов заборов от загрязнений.",
                            },
                        ],
                    },
                ),
                (
                    "features",
                    {
                        "title": "Почему выбирают нас",
                        "items": [
                            {
                                "title": "Опыт и качество",
                                "text": "Используем только проверенные материалы и профессиональное оборудование.",
                            },
                            {
                                "title": "Скорость работы",
                                "text": "Выполняем большинство заказов в течение 1-2 дней.",
                            },
                            {
                                "title": "Гарантия",
                                "text": "Предоставляем гарантию на все виды выполненных работ.",
                            },
                        ],
                    },
                ),
                (
                    "about",
                    {
                        "title": "О нашей компании",
                        "content": "<p>Мы — команда профессионалов, которая занимается комплексным уходом за частными домами и прилегающими территориями уже более 5 лет. Наша миссия — возвращать эстетичный вид вашему имуществу и продлевать срок его службы.</p><p>Мы используем специализированное оборудование высокого давления и экологически безопасные составы для очистки и покраски.</p>",
                        "stats": [
                            {"value": "5+", "label": "лет работы"},
                            {"value": "100+", "label": "объектов"},
                            {"value": "100%", "label": "гарантия"},
                        ],
                    },
                ),
                (
                    "contact_form",
                    {
                        "title": "Свяжитесь с нами",
                        "subtitle": "Оставьте свои контакты, и мы перезвоним вам для консультации.",
                    },
                ),
            ]
            homepage.save_revision().publish()
            self.stdout.write(self.style.SUCCESS("Demo content added to HomePage."))
        else:
            self.stdout.write(
                self.style.WARNING(
                    "HomePage body is not empty. If you want to update content, use Wagtail admin."
                )
            )

        # 4. Configure Site object
        site = Site.objects.filter(is_default_site=True).first() or Site.objects.first()

        if site:
            # Check if we need to update
            if (
                site.hostname != hostname
                or site.port != port
                or site.root_page != homepage
            ):
                self.stdout.write(
                    f"Updating existing site: {site.hostname}:{site.port}"
                )
                site.hostname = hostname
                site.port = port
                site.root_page = homepage
                site.save()
                self.stdout.write(self.style.SUCCESS("Site updated."))
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Site {site.hostname}:{site.port} already correctly configured."
                    )
                )
        else:
            self.stdout.write("Creating new Site object...")
            Site.objects.create(
                hostname=hostname,
                port=port,
                root_page=homepage,
                is_default_site=True,
                site_name="HomeService",
            )
            self.stdout.write(self.style.SUCCESS("Site object created."))
