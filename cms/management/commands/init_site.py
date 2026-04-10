from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from wagtail.models import Site, Page
from cms.models import HomePage, FormPage, FormField
from cms.models import (
    SocialMediaSettings,
    ContactSettings,
    NavigationSettings,
    MenuItem,
)

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

        if run_all or content_only:
            self.init_content()

        if run_all or settings_only:
            self.init_global_settings()
            self.init_navigation_settings()

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
        if not social_settings.social_media_links.exists():
            MenuItem.objects.filter()  # Just to have it in scope if needed, but not really
            from cms.models import SocialMediaLink

            SocialMediaLink.objects.create(
                setting=social_settings,
                platform="whatsapp",
                url="https://wa.me/375296023356",
                sort_order=0,
            )
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

    def init_navigation_settings(self):
        self.stdout.write("Initializing navigation settings...")
        nav_settings = NavigationSettings.load()
        if not nav_settings.menu_items.exists():
            homepage = HomePage.objects.first()
            contact_page = FormPage.objects.filter(slug="contact-us").first()

            if homepage:
                MenuItem.objects.create(
                    setting=nav_settings,
                    label="Главная",
                    link_page=homepage,
                    sort_order=0,
                )
                MenuItem.objects.create(
                    setting=nav_settings,
                    label="Услуги",
                    link_url="#services",
                    sort_order=1,
                )
                MenuItem.objects.create(
                    setting=nav_settings,
                    label="Преимущества",
                    link_url="#features",
                    sort_order=2,
                )
                MenuItem.objects.create(
                    setting=nav_settings,
                    label="О нас",
                    link_url="#about-us",
                    sort_order=3,
                )

            if contact_page:
                MenuItem.objects.create(
                    setting=nav_settings,
                    label="Связаться с нами",
                    link_page=contact_page,
                    sort_order=4,
                )

            self.stdout.write(
                self.style.SUCCESS("Navigation settings created with default items.")
            )
        else:
            self.stdout.write(self.style.WARNING("Navigation settings already exist."))

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
                show_in_menus=True,
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

            # Ensure homepage is in menu
            if not homepage.show_in_menus:
                homepage.show_in_menus = True
                homepage.save_revision().publish()
                self.stdout.write(self.style.SUCCESS("HomePage set to show in menus."))

        # 2.5 Ensure Contact Form Page exists before filling content
        self.init_contact_form_page(homepage)

        # 3. Fill with demo content if body is empty or we want to overwrite/extend
        if not homepage.body:
            contact_page = FormPage.objects.filter(slug="contact-us").first()
            self.stdout.write("Filling HomePage with demo content...")
            homepage.body = [
                (
                    "hero",
                    {
                        "title": "Мойка и покраска крыш, домов, заборов",
                        "subtitle": "Моем всё! Профессиональная очистка и обновление вашего имущества. Работаем по всей Беларуси.",
                        "cta_text": "Связаться с нами",
                        "cta_page": contact_page,
                        "anchor": "hero",
                    },
                ),
                (
                    "services",
                    {
                        "title": "Что мы предлагаем",
                        "anchor": "services",
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
                        "anchor": "features",
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
                        "anchor": "about-us",
                        "content": "<p>Мы — команда профессионалов, которая занимается комплексным уходом за частными домами и прилегающими территориями уже более 5 лет. Наша миссия — возвращать эстетичный вид вашему имуществу и продлевать срок его службы.</p><p>Мы используем специализированное оборудование высокого давления и экологически безопасные составы для очистки и покраски.</p>",
                        "stats": [
                            {"value": "5+", "label": "лет работы"},
                            {"value": "100+", "label": "объектов"},
                            {"value": "100%", "label": "гарантия"},
                        ],
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

        return homepage

    def init_contact_form_page(self, homepage):
        """
        Creates a contact form page using Wagtail's AbstractEmailForm
        """
        self.stdout.write("Checking for Contact Form Page...")
        contact_page = (
            FormPage.objects.descendant_of(homepage).filter(slug="contact-us").first()
        )

        if not contact_page:
            self.stdout.write("Creating Contact Form Page...")
            contact_page = FormPage(
                title="Контакты",
                slug="contact-us",
                intro="<p>Пожалуйста, заполните форму ниже, и мы свяжемся с вами в ближайшее время.</p>",
                thank_you_text="<p>Спасибо за ваше сообщение! Мы свяжемся с вами скоро.</p>",
                to_address="info@homeservice.by",  # Значение по умолчанию
                from_address="noreply@homeservice.by",
                subject="Новое сообщение с сайта",
                show_in_menus=True,
            )
            homepage.add_child(instance=contact_page)
            contact_page.save_revision().publish()

            # Add form fields
            FormField.objects.create(
                page=contact_page,
                label="Ваше имя",
                field_type="singleline",
                required=True,
                sort_order=0,
            )
            FormField.objects.create(
                page=contact_page,
                label="Телефон",
                field_type="singleline",
                required=True,
                sort_order=1,
            )
            FormField.objects.create(
                page=contact_page,
                label="Email",
                field_type="email",
                required=False,
                sort_order=2,
            )
            FormField.objects.create(
                page=contact_page,
                label="Ваш комментарий",
                field_type="multiline",
                required=False,
                sort_order=3,
            )

            contact_page.save_revision().publish()
            self.stdout.write(self.style.SUCCESS("Contact Form Page created."))
        else:
            self.stdout.write(self.style.WARNING("Contact Form Page already exists."))
            if not contact_page.show_in_menus:
                contact_page.show_in_menus = True
                contact_page.save_revision().publish()
                self.stdout.write(
                    self.style.SUCCESS("Contact Form Page set to show in menus.")
                )
