from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from wagtail.models import Page, Site

from cms.blocks.reviews import ReviewsBlock
from cms.models.pages.forms.models import FormPage
from cms.models.pages.home import HomePage
from cms.models.pages.portfolio import PortfolioIndexPage, PortfolioWorkPage
from cms.models.reviews import Review
from cms.templatetags.navigation_tags import request_page


class PageTests(TestCase):
    def setUp(self):
        self.home = Page.get_first_root_node().add_child(instance=HomePage(title="Home", slug="home-test"))
        Site.objects.update(is_default_site=False)
        self.site = Site.objects.create(hostname="testserver", root_page=self.home, is_default_site=True)

    def test_request_page_is_live_and_scoped_to_site(self):
        other = Page.get_first_root_node().add_child(instance=HomePage(title="Other", slug="other-test"))
        other.add_child(instance=FormPage(title="External form", slug="form"))
        draft = self.home.add_child(instance=FormPage(title="Draft", slug="draft", live=False))
        request = RequestFactory().get("/")
        self.assertIsNone(request_page({"request": request}))
        target = self.home.add_child(instance=FormPage(title="Request", slug="request"))
        self.assertEqual(request_page({"request": RequestFactory().get("/")}), target)
        self.assertNotEqual(target, draft)

    @patch("cms.models.pages.forms.models.LeadNotificationService")
    def test_lead_submission_is_saved_and_honeypot_is_rejected(self, notification):
        cache.clear()
        page = self.home.add_child(instance=FormPage(title="Request", slug="request"))
        request = RequestFactory().post("/request/", {"_contact_website": "spam"})
        request.user = AnonymousUser()
        response = page.serve(request)
        self.assertFalse(response.context_data["form"].is_valid())
        self.assertEqual(page.get_submission_class().objects.filter(page=page).count(), 0)
        notification.assert_not_called()
        request = RequestFactory().post("/request/", {})
        request.user = AnonymousUser()
        response = page.serve(request)
        submission = page.get_submission_class().objects.get(page=page)
        self.assertNotIn("_contact_website", submission.form_data)
        self.assertIn("no-store", response["Cache-Control"])
        notification.assert_called_once_with(submission)

    def test_related_portfolio_works_are_stable_and_bounded(self):
        index = self.home.add_child(instance=PortfolioIndexPage(title="Works", slug="works"))
        works = [index.add_child(instance=PortfolioWorkPage(title=f"Work {i}", slug=f"work-{i}")) for i in range(5)]
        context = works[0].get_context(RequestFactory().get("/"))
        self.assertEqual([work.id for work in context["other_works"]], [work.id for work in reversed(works[-3:])])
        self.assertEqual(context["other_works"].query.select_related, {"main_image": {}})

    @patch("cms.models.reviews.LeadNotificationService")
    def test_review_list_is_bounded_and_approved(self, _notification):
        Review.objects.bulk_create(
            [Review(author=f"Author {i}", text="Review", is_approved=True) for i in range(35)]
            + [Review(author="Pending", text="Hidden")]
        )
        reviews = list(ReviewsBlock().get_context({})["reviews"])
        self.assertEqual(len(reviews), 30)
        self.assertTrue(all(review.is_approved for review in reviews))
