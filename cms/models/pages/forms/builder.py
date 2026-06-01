from django import forms
from django.utils.translation import gettext_lazy as _
from wagtail.contrib.forms.forms import FormBuilder
from wagtail.contrib.forms.models import FORM_FIELD_CHOICES
from collections import OrderedDict
from .form_fields import BYPhoneFormField

CUSTOM_FORM_FIELD_CHOICES = FORM_FIELD_CHOICES + (
    ("phonenumber", _("Номер телефона")),
    ("checkbox_agreement", _("Чекбокс согласия")),
)


class CustomFormBuilder(FormBuilder):
    def create_phonenumber_field(self, field, options):
        return BYPhoneFormField(**options)

    def create_checkbox_agreement_field(self, field, options):
        options.update({"required": True})
        return forms.BooleanField(**options)

    @property
    def formfields(self):
        """
        Переопределяем оригинальное свойство, чтобы добавить field_type
        в каждый создаваемый объект поля Django.
        """
        formfields = OrderedDict()

        for field in self.fields:
            options = self.get_field_options(field)
            # Вызывает нужный метод (create_checkbox_agreement_field и т.д.)
            create_field = self.get_create_field_function(field.field_type)

            clean_name = field.clean_name or field.get_field_clean_name()

            # Создаем поле Django
            django_field = create_field(field, options)

            # ВАЖНО: Пробрасываем тип из модели Wagtail в объект поля Django
            django_field.field_type = field.field_type

            formfields[clean_name] = django_field

        return formfields
