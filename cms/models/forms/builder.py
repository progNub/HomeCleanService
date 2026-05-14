from django.utils.translation import gettext_lazy as _
from wagtail.contrib.forms.forms import FormBuilder
from wagtail.contrib.forms.models import FORM_FIELD_CHOICES

from cms.models.forms.form_fields import BYPhoneFormField

CUSTOM_FORM_FIELD_CHOICES = FORM_FIELD_CHOICES + (("phonenumber", _("Номер телефона")),)


class CustomFormBuilder(FormBuilder):
    def create_phonenumber_field(self, field, options):
        return BYPhoneFormField(**options)
