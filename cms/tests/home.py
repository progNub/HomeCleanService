from cms.models import HomePage
from contacts.models import ContactRequest
from django.utils import timezone
from datetime import timedelta

from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTestCase


class HomeSetUpTests(WagtailPageTestCase):
    """
    Tests for basic page structure setup and HomePage creation.
    """

    def test_root_create(self):
        root_page = Page.objects.get(pk=1)
        self.assertIsNotNone(root_page)

    def test_homepage_create(self):
        root_page = Page.objects.get(pk=1)
        homepage = HomePage(title="Home")
        root_page.add_child(instance=homepage)
        self.assertTrue(HomePage.objects.filter(title="Home").exists())


class HomeTests(WagtailPageTestCase):
    """
    Tests for homepage functionality and rendering.
    """

    def setUp(self):
        """
        Create a homepage instance for testing.
        """
        root_page = Page.get_first_root_node()
        # Clean up existing sites if any to avoid conflict
        Site.objects.all().delete()
        Site.objects.create(hostname="testserver", root_page=root_page, is_default_site=True)
        self.homepage = HomePage(title="Home", slug="home-test")
        root_page.add_child(instance=self.homepage)
        
        # Add contact_form block to homepage body
        self.homepage.body = [
            ('contact_form', {
                'title': 'Свяжитесь с нами',
                'subtitle': 'Оставьте свои контакты'
            })
        ]
        self.homepage.save_revision().publish()

    def test_homepage_is_renderable(self):
        self.assertPageIsRenderable(self.homepage)

    def test_homepage_template_used(self):
        response = self.client.get(self.homepage.url)
        self.assertTemplateUsed(response, "cms/home/home_page.html")

    def test_contact_form_timeout(self):
        """
        Test that multiple requests from the same phone number within an hour
        are ignored in DB but show success message.
        """
        phone = "+375291234567"
        data = {
            'name': 'Test User',
            'phone': phone,
            'email': 'test@example.com',
            'comment': 'Test comment'
        }

        # First request
        response = self.client.post(self.homepage.url, data)
        self.assertEqual(ContactRequest.objects.filter(phone=phone).count(), 1)
        self.assertContains(response, "Заявка успешно принята!")

        # Second request from same phone (within an hour)
        response2 = self.client.post(self.homepage.url, data)
        # Should still be 1 in DB
        self.assertEqual(ContactRequest.objects.filter(phone=phone).count(), 1)
        # But user sees success
        self.assertContains(response2, "Заявка успешно принята!")

        # Request from another phone
        phone2 = "+375297654321"
        data2 = data.copy()
        data2['phone'] = phone2
        response3 = self.client.post(self.homepage.url, data2)
        self.assertEqual(ContactRequest.objects.filter(phone=phone2).count(), 1)
        self.assertContains(response3, "Заявка успешно принята!")
