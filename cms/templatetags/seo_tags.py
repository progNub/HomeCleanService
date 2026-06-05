from django import template

register = template.Library()


@register.simple_tag
def get_og_image_url(page, request):
    """
    Get the appropriate OG image URL for a page.
    Uses the unified logic from SeoAbstract model if available,
    otherwise falls back to manual logic.
    """
    try:
        # Use the model's method if page inherits from SeoAbstract
        if hasattr(page, "get_og_image_url"):
            return page.get_og_image_url(request)

        # Fallback for pages that don't inherit from SeoAbstract
        def get_compressed_image(image):
            return image.get_rendition("fill-1200x630|format-webp").url

        # Check if page has og_image
        if hasattr(page, "og_image") and page.og_image:
            return request.build_absolute_uri(get_compressed_image(page.og_image))

        # Check parent page
        parent_page = page.get_parent()
        if parent_page and hasattr(parent_page, "og_image") and parent_page.og_image:
            return request.build_absolute_uri(get_compressed_image(parent_page.og_image))

        # Check root page/site
        if hasattr(page, "get_site"):
            root_page = page.get_site().root_page.specific
            if root_page and hasattr(root_page, "logo") and root_page.logo:
                return request.build_absolute_uri(get_compressed_image(root_page.logo))

        # Check if current page has logo
        if hasattr(page, "logo") and page.logo:
            return request.build_absolute_uri(get_compressed_image(page.logo))

        return ""
    except Exception:
        # Return empty string if any error occurs
        return ""


@register.simple_tag
def get_page_canonical_url(page, request):
    """
    Get the canonical URL for a page.
    """
    try:
        if hasattr(page, "get_url"):
            return request.build_absolute_uri(page.get_url())
        return request.build_absolute_uri("/")
    except Exception:
        return request.build_absolute_uri("/")


@register.simple_tag
def get_seo_title(page):
    """
    Get the SEO title for a page, falling back to regular title if not set.
    """
    try:
        if hasattr(page, "seo_title") and page.seo_title:
            return page.seo_title
        if hasattr(page, "title") and page.title:
            return page.title
        return "Untitled Page"
    except Exception:
        return "Untitled Page"


@register.simple_tag
def get_seo_description(page):
    """
    Get the SEO description for a page.
    """
    try:
        if hasattr(page, "search_description") and page.search_description:
            return page.search_description
        return ""
    except Exception:
        return ""


@register.simple_tag
def get_published_date(page):
    """
    Get the publication date for OG tags.
    """
    try:
        if hasattr(page, "published_date") and page.published_date:
            return page.published_date.isoformat()
        if hasattr(page, "first_published_at") and page.first_published_at:
            return page.first_published_at.isoformat()
        return ""
    except Exception:
        return ""


@register.simple_tag
def get_modified_date(page):
    """
    Get the modification date for OG tags.
    """
    try:
        if hasattr(page, "modified_date") and page.modified_date:
            return page.modified_date.isoformat()
        if hasattr(page, "last_published_at") and page.last_published_at:
            return page.last_published_at.isoformat()
        return ""
    except Exception:
        return ""


@register.simple_tag
def get_og_image_alt(page):
    """
    Get the alt text for OG image.
    Fallback to page title if image title looks like a filename.
    """
    import re

    try:
        if hasattr(page, "og_image") and page.og_image:
            image_title = page.og_image.title or ""
            if re.search(r"\.(jpg|jpeg|png|gif|webp|svg|bmp)$", image_title.lower()):
                return page.title if hasattr(page, "title") else ""
            return image_title or (page.title if hasattr(page, "title") else "")
        return page.title if hasattr(page, "title") else ""
    except Exception:
        return ""


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
