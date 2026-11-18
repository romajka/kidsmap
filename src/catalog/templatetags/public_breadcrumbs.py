from django import template

from catalog.services.seo import build_section_breadcrumbs

register = template.Library()


@register.inclusion_tag("catalog/includes/section_breadcrumbs.html", takes_context=True)
def section_breadcrumbs(context, label, nav_class=""):
    request = context["request"]
    items, schema = build_section_breadcrumbs(request, label, request.path)
    return {
        "items": items,
        "nav_class": nav_class,
        "schema": schema if "noindex" not in context.get("robots_content", "") else "",
    }
