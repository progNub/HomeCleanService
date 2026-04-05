from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from .forms import ContactForm


@csrf_exempt
def contact_request_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Спасибо! Ваша заявка принята, мы свяжемся с вами."))
        else:
            messages.error(request, _("Пожалуйста, исправьте ошибки в форме."))
    return redirect(request.META.get('HTTP_REFERER', '/'))
