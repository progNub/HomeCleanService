from django.conf import settings

from cms.models import (
    ContactSettings,
    FormPage,
    HomePage,
    MenuItem,
    NavigationSettings,
    SocialMediaSettings,
)


def init_global_settings(command):
    command.stdout.write("Initializing global settings (social and contacts)...")

    # Social Media Settings
    social_settings = SocialMediaSettings.load()
    if not social_settings.social_media_links.exists():
        MenuItem.objects.filter()  # Just to have it in scope if needed, but not really
        from cms.models import SocialMediaLink

        whatsapp_phone = (
            settings.ENV_CONTACT_PHONE.replace("+", "")
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
        command.stdout.write(command.style.SUCCESS("Social media settings created."))
    else:
        command.stdout.write(command.style.WARNING("Social media settings already exist."))

    # Contact Settings
    contact_settings = ContactSettings.load()
    if not contact_settings.phone_number or not contact_settings.legal_unp:
        contact_settings.phone_number = settings.ENV_CONTACT_PHONE
        contact_settings.email = settings.ENV_CONTACT_EMAIL
        contact_settings.address = settings.ENV_CONTACT_ADDRESS

        # Legal info
        contact_settings.legal_full_name = settings.ENV_LEGAL_FULL_NAME
        contact_settings.legal_unp = settings.ENV_LEGAL_UNP
        contact_settings.legal_address = settings.ENV_LEGAL_ADDRESS
        contact_settings.legal_reg_date = settings.ENV_LEGAL_REG_DATE

        contact_settings.save()
        command.stdout.write(command.style.SUCCESS("Contact settings created/updated."))
    else:
        # Let's update it if it's the old default
        if contact_settings.phone_number == "+7 (900) 123-45-67":
            contact_settings.phone_number = settings.ENV_CONTACT_PHONE
            contact_settings.email = settings.ENV_CONTACT_EMAIL
            contact_settings.address = settings.ENV_CONTACT_ADDRESS
            contact_settings.save()
            command.stdout.write(command.style.SUCCESS("Contact settings updated with new phone number."))
        else:
            command.stdout.write(command.style.WARNING("Contact settings already exist and differ from old default."))


def init_navigation_settings(command):
    command.stdout.write("Initializing navigation settings...")
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

        command.stdout.write(command.style.SUCCESS("Navigation settings created with default items."))
    else:
        command.stdout.write(command.style.WARNING("Navigation settings already exist."))
