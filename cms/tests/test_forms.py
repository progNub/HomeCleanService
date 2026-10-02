from unittest.mock import patch

from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings

from cms.blocks.reviews import ReviewsBlock
from cms.forms import ReviewForm
from cms.models.pages.forms.builder import LeadForm
from cms.models.reviews import Review
from cms.request_utils import get_client_ip
from cms.views import post_review
from cms.wagtail_hooks.cache import skip_personal_feedback


class ReviewTests(TestCase):
    def request(self, data=None, **meta):
        request = RequestFactory().post("/post-review/", data or {}, **meta)
        SessionMiddleware(lambda r: None).process_request(request)
        request._messages = FallbackStorage(request)
        return request

    @override_settings(TRUSTED_PROXY_CIDRS=["172.20.0.0/16"])
    def test_client_ip_only_trusts_known_proxy(self):
        request = self.request(REMOTE_ADDR="172.20.0.8", HTTP_X_REAL_IP="203.0.113.4")
        self.assertEqual(get_client_ip(request), "203.0.113.4")
        request.META["REMOTE_ADDR"] = "192.0.2.1"
        self.assertEqual(get_client_ip(request), "192.0.2.1")
        request.META["REMOTE_ADDR"] = "172.20.0.8"
        request.META["HTTP_X_REAL_IP"] = "not-an-ip"
        self.assertEqual(get_client_ip(request), "172.20.0.8")

    def test_review_post_rejects_get_and_external_redirect(self):
        self.assertEqual(post_review(RequestFactory().get("/post-review/")).status_code, 405)
        for destination in ("https://evil.example/x", "//evil.example/x", "javascript:alert(1)"):
            response = post_review(self.request({"next": destination}))
            self.assertEqual(response.url, "/#reviews")
            self.assertIn("no-store", response["Cache-Control"])

    def test_invalid_form_preserves_bound_fields_and_disables_cache(self):
        request = self.request({"author": "Alice", "text": "My review", "rating": "7", "next": "/works/"})
        self.assertEqual(post_review(request).url, "/works/#reviews")
        self.assertFalse(skip_personal_feedback(request, True))
        context = ReviewsBlock().get_context({}, parent_context={"request": request})
        form = context["review_form"]
        self.assertTrue(form.is_bound)
        self.assertEqual(form["text"].value(), "My review")
        self.assertIn("rating", form.errors)
        self.assertNotIn("review_form_data", request.session)
        self.assertFalse(request._wagtailcache_update)

    def test_overlong_review_errors_survive_redirect(self):
        request = self.request({"author": "A" * 300, "text": "X" * 3000, "rating": "5", "accept_privacy": "on"})
        post_review(request)
        form = ReviewsBlock().get_context({}, parent_context={"request": request})["review_form"]
        self.assertIn("author", form.errors)
        self.assertIn("text", form.errors)

    @patch("cms.models.reviews.LeadNotificationService")
    @override_settings(TRUSTED_PROXY_CIDRS=["172.20.0.0/16"])
    def test_cooldown_does_not_merge_different_visitors_behind_proxy(self, _notification):
        Review.objects.create(author="First", text="OK", ip="203.0.113.4", user_agent="browser")
        data = {"author": "Second", "text": "OK", "rating": "5", "accept_privacy": "on"}
        request = self.request(REMOTE_ADDR="172.20.0.8", HTTP_X_REAL_IP="203.0.113.5", HTTP_USER_AGENT="browser")
        self.assertTrue(ReviewForm(data, request=request).is_valid())
        request.META["HTTP_X_REAL_IP"] = "203.0.113.4"
        self.assertFalse(ReviewForm(data, request=request).is_valid())

    def test_personal_session_and_message_cookies_are_not_cached(self):
        request = self.request()
        for cookie in ("sessionid", "messages"):
            request.COOKIES = {cookie: "value"}
            self.assertFalse(skip_personal_feedback(request, True))


class LeadTests(TestCase):
    def setUp(self):
        cache.clear()
        self.request = RequestFactory().post("/request/", REMOTE_ADDR="203.0.113.1")

    def test_honeypot_is_not_saved_and_blocks_filled_value(self):
        form = LeadForm({"_contact_website": "https://spam.example"}, request=self.request)
        self.assertFalse(form.is_valid())
        form = LeadForm({}, request=self.request)
        self.assertTrue(form.is_valid())
        self.assertNotIn("_contact_website", form.cleaned_data)

    @override_settings(LEAD_RATE_LIMIT=2)
    def test_rate_limit_is_per_client_and_preserves_validation_retries(self):
        for _ in range(4):
            self.assertFalse(LeadForm({"_contact_website": "spam"}, request=self.request).is_valid())
        self.assertTrue(LeadForm({}, request=self.request).is_valid())
        self.assertTrue(LeadForm({}, request=self.request).is_valid())
        self.assertFalse(LeadForm({}, request=self.request).is_valid())
        other = RequestFactory().post("/request/", REMOTE_ADDR="203.0.113.2")
        self.assertTrue(LeadForm({}, request=other).is_valid())

    @patch("cms.models.pages.forms.builder.cache.add", side_effect=ConnectionError)
    def test_cache_outage_does_not_discard_legitimate_leads(self, _cache):
        self.assertTrue(LeadForm({}, request=self.request).is_valid())
