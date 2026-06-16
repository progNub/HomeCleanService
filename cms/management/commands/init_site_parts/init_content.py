import os
from urllib.parse import urlparse

from django.conf import settings
from django.core.files import File
from wagtail.images.models import Image
from wagtail.models import Page, Site

from cms.blocks.base.blocks import BackgroundColorChoices, PaddingVerticalChoices
from cms.models import FormPage, HomePage
from cms.models.seo import SeoAbstract

from .init_forms import init_contact_form_page


def get_or_import_image(image_path, title):
    if not os.path.exists(image_path):
        return None

    image = Image.objects.filter(title=title).first()
    if not image:
        with open(image_path, "rb") as f:
            image = Image.objects.create(title=title, file=File(f, name=os.path.basename(image_path)))
    return image


def init_content(command):
    # 1. Site configuration from env
    site_url_env = settings.ENV_SITE_URL
    parsed_url = urlparse(site_url_env)
    hostname = parsed_url.hostname or "localhost"
    port = parsed_url.port
    if not port:
        port = 443 if parsed_url.scheme == "https" else 80

    command.stdout.write(f"Configuring site for: {hostname}:{port} (from {site_url_env})")

    get_or_import_image("cms/static/cms/images/logo/logo.png", "Логотип HomeCleanService")
    hero_img = get_or_import_image("cms/static/cms/images/default/hero_1.webp", "Главное изображение")

    # 2. Find or create HomePage
    homepage = HomePage.objects.first()
    if not homepage:
        command.stdout.write("HomePage not found, creating...")
        root_page = Page.objects.get(id=1)
        # Remove default "Home" page if it exists
        Page.objects.filter(slug="home").delete()

        homepage = HomePage(
            title="Главная",
            slug="home",
            seo_title="Мойка и покраска крыш в Беларуси - HomeCleanService",
            search_description="Профессиональная мойка и покраска крыш, фасадов и заборов. Работаем по всей Беларуси. Качество, гарантия, доступные цены.",
            og_image=hero_img,
            og_type=SeoAbstract.OgTypeChoices.WEBSITE,
            meta_robots=SeoAbstract.MetaRobotsChoices.INDEX_FOLLOW,
            live=True,
            show_in_menus=True,
        )
        root_page.add_child(instance=homepage)
        homepage.save_revision().publish()
        command.stdout.write(command.style.SUCCESS("HomePage created with SEO tags."))
    else:
        command.stdout.write(command.style.WARNING("HomePage already exists."))
        # Update SEO if empty
        updated = False
        if not homepage.seo_title:
            homepage.seo_title = "Мойка и покраска крыш в Беларуси - HomeCleanService"
            updated = True
        if not homepage.search_description:
            homepage.search_description = "Профессиональная мойка и покраска крыш, фасадов и заборов. Работаем по всей Беларуси. Качество, гарантия, доступные цены."
            updated = True
        if not homepage.og_image and hero_img:
            homepage.og_image = hero_img
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
            command.stdout.write(command.style.SUCCESS("HomePage SEO tags updated."))

        # Ensure homepage is in menu
        if not homepage.show_in_menus:
            homepage.show_in_menus = True
            homepage.save_revision().publish()
            command.stdout.write(command.style.SUCCESS("HomePage set to show in menus."))

    # 2.5 Ensure Contact Form Page exists before filling content
    init_contact_form_page(command, homepage)

    # 3. Fill with demo content if body is empty or we want to overwrite/extend
    if not homepage.body:
        contact_page = FormPage.objects.filter(slug="request").first()

        # Import services images
        roof_img = get_or_import_image("cms/static/cms/images/default/roof_washing.webp", "Мойка крыши")
        house_img = get_or_import_image("cms/static/cms/images/default/house_painting.webp", "Покраска дома")
        fence_img = get_or_import_image("cms/static/cms/images/default/fence_washing.webp", "Мойка забора")
        command.stdout.write("Filling HomePage with demo content...")
        homepage.body = [
            (
                "hero",
                {
                    "title": "Мойка и покраска крыш, домов, заборов",
                    "subtitle": "Моем всё! Профессиональная очистка и обновление вашего имущества. Работаем по всей Беларуси.",
                    "image": hero_img,
                    "cta_text": "Связаться с нами",
                    "cta_page": contact_page,
                    "anchor": "hero",
                    "padding_vertical": PaddingVerticalChoices.PY_5,
                },
            ),
            (
                "services",
                {
                    "title": "Что мы предлагаем",
                    "anchor": "services",
                    "background_color": BackgroundColorChoices.TERTIARY,
                    "items": [
                        {
                            "name": "Мойка крыш",
                            "description": "Удаление мха, лишайника и грязи. Возвращаем крыше первоначальный цвет.",
                            "image": roof_img,
                        },
                        {
                            "name": "Покраска крыш и фасадов",
                            "description": "Качественная покраска специальными составами для долговечной защиты.",
                            "image": house_img,
                        },
                        {
                            "name": "Мойка заборов и мощения",
                            "description": "Очистка тротуарной плитки и любых видов заборов от загрязнений.",
                            "image": fence_img,
                        },
                    ],
                },
            ),
            (
                "features",
                {
                    "title": "Почему выбирают нас",
                    "anchor": "features",
                    "background_color": BackgroundColorChoices.DEFAULT,
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
                    "background_color": BackgroundColorChoices.TERTIARY,
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
                    "background_color": BackgroundColorChoices.SECONDARY,
                    "reviews": [],
                },
            ),
            (
                "faq",
                {
                    "title": "Часто задаваемые вопросы",
                    "anchor": "faq",
                    "background_color": BackgroundColorChoices.TERTIARY,
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
        command.stdout.write(command.style.SUCCESS("Demo content added to HomePage."))
    else:
        command.stdout.write(
            command.style.WARNING("HomePage body is not empty. If you want to update content, use Wagtail admin.")
        )

    # 4. Configure Site object
    site = Site.objects.filter(is_default_site=True).first() or Site.objects.first()

    if site:
        # Check if we need to update
        if site.hostname != hostname or site.port != port or site.root_page != homepage:
            command.stdout.write(f"Updating existing site: {site.hostname}:{site.port}")
            site.hostname = hostname
            site.port = port
            site.root_page = homepage
            site.save()
            command.stdout.write(command.style.SUCCESS("Site updated."))
        else:
            command.stdout.write(
                command.style.WARNING(f"Site {site.hostname}:{site.port} already correctly configured.")
            )
    else:
        command.stdout.write("Creating new Site object...")
        Site.objects.create(
            hostname=hostname,
            port=port,
            root_page=homepage,
            is_default_site=True,
            site_name="HomeCleanService",
        )
        command.stdout.write(command.style.SUCCESS("Site object created."))

    return homepage
