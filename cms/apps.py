from django.apps import AppConfig
from django.forms import widgets
from django.utils.translation import gettext_lazy as _


class CMSConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cms"
    verbose_name = _("Настройки системы")

    def ready(self):
        # 1. Patch standard DateInput
        self.patch_widget(widgets.DateInput, {"type": "date"})

        # 2. Patch DateTimeInput
        # Important: use 'datetime-local' to trigger the browser's native picker with clock
        self.patch_widget(widgets.DateTimeInput, {"type": "datetime-local"})

    def patch_widget(self, widget_class, default_attrs):
        """Helper method for monkey-patching widgets"""
        original_init = widget_class.__init__

        def new_init(self, attrs=None, format=None):
            # We don't hardcode 'form-control' here to keep it flexible,
            # but you can add it to default_attrs if needed globally.
            final_attrs = default_attrs.copy()
            if attrs:
                final_attrs.update(attrs)
            original_init(self, attrs=final_attrs, format=format)

        widget_class.__init__ = new_init
