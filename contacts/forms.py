from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
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

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Проверка на дубликат за последний час
        an_hour_ago = timezone.now() - timedelta(hours=1)
        exists = ContactRequest.objects.filter(
            phone=phone,
            created_at__gte=an_hour_ago
        ).exists()

        if exists:
            # Мы пометим форму как "дубликат", но не будем выбрасывать обычную ошибку,
            self.is_duplicate = True
        else:
            self.is_duplicate = False
            
        return phone
