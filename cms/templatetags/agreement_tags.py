from django import template

register = template.Library()


@register.inclusion_tag("cms/tags/agreement_text.html", takes_context=True)
def agreement_text(context):
    """
    Отображает текст согласия с политикой конфиденциальности и условиями использования.
    Используется в формах рядом с чекбоксом согласия.
    """
    return {
        "settings": context.get("settings"),
    }
