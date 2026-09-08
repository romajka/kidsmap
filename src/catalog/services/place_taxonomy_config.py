"""Shared form taxonomy for admin pickers and the ChatGPT JSON instruction."""
from django.db.models import Count

from catalog.models import Place, Subcategory


def build_place_taxonomy_config(form):
    category_field = form.fields.get("category")
    subcategory_field = form.fields.get("subcategory")
    if category_field is None or subcategory_field is None:
        return {"categories": [], "subcategories": []}

    categories = []
    category_queryset = category_field.queryset.order_by("order", "name_ru", "name")
    subcategory_counts = {
        item["category_id"]: item["total"]
        for item in Subcategory.objects.filter(category__in=category_queryset)
        .values("category_id")
        .annotate(total=Count("pk"))
    }
    for category in category_queryset:
        categories.append(
            {
                "code": category.pk,
                "label": str(category.name_i18n()),
                "icon": category.icon_file_url,
                "icon_class": category.icon_name if category.icon_is_font_class else "",
                "color_bg": category.resolved_color_bg,
                "color_text": category.resolved_color_text,
                "subcategory_count": int(subcategory_counts.get(category.pk, 0) or 0),
            }
        )

    subcategories = []
    for subcategory in subcategory_field.queryset.order_by("category__order", "order", "name_ru", "name"):
        subcategories.append(
            {
                "id": str(subcategory.pk),
                "code": subcategory.code or "",
                "category": subcategory.category_id,
                "label": str(subcategory.name_i18n()),
                "icon": subcategory.icon_file_url,
            }
        )

    from catalog.services.locations import AZERBAIJAN_REGIONS_MAP, BAKU_DISTRICTS_MAP
    from catalog.models.pricing_plan import PricingPlan

    regions = [
        {"code": code, "name_ru": data["ru"], "name_az": data["az"], "name_en": data.get("en", "")}
        for code, data in AZERBAIJAN_REGIONS_MAP.items()
    ]
    districts = [
        {"code": code, "name_ru": data["ru"], "name_az": data["az"], "name_en": data.get("en", "")}
        for code, data in BAKU_DISTRICTS_MAP.items()
    ]
    price_modes = [{"code": code, "label": str(label)} for code, label in Place.PRICE_MODE_CHOICES]
    schedule_modes = [{"code": code, "label": str(label)} for code, label in Place.SCHEDULE_MODE_CHOICES]
    product_types = [{"code": code, "label": str(label)} for code, label in PricingPlan.PRODUCT_CHOICES]
    price_kinds = [{"code": code, "label": str(label)} for code, label in PricingPlan.PRICE_KIND_CHOICES]
    lesson_formats = [{"code": code, "label": str(label)} for code, label in PricingPlan.LESSON_FORMAT_CHOICES]
    billing_modes = [{"code": code, "label": str(label)} for code, label in PricingPlan.BILLING_MODE_CHOICES]

    return {
        "categories": categories,
        "subcategories": subcategories,
        "regions": regions,
        "districts": districts,
        "price_modes": price_modes,
        "schedule_modes": schedule_modes,
        "product_types": product_types,
        "price_kinds": price_kinds,
        "lesson_formats": lesson_formats,
        "billing_modes": billing_modes,
    }

