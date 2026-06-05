from django.conf import settings
from django.urls import include, path
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import TemplateView
from django.http import HttpResponse

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from cms import views as cms_views
from wagtail.contrib.sitemaps.views import sitemap
from debug_toolbar.toolbar import debug_toolbar_urls


urlpatterns = [
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path("health/", lambda r: HttpResponse("OK"), name="health_check"),
]

urlpatterns += i18n_patterns(
    path("django-admin/", admin.site.urls),
    path("sitemap.xml", sitemap),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("post-review/", cms_views.post_review, name="post_review"),
    path("i18n/", include("django.conf.urls.i18n")),
    prefix_default_language=False,
)


if settings.DEBUG:
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
