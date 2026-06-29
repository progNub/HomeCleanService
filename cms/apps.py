from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CMSConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cms"
    verbose_name = _("Настройки системы")
