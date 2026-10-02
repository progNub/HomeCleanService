import re
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from django.core.cache import caches
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Page, Site

from cms.forms import ReviewForm
from cms.models.pages.forms.models import FormPage
from cms.models.pages.home import HomePage
from cms.models.pages.portfolio import PortfolioIndexPage, PortfolioWorkPage


class PublicTemplateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.home = Page.get_first_root_node().add_child(instance=HomePage(title="Home", slug="home-test"))
        cls.site = Site.objects.get(is_default_site=True)
        cls.site.root_page = cls.home
        cls.site.save()

    def setUp(self):
        # Wagtail caches renditions by image ID; TestCase rolls IDs back between tests.
        for cache in caches.all():
            cache.clear()
        media = TemporaryDirectory(prefix="homeservice-template-test-")
        self.addCleanup(media.cleanup)
        self.enterContext(self.settings(MEDIA_ROOT=media.name))
        self.request = RequestFactory().get("/", HTTP_HOST="testserver")

    def test_base_uses_local_assets_and_theme_before_css(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        for asset in ("main.css", "bootstrap-icons.css", "bootstrap.bundle.min.js"):
            self.assertIn(f"/static/cms/dist/{asset}", html)
        self.assertNotIn("cdn.jsdelivr.net", html)
        self.assertNotIn("text/x-scss", html)
        self.assertNotIn("onclick=", html)
        self.assertIn("/static/cms/images/logo/favicon.ico", html)
        # The development middleware injects its own configured reload listener.
        self.assertNotIn("django-browser-reload/reload-listener.js", html)
        self.assertLess(html.index("cms/js/theme-switcher.js"), html.index("cms/dist/main.css"))

    def test_hero_has_responsive_high_priority_image(self):
        image = get_image_model().objects.create(title="Hero", file=get_test_image_file(size=(1920, 1080)))
        html = render_to_string("cms/home/blocks/hero.html", {"self": {"image": image, "title": "Welcome"}})
        self.assertIn('<picture class="hero-bg-image"', html)
        self.assertIn('fetchpriority="high"', html)
        self.assertIn('loading="eager"', html)
        self.assertIn('sizes="100vw"', html)
        self.assertIn('alt=""', html)
        self.assertIn("640w,", html)
        self.assertIn("1280w,", html)
        self.assertIn("1920w", html)
        self.assertNotIn("background-image:", html)

    def test_small_hero_does_not_repeat_srcset_widths(self):
        image = get_image_model().objects.create(title="Small hero", file=get_test_image_file(size=(320, 180)))
        html = render_to_string("cms/home/blocks/hero.html", {"self": {"image": image}})
        srcset = re.search(r'srcset="([^"]+)"', html).group(1)
        self.assertEqual(len(srcset.split(",")), 1)
        self.assertIn("320w", srcset)

    def test_reviews_escape_content_and_display_nonfield_errors(self):
        form = ReviewForm(data={"author": "Alice", "text": "Review", "rating": 5, "accept_privacy": True})
        self.assertTrue(form.is_valid())
        form.add_error(None, "Please wait before posting again")
        html = render_to_string(
            "cms/home/blocks/reviews.html",
            {
                "self": {"title": "Reviews"},
                "reviews": [SimpleNamespace(author="<script>author</script>", text="<b>text</b>", rating=5)],
                "review_form": form,
            },
            request=self.request,
        )
        self.assertIn("Please wait before posting again", html)
        self.assertIn("&lt;script&gt;author&lt;/script&gt;", html)
        self.assertIn('name="next" value="/"', html)
        self.assertIn('data-reviews-direction="-1"', html)
        self.assertIn('data-reviews-direction="1"', html)
        self.assertNotIn("onclick=", html)
        self.assertNotIn("style=", html)

    def test_portfolio_cta_follows_form_slug(self):
        form_page = self.home.add_child(instance=FormPage(title="Contact", slug="custom-contact"))
        portfolio = self.home.add_child(instance=PortfolioIndexPage(title="Works", slug="works"))
        work = portfolio.add_child(instance=PortfolioWorkPage(title="Work", slug="example"))
        response = self.client.get(work.get_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'href="{form_page.get_url()}"')
        self.assertNotContains(response, 'href="/request/"')
