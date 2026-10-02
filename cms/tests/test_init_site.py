from io import StringIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from wagtail.images import get_image_model
from wagtail.models import Page, Site

from cms.models import FormField, FormPage, HomePage, MenuItem, Review


@override_settings(
    ENV_CONTACT_FORM_TO_EMAIL=None,
    ENV_CONTACT_FORM_FROM_EMAIL=None,
    ENV_CONTACT_PHONE=None,
    ENV_CONTACT_EMAIL=None,
    ENV_CONTACT_ADDRESS=None,
    ENV_LEGAL_FULL_NAME=None,
    ENV_LEGAL_UNP=None,
    ENV_LEGAL_ADDRESS=None,
    ENV_LEGAL_REG_DATE=None,
    ENV_SUPERUSER_USERNAME=None,
    ENV_SUPERUSER_EMAIL=None,
    ENV_SUPERUSER_PASSWORD=None,
    ENV_SITE_URL=None,
    TELEGRAM_BOT_TOKEN=None,
    TELEGRAM_NOTIFICATIONS_CHAT_ID=None,
)
class InitSiteTests(TestCase):
    def counts(self):
        return tuple(
            model.objects.count()
            for model in (Page, Site, FormField, MenuItem, Review, get_image_model(), get_user_model())
        )

    @patch("dotenv.load_dotenv")
    @patch("cms.services.telegram.base.requests.post")
    def test_clean_init_with_missing_optional_settings_is_idempotent(self, post, load_dotenv):
        cache.clear()
        # Fresh migrations create one CMS HomePage beneath Wagtail's root.
        root = Page.get_first_root_node()
        self.assertEqual(root.numchild, root.get_children().count())
        with TemporaryDirectory(prefix="homeservice-init-test-") as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                call_command("init_site", stdout=StringIO())
                initial = self.counts()
                form = FormPage.objects.get()
                self.assertEqual(form.to_address, "")
                self.assertEqual(form.from_address, "")
                self.assertEqual(form.form_fields.count(), 4)
                self.assertEqual(HomePage.objects.count(), 1)
                self.assertEqual(get_user_model().objects.count(), 0)
                call_command("init_site", stdout=StringIO())
                self.assertEqual(self.counts(), initial)
                for page in Page.objects.all():
                    self.assertEqual(page.numchild, page.get_children().count(), page.title)
        load_dotenv.assert_not_called()
        post.assert_not_called()
        cache.clear()

    def test_replacing_plain_placeholder_refreshes_root_child_count(self):
        from cms.management.commands.init_site import Command
        from cms.management.commands.init_site_parts.init_content import init_content

        HomePage.objects.all().delete()
        root = Page.get_first_root_node()
        root.add_child(instance=Page(title="Default Home", slug="home"))
        command = Command(stdout=StringIO())
        with TemporaryDirectory(prefix="homeservice-init-test-") as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                homepage = init_content(command)
                self.assertIsInstance(homepage, HomePage)
                root.refresh_from_db()
                self.assertEqual(root.numchild, root.get_children().count())

    def test_failed_child_insert_rolls_back_tree_and_retry_succeeds(self):
        cache.clear()
        initial = self.counts()
        original_save = FormPage.save

        def fail_initial_form_save(instance, *args, **kwargs):
            # Treebeard increments the parent's numchild before saving this child.
            if instance._state.adding:
                raise RuntimeError("Injected form insert failure")
            return original_save(instance, *args, **kwargs)

        with TemporaryDirectory(prefix="homeservice-init-test-") as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                with patch.object(FormPage, "save", fail_initial_form_save):
                    with self.assertRaisesRegex(RuntimeError, "Injected form insert failure"):
                        call_command("init_site", stdout=StringIO())
                self.assertEqual(self.counts(), initial)
                for page in Page.objects.all():
                    self.assertEqual(page.numchild, page.get_children().count(), page.title)
                # No repair command should be necessary after an atomic failure.
                cache.clear()
                call_command("init_site", stdout=StringIO())
                self.assertEqual(FormPage.objects.count(), 1)
                for page in Page.objects.all():
                    self.assertEqual(page.numchild, page.get_children().count(), page.title)
        cache.clear()
