import json

from django.templatetags.static import static
from django.urls import reverse
from django.utils.text import Truncator
from django.utils.translation import gettext as _

from catalog.models import Place


DEFAULT_ROBOTS_CONTENT = "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"


def _normalize_text(value: str) -> str:
    return " ".join(str(value or "").split())


def _truncate_text(value: str, limit: int = 160) -> str:
    normalized = _normalize_text(value)
    if not normalized:
        return ""
    return Truncator(normalized).chars(limit, truncate="…")


def _absolute_uri(request, url: str) -> str:
    if not url:
        return ""
    if url.startswith(("http://", "https://")):
        return url
    return request.build_absolute_uri(url)


def _build_breadcrumb_schema(items: list[dict]) -> str:
    return json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": idx,
                    "name": item["name"],
                    "item": item["url"],
                }
                for idx, item in enumerate(items, start=1)
            ],
        },
        ensure_ascii=False,
    )


def _build_item_list_schema(*, name: str, item_urls: list[dict], total_count: int | None = None) -> str:
    payload = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": name,
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": item["position"],
                "url": item["url"],
                "name": item["name"],
            }
            for item in item_urls
        ],
    }
    if total_count is not None:
        payload["numberOfItems"] = int(total_count)
    return json.dumps(payload, ensure_ascii=False)


def _catalog_category_label(category_code: str) -> str:
    from catalog.models import Category
    category = Category.objects.filter(code=category_code).first()
    if category:
        return str(category.name_i18n())
    return str(category_code)


def _catalog_title_base(*, selected: dict, is_new_page: bool) -> str:
    if is_new_page:
        days = str(selected.get("days") or "30")
        if days != "30":
            return _("Новые кружки и секции для детей в Азербайджане за %(days)s дней") % {"days": days}
        return _("Новые кружки и секции для детей в Азербайджане")

    query = _normalize_text(selected.get("q"))
    category = _normalize_text(selected.get("category"))
    district = _normalize_text(selected.get("district"))
    metro = _normalize_text(selected.get("metro"))
    district_label = str(_(district)) if district else ""
    metro_label = str(_(metro)) if metro else ""

    if query:
        return _('Поиск "%(query)s" среди кружков и секций для детей в Азербайджане') % {"query": query}
    if category and district:
        return _("%(category)s для детей в регионе %(district)s") % {
            "category": _catalog_category_label(category),
            "district": district_label,
        }
    if category:
        return _("%(category)s для детей в Азербайджане") % {"category": _catalog_category_label(category)}
    if district:
        return _("Кружки и секции для детей в регионе %(district)s") % {"district": district_label}
    if metro:
        return _("Кружки и секции для детей у метро %(metro)s") % {"metro": metro_label}
    return _("Каталог кружков и секций для детей в Азербайджане")


def _catalog_filter_summary(selected: dict, *, is_new_page: bool) -> list[str]:
    summary: list[str] = []
    category = _normalize_text(selected.get("category"))
    district = _normalize_text(selected.get("district"))
    metro = _normalize_text(selected.get("metro"))
    age_from = _normalize_text(selected.get("age_from"))
    age_to = _normalize_text(selected.get("age_to"))
    min_rating = _normalize_text(selected.get("min_rating"))
    price_from = _normalize_text(selected.get("price_from"))
    price_to = _normalize_text(selected.get("price_to"))

    if category:
        summary.append(_("Категория: %(category)s") % {"category": _catalog_category_label(category)})
    if district:
        summary.append(_("Регион / район: %(district)s") % {"district": str(_(district))})
    if metro:
        summary.append(_("Метро: %(metro)s") % {"metro": str(_(metro))})
    if age_from and age_to:
        summary.append(_("Возраст: %(age_from)s-%(age_to)s лет") % {"age_from": age_from, "age_to": age_to})
    elif age_from:
        summary.append(_("Возраст: от %(age_from)s лет") % {"age_from": age_from})
    elif age_to:
        summary.append(_("Возраст: до %(age_to)s лет") % {"age_to": age_to})
    if price_from and price_to:
        summary.append(_("Цена: %(price_from)s-%(price_to)s AZN") % {"price_from": price_from, "price_to": price_to})
    elif price_from:
        summary.append(_("Цена: от %(price_from)s AZN") % {"price_from": price_from})
    elif price_to:
        summary.append(_("Цена: до %(price_to)s AZN") % {"price_to": price_to})
    if min_rating:
        summary.append(_("Рейтинг: от %(rating)s") % {"rating": min_rating})
    if is_new_page and str(selected.get("with_photo") or "") == "1":
        summary.append(_("Только карточки с фото"))
    if is_new_page and str(selected.get("verified") or "") == "1":
        summary.append(_("Только проверенные карточки"))
    return summary


def build_sitewide_schema_payload(*, request, site_name: str, logo_url: str = "", social_urls: list[str] | None = None) -> dict:
    home_url = request.build_absolute_uri(reverse("home"))
    catalog_url = request.build_absolute_uri(reverse("place_list"))
    resolved_logo_url = _absolute_uri(request, logo_url or static("img/logo.svg"))

    organization = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": site_name,
        "url": home_url,
        "logo": resolved_logo_url,
    }
    if social_urls:
        organization["sameAs"] = [url for url in social_urls if url]

    website = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": site_name,
        "url": home_url,
        "potentialAction": {
            "@type": "SearchAction",
            "target": f"{catalog_url}?q={{search_term_string}}",
            "query-input": "required name=search_term_string",
        },
    }

    return {
        "organization_schema_json": json.dumps(organization, ensure_ascii=False),
        "website_schema_json": json.dumps(website, ensure_ascii=False),
    }


def build_home_seo_payload(*, request, popular_places) -> dict:
    title = _("Кружки и секции для детей в Азербайджане")
    description = _("KidsMap: каталог детских кружков и секций в Азербайджане с фильтрами по региону, возрасту и цене.")

    featured_places_schema_json = ""
    if popular_places:
        featured_places_schema_json = _build_item_list_schema(
            name=_("Популярные кружки и секции для детей в Азербайджане"),
            item_urls=[
                {
                    "position": idx,
                    "url": request.build_absolute_uri(place.get_absolute_url()),
                    "name": place.name_i18n(request.LANGUAGE_CODE),
                }
                for idx, place in enumerate(popular_places, start=1)
            ],
            total_count=len(popular_places),
        )

    return {
        "seo_title": f"{title} | KidsMap",
        "meta_description": description,
        "home_featured_schema_json": featured_places_schema_json,
    }


def build_catalog_seo_payload(*, request, selected: dict, places, total_count: int, is_new_page: bool, page_number: int) -> dict:
    title_base = _catalog_title_base(selected=selected, is_new_page=is_new_page)
    title_with_page = title_base
    if int(page_number or 1) > 1:
        title_with_page = _("%(title)s — страница %(page)s") % {"title": title_base, "page": int(page_number)}

    filter_summary = _catalog_filter_summary(selected, is_new_page=is_new_page)
    if filter_summary:
        description = _("%(title)s. %(filters)s. Сейчас в подборке %(total)s карточек на KidsMap.") % {
            "title": title_base,
            "filters": "; ".join(filter_summary),
            "total": int(total_count),
        }
    elif is_new_page:
        description = _("%(title)s. Смотрите свежие карточки, фильтруйте по рейтингу, фото и проверке на KidsMap.") % {
            "title": title_base
        }
    else:
        description = _("%(title)s. Фильтры по категории, региону, метро, возрасту и цене на KidsMap.") % {
            "title": title_base
        }

    intro = (
        _("%(title)s. Найдено %(total)s карточек. %(filters)s.") % {
            "title": title_base,
            "total": int(total_count),
            "filters": "; ".join(filter_summary),
        }
        if filter_summary
        else _("%(title)s. Найдено %(total)s карточек в каталоге KidsMap.") % {
            "title": title_base,
            "total": int(total_count),
        }
    )

    breadcrumb_name = _("Новое в каталоге") if is_new_page else _("Каталог")
    breadcrumb_schema_json = _build_breadcrumb_schema(
        [
            {"name": _("Главная"), "url": request.build_absolute_uri(reverse("home"))},
            {
                "name": breadcrumb_name,
                "url": request.build_absolute_uri(reverse("place_new" if is_new_page else "place_list")),
            },
        ]
    )

    position_offset = max(int(page_number or 1) - 1, 0) * 10
    item_list_schema_json = _build_item_list_schema(
        name=title_base,
        item_urls=[
            {
                "position": position_offset + idx,
                "url": request.build_absolute_uri(place.get_absolute_url()),
                "name": place.name_i18n(request.LANGUAGE_CODE),
            }
            for idx, place in enumerate(places, start=1)
        ],
        total_count=total_count,
    )

    return {
        "seo_title": f"{title_with_page} | KidsMap",
        "meta_description": _truncate_text(description, 180),
        "catalog_heading": title_base,
        "catalog_intro": intro,
        "catalog_breadcrumb_schema_json": breadcrumb_schema_json,
        "catalog_item_list_schema_json": item_list_schema_json,
    }


def _place_description(place, language_code: str) -> str:
    if place.description_i18n(language_code):
        return _truncate_text(place.description_i18n(language_code), 180)

    bits = [place.name_i18n(language_code), str(place.get_category_display())]
    if place.district:
        bits.append(_("регион %(district)s") % {"district": str(_(place.district))})
    if place.metro:
        bits.append(_("метро %(metro)s") % {"metro": str(_(place.metro))})
    if place.age_display:
        bits.append(_("возраст %(age)s") % {"age": place.age_display})
    if place.price_range_display:
        bits.append(_("цена %(price)s") % {"price": place.price_range_display})
    return _truncate_text(". ".join(bits) + ".", 180)


def build_place_seo_payload(place, request, language_code):
    gallery = place.gallery_files()
    first_image_url = _absolute_uri(request, gallery[0].url) if gallery else _absolute_uri(request, static("img/logo.svg"))
    description = _place_description(place, language_code)

    if place.district:
        title = _("%(name)s — %(category)s для детей в регионе %(district)s | KidsMap") % {
            "name": place.name_i18n(language_code),
            "category": place.get_category_display(),
            "district": str(_(place.district)),
        }
    else:
        title = _("%(name)s — кружок и секция для детей в Азербайджане | KidsMap") % {
            "name": place.name_i18n(language_code),
        }

    schema = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": place.name_i18n(language_code),
        "description": description,
        "url": request.build_absolute_uri(place.get_absolute_url()),
        "image": first_image_url,
        "telephone": place.phone1 or "",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": place.address or "",
            "addressLocality": place.district or "Azerbaijan",
            "addressCountry": "AZ",
        },
        "areaServed": {"@type": "Country", "name": "Azerbaijan"},
        "additionalType": str(place.get_category_display()),
    }

    same_as = [place.website_url(), place.instagram_url()]
    same_as = [item for item in same_as if item]
    if same_as:
        schema["sameAs"] = same_as

    if place.rating_count:
        schema["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": round(float(place.rating_avg or 0), 1),
            "reviewCount": int(place.rating_count),
            "bestRating": 5,
            "worstRating": 1,
        }

    offers = []
    if place.price_per_lesson is not None:
        offers.append(
            {
                "@type": "Offer",
                "name": str(_("1 урок")),
                "price": place.price_per_lesson,
                "priceCurrency": "AZN",
            }
        )
    if place.price_per_month is not None:
        offers.append(
            {
                "@type": "Offer",
                "name": str(_("1 месяц")),
                "price": place.price_per_month,
                "priceCurrency": "AZN",
            }
        )
    if place.price_from is not None:
        offer = {"@type": "Offer", "price": place.price_from, "priceCurrency": "AZN"}
        if place.price_to is not None:
            offer["priceSpecification"] = {
                "@type": "PriceSpecification",
                "minPrice": place.price_from,
                "maxPrice": place.price_to,
                "priceCurrency": "AZN",
            }
        offers.append(offer)
    if offers:
        schema["offers"] = offers if len(offers) > 1 else offers[0]

    map_embed_url = ""
    map_open_url = ""
    if place.lat is not None and place.lng is not None:
        schema["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": place.lat,
            "longitude": place.lng,
        }
        query = f"{place.lat},{place.lng}"
        map_embed_url = f"https://maps.google.com/maps?q={query}&z=15&output=embed"
        map_open_url = f"https://www.google.com/maps/search/?api=1&query={query}"

    breadcrumb_schema_json = _build_breadcrumb_schema(
        [
            {"name": _("Главная"), "url": request.build_absolute_uri(reverse("home"))},
            {"name": _("Каталог"), "url": request.build_absolute_uri(reverse("place_list"))},
            {"name": place.name_i18n(language_code), "url": request.build_absolute_uri(place.get_absolute_url())},
        ]
    )

    return {
        "title": title,
        "description": description,
        "first_image_url": first_image_url,
        "schema_json": json.dumps(schema, ensure_ascii=False),
        "breadcrumb_schema_json": breadcrumb_schema_json,
        "map_embed_url": map_embed_url,
        "map_open_url": map_open_url,
    }


def build_site_reviews_seo_payload(*, request, review_count: int) -> dict:
    title = _("Отзывы о KidsMap от родителей и пользователей")
    description = (
        _("Отзывы о сервисе KidsMap: впечатления родителей и пользователей о каталоге кружков и секций по Азербайджану.")
        if not review_count
        else _("Отзывы о сервисе KidsMap: %(count)s оценок и отзывов от родителей и пользователей.") % {
            "count": int(review_count)
        }
    )

    breadcrumb_schema_json = _build_breadcrumb_schema(
        [
            {"name": _("Главная"), "url": request.build_absolute_uri(reverse("home"))},
            {"name": _("Отзывы"), "url": request.build_absolute_uri(reverse("site_reviews"))},
        ]
    )

    return {
        "seo_title": f"{title} | KidsMap",
        "meta_description": _truncate_text(description, 180),
        "site_reviews_breadcrumb_schema_json": breadcrumb_schema_json,
    }


def build_seo_landing_schema_payload(request, page):
    breadcrumb_schema = _build_breadcrumb_schema(
        [
            {"name": _("Главная"), "url": request.build_absolute_uri(reverse("home"))},
            {"name": page["title"], "url": request.build_absolute_uri(request.path)},
        ]
    )
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {"@type": "Answer", "text": answer},
            }
            for question, answer in page["faq"]
        ],
    }
    return {
        "breadcrumb_schema_json": breadcrumb_schema,
        "faq_schema_json": json.dumps(faq_schema, ensure_ascii=False),
    }
