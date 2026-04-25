from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from wagtail.models import Site, Page
from cms.models import HomePage, FormPage, FormField
from cms.models.seo import SeoAbstract
from cms.models import (
    SocialMediaSettings,
    ContactSettings,
    NavigationSettings,
    MenuItem,
    Review,
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
            self.init_reviews()
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

            whatsapp_phone = (
                os.getenv("CONTACT_PHONE", "375296023356")
                .replace("+", "")
                .replace(" ", "")
                .replace("-", "")
                .replace("(", "")
                .replace(")", "")
            )

            SocialMediaLink.objects.create(
                setting=social_settings,
                platform="whatsapp",
                url=f"https://wa.me/{whatsapp_phone}",
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
            contact_settings.phone_number = os.getenv("CONTACT_PHONE", "+375296023356")
            contact_settings.email = os.getenv("CONTACT_EMAIL", "info@homeservice.by")
            contact_settings.address = os.getenv("CONTACT_ADDRESS", "Беларусь")
            contact_settings.save()
            self.stdout.write(self.style.SUCCESS("Contact settings created."))
        else:
            # Let's update it if it's the old default
            if contact_settings.phone_number == "+7 (900) 123-45-67":
                contact_settings.phone_number = os.getenv(
                    "CONTACT_PHONE", "+375296023356"
                )
                contact_settings.email = os.getenv(
                    "CONTACT_EMAIL", "info@homeservice.by"
                )
                contact_settings.address = os.getenv("CONTACT_ADDRESS", "Беларусь")
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
            contact_page = FormPage.objects.filter(slug="request").first()

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
                MenuItem.objects.create(
                    setting=nav_settings,
                    label="Отзывы",
                    link_url="#reviews",
                    sort_order=4,
                )
                MenuItem.objects.create(
                    setting=nav_settings,
                    label="FAQ",
                    link_url="#faq",
                    sort_order=5,
                )

            if contact_page:
                MenuItem.objects.create(
                    setting=nav_settings,
                    label="Оставить заявку",
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
                og_type=SeoAbstract.OgTypeChoices.WEBSITE,
                meta_robots=SeoAbstract.MetaRobotsChoices.INDEX_FOLLOW,
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
            if not homepage.og_type:
                homepage.og_type = SeoAbstract.OgTypeChoices.WEBSITE
                updated = True
            if not homepage.meta_robots:
                homepage.meta_robots = SeoAbstract.MetaRobotsChoices.INDEX_FOLLOW
                updated = True

            # Update dates if empty
            if not homepage.published_date:
                from django.utils import timezone

                homepage.published_date = homepage.first_published_at or timezone.now()
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
            contact_page = FormPage.objects.filter(slug="request").first()
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
                (
                    "reviews",
                    {
                        "title": "Отзывы наших клиентов",
                        "anchor": "reviews",
                        "reviews": [],
                    },
                ),
                (
                    "faq",
                    {
                        "title": "Часто задаваемые вопросы",
                        "anchor": "faq",
                        "items": [
                            {
                                "question": "Сколько времени занимает мойка крыши?",
                                "answer": "<p>В среднем мойка стандартной крыши занимает от 4 до 8 часов, в зависимости от степени загрязнения и площади.</p>",
                            },
                            {
                                "question": "Безопасна ли покраска для растений вокруг дома?",
                                "answer": "<p>Да, мы используем экологичные составы и при необходимости укрываем растения защитной пленкой.</p>",
                            },
                            {
                                "question": "Как долго держится краска на крыше?",
                                "answer": "<p>При соблюдении технологии нанесения и использовании качественных материалов, покрытие служит от 7 до 12 лет.</p>",
                            },
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

    def init_reviews(self):
        self.stdout.write("Checking for demo reviews...")
        if not Review.objects.exists():
            Review.objects.create(
                author="Александр Е.",
                text="Заказывал мойку и покраску крыши. Ребята приехали вовремя, сделали всё очень аккуратно. Крыша выглядит как новая! Рекомендую.",
                rating=5,
                is_approved=True,
                ip="127.0.0.1",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            Review.objects.create(
                author="Мария С.",
                text="Очень довольна результатом очистки фасада. Все пятна ушли, дом преобразился. Спасибо за профессионализм!",
                rating=5,
                is_approved=True,
                ip="127.0.0.1",
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            Review.objects.create(
                author="Иван Петрович",
                text="Хорошая работа. Быстро, четко и по адекватной цене. Буду обращаться еще.",
                rating=4,
                is_approved=True,
                ip="127.0.0.1",
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            self.stdout.write(self.style.SUCCESS("Demo reviews created."))
        else:
            self.stdout.write(self.style.WARNING("Reviews already exist."))

    def init_contact_form_page(self, homepage):
        """
        Creates a contact form page using Wagtail's AbstractEmailForm
        """
        self.stdout.write("Checking for Contact Form Page...")
        contact_page = (
            FormPage.objects.descendant_of(homepage).filter(slug="request").first()
        )

        if not contact_page:
            self.stdout.write("Creating Request Form Page...")
            contact_page = FormPage(
                title="Заявка",
                slug="request",
                seo_title="Оставить заявку - HomeService",
                search_description="Оставьте заявку на мойку или покраску крыши. Мы перезвоним вам в ближайшее время для уточнения деталей.",
                og_type=SeoAbstract.OgTypeChoices.WEBSITE,
                meta_robots=SeoAbstract.MetaRobotsChoices.INDEX_FOLLOW,
                intro="<p>Пожалуйста, заполните форму ниже, и мы свяжемся с вами в ближайшее время.</p>",
                thank_you_text="<p>Спасибо за вашу заявку! Мы свяжемся с вами скоро.</p>",
                to_address=os.getenv("CONTACT_FORM_TO_EMAIL", "info@homeservice.by"),
                from_address=os.getenv(
                    "CONTACT_FORM_FROM_EMAIL", "noreply@homeservice.by"
                ),
                subject="Новая заявка с сайта",
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
                label="Ваш комментарий",
                field_type="multiline",
                required=False,
                sort_order=2,
            )

            contact_page.save_revision().publish()
            self.stdout.write(self.style.SUCCESS("Request Form Page created."))
        else:
            self.stdout.write(self.style.WARNING("Request Form Page already exists."))

            # Update SEO if empty
            updated = False
            if contact_page.title == "Контакты":
                contact_page.title = "Оставить заявку"
                updated = True
            if (
                not contact_page.seo_title
                or contact_page.seo_title == "Связаться с нами - HomeService"
            ):
                contact_page.seo_title = "Оставить заявку - HomeService"
                updated = True
            if not contact_page.search_description:
                contact_page.search_description = "Оставьте заявку на мойку или покраску крыши. Мы перезвоним вам в ближайшее время для уточнения деталей."
                updated = True
            if not contact_page.og_type:
                contact_page.og_type = SeoAbstract.OgTypeChoices.WEBSITE
                updated = True
            if not contact_page.meta_robots:
                contact_page.meta_robots = SeoAbstract.MetaRobotsChoices.INDEX_FOLLOW
                updated = True

            # Update dates if empty
            if not contact_page.published_date:
                from django.utils import timezone

                contact_page.published_date = (
                    contact_page.first_published_at or timezone.now()
                )
                updated = True

            if updated:
                contact_page.save_revision().publish()
                self.stdout.write(
                    self.style.SUCCESS("Contact Form Page SEO tags updated.")
                )

            if not contact_page.show_in_menus:
                contact_page.show_in_menus = True
                contact_page.save_revision().publish()
                self.stdout.write(
                    self.style.SUCCESS("Contact Form Page set to show in menus.")
                )
