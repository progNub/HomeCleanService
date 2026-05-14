from wagtail.models import Page
from cms.models.seo import SeoAbstract
from cms.models import (
    ContactSettings,
    LegalIndexPage,
    LegalDocumentPage,
)


def init_legal_pages(command, homepage):
    """
    Creates a 'Legal' parent page and nested legal documents.
    """
    command.stdout.write("Checking for Legal Pages...")

    # 1. Create Legal parent page if it doesn't exist
    legal_parent = (
        LegalIndexPage.objects.descendant_of(homepage).filter(slug="legal").first()
    )
    if not legal_parent:
        # Check if it exists but as a plain Page (from previous init)
        existing_plain = (
            Page.objects.descendant_of(homepage).filter(slug="legal").first()
        )
        if existing_plain:
            command.stdout.write("Deleting existing plain Legal page...")
            existing_plain.delete()

        command.stdout.write("Creating Legal parent page (LegalIndexPage)...")
        legal_parent = LegalIndexPage(
            title="Юридическая информация",
            slug="legal",
            body="<p>В данном разделе представлены основные юридические документы, регламентирующие работу нашего сервиса и правила обработки данных.</p>",
            meta_robots=SeoAbstract.MetaRobotsChoices.NOINDEX_NOFOLLOW,
            show_in_menus=False,
        )
        homepage.add_child(instance=legal_parent)
        legal_parent.save_revision().publish()
        command.stdout.write(command.style.SUCCESS("Legal parent page created."))
    else:
        # Update meta_robots if not set
        if legal_parent.meta_robots != SeoAbstract.MetaRobotsChoices.NOINDEX_NOFOLLOW:
            legal_parent.meta_robots = SeoAbstract.MetaRobotsChoices.NOINDEX_NOFOLLOW
            legal_parent.save_revision().publish()
            command.stdout.write(
                command.style.SUCCESS("Legal parent page SEO tags updated.")
            )

    # 2. Create Privacy Policy
    privacy_policy = (
        LegalDocumentPage.objects.descendant_of(legal_parent)
        .filter(slug="privacy-policy")
        .first()
    )
    if not privacy_policy:
        # Check if it exists as old LegalPage
        existing_old = (
            Page.objects.descendant_of(legal_parent)
            .filter(slug="privacy-policy")
            .first()
        )
        if existing_old:
            existing_old.delete()

        command.stdout.write("Creating Privacy Policy page...")
        privacy_policy = LegalDocumentPage(
            title="Политика конфиденциальности",
            slug="privacy-policy",
            body="<h2>1. Общие положения</h2><p>Настоящая политика обработки персональных данных составлена в соответствии с требованиями Закона Республики Беларусь от 07.05.2021 № 99-З «О защите персональных данных»...</p>",
            meta_robots=SeoAbstract.MetaRobotsChoices.NOINDEX_NOFOLLOW,
            show_in_menus=False,
        )
        legal_parent.add_child(instance=privacy_policy)
        privacy_policy.save_revision().publish()
        command.stdout.write(command.style.SUCCESS("Privacy Policy page created."))
    else:
        # Update meta_robots if not set
        if privacy_policy.meta_robots != SeoAbstract.MetaRobotsChoices.NOINDEX_NOFOLLOW:
            privacy_policy.meta_robots = SeoAbstract.MetaRobotsChoices.NOINDEX_NOFOLLOW
            privacy_policy.save_revision().publish()
            command.stdout.write(
                command.style.SUCCESS("Privacy Policy page SEO tags updated.")
            )

    # 3. Create User Agreement
    user_agreement = (
        LegalDocumentPage.objects.descendant_of(legal_parent)
        .filter(slug="user-agreement")
        .first()
    )
    if not user_agreement:
        # Check if it exists as old LegalPage
        existing_old = (
            Page.objects.descendant_of(legal_parent)
            .filter(slug="user-agreement")
            .first()
        )
        if existing_old:
            existing_old.delete()

        command.stdout.write("Creating User Agreement page...")
        user_agreement = LegalDocumentPage(
            title="Пользовательское соглашение",
            slug="user-agreement",
            body="<h2>1. Предмет соглашения</h2><p>Данное соглашение регулирует правила использования сайта и предоставления услуг...</p>",
            meta_robots=SeoAbstract.MetaRobotsChoices.NOINDEX_NOFOLLOW,
            show_in_menus=False,
        )
        legal_parent.add_child(instance=user_agreement)
        user_agreement.save_revision().publish()
        command.stdout.write(command.style.SUCCESS("User Agreement page created."))
    else:
        # Update meta_robots if not set
        if user_agreement.meta_robots != SeoAbstract.MetaRobotsChoices.NOINDEX_NOFOLLOW:
            user_agreement.meta_robots = SeoAbstract.MetaRobotsChoices.NOINDEX_NOFOLLOW
            user_agreement.save_revision().publish()
            command.stdout.write(
                command.style.SUCCESS("User Agreement page SEO tags updated.")
            )

    # 4. Link in ContactSettings
    contact_settings = ContactSettings.load()
    updated = False
    if (
        not contact_settings.privacy_policy_page
        or contact_settings.privacy_policy_page.id != privacy_policy.id
    ):
        contact_settings.privacy_policy_page = privacy_policy
        updated = True
    if (
        not contact_settings.terms_of_service_page
        or contact_settings.terms_of_service_page.id != user_agreement.id
    ):
        contact_settings.terms_of_service_page = user_agreement
        updated = True
    if (
        not contact_settings.legal_index_page
        or contact_settings.legal_index_page.id != legal_parent.id
    ):
        contact_settings.legal_index_page = legal_parent
        updated = True

    if updated:
        contact_settings.save()
        command.stdout.write(
            command.style.SUCCESS("Legal pages linked in Contact Settings.")
        )
