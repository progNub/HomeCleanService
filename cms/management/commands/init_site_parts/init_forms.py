from cms.models import FormPage, FormField
from cms.models.seo import SeoAbstract

import os


def init_contact_form_page(command, homepage):
    """
    Creates a contact form page using Wagtail's AbstractEmailForm
    """
    command.stdout.write("Checking for Contact Form Page...")
    contact_page = (
        FormPage.objects.descendant_of(homepage).filter(slug="request").first()
    )

    if not contact_page:
        command.stdout.write("Creating Request Form Page...")
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
            from_address=os.getenv("CONTACT_FORM_FROM_EMAIL", "noreply@homeservice.by"),
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
            field_type="phonenumber",
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
        command.stdout.write(command.style.SUCCESS("Request Form Page created."))
    else:
        command.stdout.write(command.style.WARNING("Request Form Page already exists."))

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
            command.stdout.write(
                command.style.SUCCESS("Contact Form Page SEO tags updated.")
            )

        if not contact_page.show_in_menus:
            contact_page.show_in_menus = True
            contact_page.save_revision().publish()
            command.stdout.write(
                command.style.SUCCESS("Contact Form Page set to show in menus.")
            )

    # Ensure Agreement Checkbox exists
    ensure_agreement_field(command, contact_page)


def ensure_agreement_field(command, contact_page):
    """
    Adds or updates the agreement checkbox
    """

    agreement_field = contact_page.form_fields.filter(
        field_type="checkbox_agreement"
    ).first()
    if not agreement_field:
        FormField.objects.create(
            page=contact_page,
            label="Согласие на обработку персональных данных",
            field_type="checkbox_agreement",
            required=True,
            sort_order=10,
        )
        contact_page.save_revision().publish()
        command.stdout.write(command.style.SUCCESS("Agreement checkbox added to form."))
    else:
        agreement_field.save()
        contact_page.save_revision().publish()
        command.stdout.write(
            command.style.SUCCESS("Agreement checkbox help_text updated.")
        )
