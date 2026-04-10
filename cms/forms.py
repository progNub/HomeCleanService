from django import forms
from django.utils.translation import gettext_lazy as _
from cms.models.reviews import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["author", "text", "rating"]
        widgets = {
            "author": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Ваше имя")}
            ),
            "text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": _("Ваш отзыв"),
                }
            ),
            "rating": forms.Select(attrs={"class": "form-select"}),
        }
