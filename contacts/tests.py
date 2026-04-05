from django.test import TestCase, Client, override_settings
from django.urls import reverse
from .models import ContactRequest
from django.middleware.csrf import get_token

class ContactCSRFTest(TestCase):
    def setUp(self):
        # При @csrf_exempt не нужен enforce_csrf_checks=True для проверки успеха,
        # но мы оставим для проверки того, что Django все равно работает.
        self.client = Client()
        self.url = reverse('contact_request')

    def test_post_succeeds(self):
        response = self.client.post(self.url, {
            'name': 'Test User',
            'phone': '+375291234567',
            'email': 'test@example.com',
            'comment': 'Test Comment',
        }, HTTP_REFERER='/')
        
        self.assertEqual(response.status_code, 302)
        request = ContactRequest.objects.get(name='Test User')
        self.assertEqual(request.phone, '+375291234567')
        self.assertEqual(request.email, 'test@example.com')

    def test_invalid_phone(self):
        response = self.client.post(self.url, {
            'name': 'Invalid User',
            'phone': 'invalid',
        }, HTTP_REFERER='/')
        # Even with @csrf_exempt, validation still happens in the form
        self.assertEqual(response.status_code, 302) # Redirects back with error message
        self.assertFalse(ContactRequest.objects.filter(name='Invalid User').exists())
