from django import template

register = template.Library()


@register.simple_tag
def get_og_image_url(page, request=None):
    """
    Get the OG image URL for pages that provide SEO metadata.
    """
    page = getattr(page, "specific", page)
    get_url = getattr(page, "get_og_image_url", None)
    if not callable(get_url):
        return ""
    return get_url(request)


@register.simple_tag
def get_page_canonical_url(page, request):
    """
    Get the canonical URL for a page.
    """
    if not request:
        return ""

    get_url = getattr(page, "get_url", None)
    relative_url = get_url() if callable(get_url) else "/"
    return request.build_absolute_uri(relative_url or "/")


@register.simple_tag
def get_seo_title(page):
    """
    Get the SEO title for a page, falling back to regular title if not set.
    """
    return getattr(page, "seo_title", "") or getattr(page, "title", "") or "Untitled Page"


@register.simple_tag
def get_seo_description(page):
    """
    Get the SEO description for a page.
    """
    return getattr(page, "search_description", "") or ""


@register.simple_tag
def get_published_date(page):
    """
    Get the publication date for OG tags.
    """
    published_date = getattr(page, "published_date", None) or getattr(page, "first_published_at", None)
    return published_date.isoformat() if published_date else ""


@register.simple_tag
def get_modified_date(page):
    """
    Get the modification date for OG tags.
    """
    modified_date = getattr(page, "modified_date", None) or getattr(page, "last_published_at", None)
    return modified_date.isoformat() if modified_date else ""


@register.simple_tag
def get_og_image_alt(page):
    """
    Get the alt text for OG image.
    Fallback to page title if image title looks like a filename.
    """
    import re

    page_title = getattr(page, "title", "") or ""
    image = getattr(page, "og_image", None)
    if not image:
        return page_title

    image_title = image.title or ""
    if re.search(r"\.(jpg|jpeg|png|gif|webp|svg|bmp)$", image_title.lower()):
        return page_title
    return image_title or page_title


@register.filter
def strip_html(value):
    """
    Strip HTML tags from text (for excerpt in JSON-LD)
    """
    import re

    from django.utils.html import strip_tags

    try:
        # Use Django's strip_tags to properly handle HTML entities
        clean = strip_tags(str(value))
        # Replace multiple spaces/newlines with single space
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()
    except Exception:
        return str(value)
