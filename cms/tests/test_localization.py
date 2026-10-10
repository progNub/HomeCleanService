from django.conf import settings
from django.test import SimpleTestCase
from django.utils.translation import gettext, override


class LocalizationTests(SimpleTestCase):
    def test_russian_and_english_are_available_in_wagtail(self):
        self.assertEqual([code for code, _name in settings.LANGUAGES], ["ru", "en"])
        self.assertEqual(settings.WAGTAILADMIN_PERMITTED_LANGUAGES, settings.LANGUAGES)
        self.assertEqual(settings.WAGTAIL_CONTENT_LANGUAGES, settings.LANGUAGES)

    def test_custom_interface_strings_have_both_languages(self):
        with override("ru"):
            self.assertEqual(gettext("Background tasks"), "Фоновые задачи")
        with override("en"):
            self.assertEqual(gettext("Настройки системы"), "System settings")
            self.assertEqual(gettext("Оставить отзыв"), "Leave a review")
