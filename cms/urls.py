from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import RedirectView, TemplateView
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps.views import sitemap
from wagtail.documents import urls as wagtaildocs_urls

from cms import views as cms_views

urlpatterns = [
    path("sitemap.xml", sitemap),
    path(
        "favicon.ico",
        RedirectView.as_view(url=settings.STATIC_URL + "cms/images/logo/logo_64x64.png", permanent=True),
    ),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path("health/", lambda r: HttpResponse("OK"), name="health_check"),
]

urlpatterns += i18n_patterns(
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("post-review/", cms_views.post_review, name="post_review"),
    path("i18n/", include("django.conf.urls.i18n")),
    prefix_default_language=False,
)

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path("__reload__/", include("django_browser_reload.urls"))]
    urlpatterns += debug_toolbar_urls()

urlpatterns = urlpatterns + i18n_patterns(
    path("", include(wagtail_urls)),
    prefix_default_language=False,
)
