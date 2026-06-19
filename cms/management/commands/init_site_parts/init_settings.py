from django.conf import settings

from cms.models import (
    ContactSettings,
    HomePage,
    MenuItem,
    NavigationSettings,
    SocialMediaSettings,
)


def init_global_settings(command):
    command.stdout.write("Initializing global settings (social and contacts)...")

    # Social Media Settings
    social_settings = SocialMediaSettings.load()
    if not social_settings.social_media_links.exists() and settings.ENV_CONTACT_PHONE:
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
    updated = False

    for field_name, value in (
        ("phone_number", settings.ENV_CONTACT_PHONE),
        ("email", settings.ENV_CONTACT_EMAIL),
        ("address", settings.ENV_CONTACT_ADDRESS),
        ("legal_full_name", settings.ENV_LEGAL_FULL_NAME),
        ("legal_unp", settings.ENV_LEGAL_UNP),
        ("legal_address", settings.ENV_LEGAL_ADDRESS),
        ("legal_reg_date", settings.ENV_LEGAL_REG_DATE),
    ):
        if value and not getattr(contact_settings, field_name):
            setattr(contact_settings, field_name, value)
            updated = True

    # Update legacy demo contact values, but leave real editor changes intact.
    if contact_settings.phone_number == "+7 (900) 123-45-67" and settings.ENV_CONTACT_PHONE:
        contact_settings.phone_number = settings.ENV_CONTACT_PHONE
        updated = True

    if updated:
        contact_settings.save()
        command.stdout.write(command.style.SUCCESS("Contact settings created/updated."))
    else:
        command.stdout.write(command.style.WARNING("Contact settings already exist."))


def init_navigation_settings(command):
    command.stdout.write("Initializing navigation settings...")
    nav_settings = NavigationSettings.load()
    if not nav_settings.menu_items.exists():
        homepage = HomePage.objects.first()

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

        command.stdout.write(command.style.SUCCESS("Navigation settings created with default items."))
    else:
        command.stdout.write(command.style.WARNING("Navigation settings already exist."))
