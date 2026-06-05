from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.views.bulk_action import BulkAction

from cms.models.reviews import Review


@hooks.register("register_bulk_action")
class ApproveBulkAction(BulkAction):
    display_name = _("Одобрить")
    action_type = "approve"
    aria_label = _("Одобрить выбранные отзывы")
    template_name = "cms/bulk_actions/confirm_bulk_approve.html"
    models = [Review]

    def check_perm(self, obj):
        return True

    def execute_action(self, objects, **kwargs):
        num_approved = Review.objects.filter(pk__in=[obj.pk for obj in objects]).update(is_approved=True)
        return num_approved, 0

    def get_success_message(self, num_parent_objects, num_child_objects):
        return _("Успешно одобрено отзывов: %d") % num_parent_objects

    def get_execution_context(self):
        return {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "header_icon": "tick-inverse",
                "action_button_class": "button",
            }
        )
        return context
