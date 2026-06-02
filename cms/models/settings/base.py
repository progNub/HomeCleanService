class SettingsPreviewMixin:
    """
    Mixin to provide common preview logic for settings models.
    It injects the current (unsaved) settings instance into the context
    under the key used by Wagtail's {% get_settings %} tag.
    """

    def get_preview_template(self, request, mode_name):
        return "cms/home/home_page.html"

    def get_preview_context(self, request, mode_name):
        from cms.models import HomePage

        homepage = HomePage.objects.first()
        context = homepage.get_context(request) if homepage else {"request": request}

        # Wagtail settings are usually accessed in templates as
        # {{ settings.app_label.ModelName }} after {% get_settings %}
        if "settings" not in context:
            context["settings"] = {}
        if "cms" not in context["settings"]:
            context["settings"]["cms"] = {}

        # self is the current instance being previewed (including unsaved changes)
        context["settings"]["cms"][self.__class__.__name__] = self
        return context
