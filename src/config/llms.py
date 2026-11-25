"""A curated, language-independent guide to the public KidsMap website."""

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import translation
from django.utils.cache import patch_cache_control
from django.views.decorators.http import require_safe

from catalog.models import SiteSettings
from catalog.services.public_urls import build_public_absolute_uri


@require_safe
def llms_txt(request):
    # Unlike get_solo(), this read never creates settings on a public GET.
    flags = SiteSettings.objects.order_by("id").values(
        "organizations_section_enabled",
        "events_section_enabled",
        "specialists_section_enabled",
    ).first() or {}
    routes = [
        ("home", "KidsMap", "Overview and entry point for families in Azerbaijan."),
        ("place_list", "Activities and places", "Find children's clubs, classes and venues; compare location, age range and listed prices."),
    ]
    for flag, route, title, description in (
        ("organizations_section_enabled", "organization_list", "Organizations", "Public organization profiles and their available offerings."),
        ("events_section_enabled", "events_landing", "Events", "Date-based activities; check each event's date, time, location and current status."),
        ("specialists_section_enabled", "specialist_list", "Specialists", "Public specialist profiles; check specialization, consultation format and age range."),
    ):
        if flags.get(flag):
            routes.append((route, title, description))
    routes.extend([
        ("about", "About KidsMap", "What the project does and who it serves."),
        ("faq_page", "Frequently asked questions", "Help with finding activities and using the site."),
        ("contacts", "Contact KidsMap", "Project contacts and feedback."),
        ("add_place", "Submit a listing", "Public entry point for adding a place or activity to the catalog."),
    ])

    sections = []
    policy_links = []
    for code, label in settings.LANGUAGES:
        with translation.override(code):
            sections.append({
                "language": f"{label} ({code})",
                "links": [
                    {"title": title, "url": build_public_absolute_uri(request, reverse(route)), "description": description}
                    for route, title, description in routes
                ],
            })
            for route, title, description in (
                ("listing_rules", "Listing rules", "Publication and listing requirements."),
                ("review_rules", "Review rules", "Rules for user reviews."),
            ):
                policy_links.append({
                    "title": f"{title} ({code})",
                    "url": build_public_absolute_uri(request, reverse(route)),
                    "description": description,
                })

    content = render_to_string("llms.txt", {
        "sections": sections,
        "policy_links": policy_links,
        "sitemap_url": build_public_absolute_uri(request, reverse("django.contrib.sitemaps.views.sitemap")),
    })
    response = HttpResponse(content, content_type="text/plain; charset=utf-8")
    response["Content-Language"] = "en"
    patch_cache_control(response, public=True, max_age=300)
    return response
