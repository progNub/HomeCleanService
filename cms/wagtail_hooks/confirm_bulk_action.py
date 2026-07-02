from abc import ABC

from django.utils.translation import gettext_lazy as _
from wagtail.admin.views.bulk_action import BulkAction


class ConfirmationBulkAction(BulkAction, ABC):
    action_title = _("Подтвердите действие")
    confirm_text = _("Вы уверены, что хотите применить это действие к выбранным объектам?")
    yes_text = _("Да, продолжить")
    no_text = _("Отмена")
    header_icon = "doc-full"
    action_button_class = "button"
    template_name = "cms/bulk_actions/confirmation_bulk_action.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "action_title": self.action_title,
                "confirm_text": self.confirm_text,
                "yes_text": self.yes_text,
                "no_text": self.no_text,
                "header_icon": self.header_icon,
                "action_button_class": self.action_button_class,
            }
        )
        return context

    def get_success_message(self, num_parent_objects, num_child_objects):
        return _("Успешно обработано объектов: {num}").format(num=num_parent_objects)
