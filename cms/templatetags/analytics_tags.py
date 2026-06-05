from django import template
from django.utils.safestring import mark_safe

from cms.models import ScriptSettings
from cms.models.settings import LocationChoices

register = template.Library()


def _render_scripts(context, location):
    """
    Helper function to render active scripts for a specific location.
    Works in both live and preview modes.
    """
    request = context.get("request")
    if not request:
        return ""

    try:
        # Get settings for the current site (Wagtail handles preview state automatically)
        settings = ScriptSettings.for_request(request)
        if not settings:
            return ""

        scripts = settings.custom_scripts.filter(location=location, is_active=True)
        html_output = "\n".join([script.code for script in scripts])
        return mark_safe(html_output)
    except Exception:
        # Silently fail if something goes wrong to avoid breaking the page
        return ""


@register.simple_tag(takes_context=True)
def render_analytics_header(context):
    """
    Renders analytics scripts intended for the <head> section.
    """
    return _render_scripts(context, LocationChoices.HEAD)


@register.simple_tag(takes_context=True)
def render_analytics_body_top(context):
    """
    Renders analytics scripts intended for the top of the <body> section.
    """
    return _render_scripts(context, LocationChoices.BODY_TOP)


@register.simple_tag(takes_context=True)
def render_analytics_body_bottom(context):
    """
    Renders analytics scripts intended for the bottom of the <body> section.
    """
    return _render_scripts(context, LocationChoices.BODY_BOTTOM)
