from django import forms
from django.utils.translation import gettext_lazy as _
from .models import ContactRequest

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactRequest
        fields = ['name', 'phone', 'email', 'comment']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': _('Ваше имя'), 'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'placeholder': _('Номер телефона (например, +375...)'), 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': _('Ваш Email (необязательно)'), 'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'placeholder': _('Дополнительный комментарий'), 'class': 'form-control', 'rows': 4}),
        }
