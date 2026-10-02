import logging
from collections import OrderedDict

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.utils.crypto import salted_hmac
from django.utils.translation import gettext_lazy as _
from wagtail.contrib.forms.forms import BaseForm, FormBuilder
from wagtail.contrib.forms.models import FORM_FIELD_CHOICES

from cms.request_utils import get_client_ip

from .form_fields import BYPhoneFormField

logger = logging.getLogger(__name__)


class LeadForm(BaseForm):
    _contact_website = forms.CharField(required=False, widget=forms.HiddenInput, max_length=200)

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.pop("_contact_website", ""):
            raise forms.ValidationError(_("Не удалось отправить форму. Пожалуйста, попробуйте ещё раз."))
        ip = get_client_ip(self.request)
        if self.errors or not ip:
            return cleaned_data
        key = "lead-rate:" + salted_hmac("lead-rate", ip).hexdigest()
        limit = getattr(settings, "LEAD_RATE_LIMIT", 10)
        window = getattr(settings, "LEAD_RATE_WINDOW_SECONDS", 3600)
        try:
            # Redis add/incr are atomic across web workers. Invalid forms never
            # consume the quota, so visitors can correct validation mistakes.
            if cache.add(key, 1, timeout=window):
                count = 1
            else:
                try:
                    count = cache.incr(key)
                except ValueError:  # Key expired between add and incr.
                    count = 1 if cache.add(key, 1, timeout=window) else cache.incr(key)
        except Exception:
            logger.warning("Lead rate-limit cache unavailable")
            return cleaned_data
        if count > limit:
            raise forms.ValidationError(_("Слишком много заявок. Пожалуйста, попробуйте позже."))
        return cleaned_data


CUSTOM_FORM_FIELD_CHOICES = FORM_FIELD_CHOICES + (
    ("phonenumber", _("Номер телефона")),
    ("checkbox_agreement", _("Чекбокс согласия")),
)


class CustomFormBuilder(FormBuilder):
    def get_form_class(self):
        return type("WagtailLeadForm", (LeadForm,), self.formfields)

    ADDITIONAL_FIELD_OPTIONS = {
        "singleline": {"max_length": 150},
        "multiline": {"max_length": 2000},
        "email": {"max_length": 254},
        "url": {"max_length": 2000},
        "phonenumber": {"max_length": 30},
        # Easy to add new defaults in the future, e.g.:
        # "number": {"min_value": 0},
    }

    def get_field_options(self, field):
        options = super().get_field_options(field)

        if field.field_type in self.ADDITIONAL_FIELD_OPTIONS:
            additional_options = self.ADDITIONAL_FIELD_OPTIONS.get(field.field_type)
            for key, value in additional_options.items():
                options.setdefault(key, value)
        return options

    def create_phonenumber_field(self, field, options):
        return BYPhoneFormField(**options)

    def create_checkbox_agreement_field(self, field, options):
        options.update({"required": True})
        return forms.BooleanField(**options)

    def create_date_field(self, field, options):
        # Override default input type 'text' to 'date'
        options.setdefault("widget", forms.DateInput(attrs={"type": "date"}))
        return forms.DateField(**options)

    def create_datetime_field(self, field, options):
        # Override default input type 'text' to 'datetime-local'
        options.setdefault("widget", forms.DateTimeInput(attrs={"type": "datetime-local"}))
        field = forms.DateTimeField(**options)
        return field

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
