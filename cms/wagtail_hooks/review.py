from django.utils.translation import gettext_lazy as _
from wagtail import hooks

from cms.models.reviews import Review
from cms.wagtail_hooks.confirm_bulk_action import ConfirmationBulkAction


@hooks.register("register_bulk_action")
class ApproveBulkAction(ConfirmationBulkAction):
    display_name = _("Одобрить")
    action_type = "approve"
    aria_label = _("Одобрить выбранные отзывы")
    confirm_text = _("Вы уверены, что хотите одобрить следующие отзывы?")
    yes_text = _("Да, одобрить")
    header_icon = "tick-inverse"
    models = [Review]

    def execute_action(self, objects, **kwargs):
        num_approved = Review.objects.filter(pk__in=[obj.pk for obj in objects]).update(is_approved=True)
        return num_approved, 0

    def get_success_message(self, num_parent_objects, num_child_objects):
        return _("Успешно одобрено отзывов: {num}").format(num=num_parent_objects)


@hooks.register("register_bulk_action")
class DisapproveBulkAction(ConfirmationBulkAction):
    display_name = _("Отклонить")
    action_type = "disapprove"
    aria_label = _("Отклонить выбранные отзывы")
    confirm_text = _("Вы уверены, что хотите отклонить следующие отзывы?")
    yes_text = _("Да, отклонить")
    header_icon = "cross"
    models = [Review]

    def execute_action(self, objects, **kwargs):
        num_disapproved = Review.objects.filter(pk__in=[obj.pk for obj in objects]).update(is_approved=False)
        return num_disapproved, 0

    def get_success_message(self, num_parent_objects, num_child_objects):
        return _("Успешно снято с публикации отзывов: {num}").format(num=num_parent_objects)
