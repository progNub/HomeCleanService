from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page

from cms.models.seo import SeoAbstract


class LegalIndexPage(SeoAbstract, Page):
    """
    Index page for legal documents.
    """

    template = "cms/legal/legal_index_page.html"
    parent_page_types = ["cms.HomePage"]
    subpage_types = ["cms.LegalDocumentPage"]

    body = RichTextField(
        blank=True,
        verbose_name=_("Описание"),
        help_text=_("Текст перед списком документов"),
    )

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]

    promote_panels = SeoAbstract.promote_panels

    def get_context(self, request):
        context = super().get_context(request)
        context["documents"] = self.get_children().live().specific()
        return context

    class Meta:
        verbose_name = _("Список юридических документов")
        verbose_name_plural = _("Списки юридических документов")


class LegalDocumentPage(SeoAbstract, Page):
    """
    Page for specific legal documents like Privacy Policy or User Agreement.
    """

    template = "cms/legal/legal_document_page.html"
    parent_page_types = ["cms.LegalIndexPage"]
    subpage_types = []

    body = RichTextField(
        verbose_name=_("Содержание страницы"),
        help_text=_("Основной текст юридического документа"),
    )

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]

    promote_panels = SeoAbstract.promote_panels

    class Meta:
        verbose_name = _("Юридический документ")
        verbose_name_plural = _("Юридические документы")
