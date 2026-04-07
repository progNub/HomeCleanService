from django import forms
from django.utils.translation import gettext_lazy as _
from .models import ContactRequest
from django.forms import ValidationError

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactRequest
        fields = ['name', 'phone', 'email', 'comment']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': _('Ваше имя'), 'class': 'form-control form-control-lg bg-light border-0'}),
            'phone': forms.TextInput(attrs={'placeholder': _('+375...'), 'class': 'form-control form-control-lg bg-light border-0'}),
            'email': forms.EmailInput(attrs={'placeholder': _('example@mail.com'), 'class': 'form-control form-control-lg bg-light border-0'}),
            'comment': forms.Textarea(attrs={'placeholder': _('Опишите вашу задачу...'), 'class': 'form-control form-control-lg bg-light border-0', 'rows': 4}),
        }
