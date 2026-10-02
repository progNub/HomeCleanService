from django import template
from wagtail.models import Site

from cms.models.pages.forms.models import FormPage

register = template.Library()


@register.simple_tag(takes_context=True)
def request_page(context):
    request = context.get("request")
    if request is None:
        return None
    if not hasattr(request, "_cms_request_page"):
        site = Site.find_for_request(request)
        request._cms_request_page = (
            FormPage.objects.live().public().descendant_of(site.root_page, inclusive=True).order_by("path").first()
            if site
            else None
        )
    return request._cms_request_page
