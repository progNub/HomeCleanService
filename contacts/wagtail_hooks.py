from django.utils.translation import gettext_lazy as _
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from .models import ContactRequest


class ContactRequestViewSet(SnippetViewSet):
    model = ContactRequest
    icon = "mail"
    menu_label = _("Заявки")
    menu_name = "contact_requests"
    menu_order = 200
    add_to_admin_menu = True
    list_display = ("name", "phone", "email", "created_at")
    search_fields = ("name", "phone", "email", "comment")


register_snippet(ContactRequestViewSet)
