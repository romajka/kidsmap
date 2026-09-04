import json

from django.templatetags.static import static
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.text import Truncator
from django.utils.translation import get_language, gettext as _, override

from catalog.models import Place
from catalog.services.public_urls import build_public_absolute_uri


DEFAULT_ROBOTS_CONTENT = "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"


def _normalize_text(value: str) -> str:
    return " ".join(str(value or "").split())


def _truncate_text(value: str, limit: int = 160) -> str:
    normalized = _normalize_text(value)
    if not normalized:
        return ""
    return Truncator(normalized).chars(limit, truncate="…")


def _catalog_cards_count(total: int) -> str:
    total = int(total)
    language_code = (get_language() or "az").split("-", 1)[0]
    if language_code == "az":
        return f"{total} kart"
    if language_code == "en":
        return f"{total} card" if total == 1 else f"{total} cards"

    mod_10 = total % 10
    mod_100 = total % 100
    if mod_10 == 1 and mod_100 != 11:
        noun = "карточка"
    elif mod_10 in {2, 3, 4} and mod_100 not in {12, 13, 14}:
        noun = "карточки"
    else:
        noun = "карточек"
    return f"{total} {noun}"


def _catalog_cards_found(total: int) -> str:
    total = int(total)
    language_code = (get_language() or "az").split("-", 1)[0]
    cards_count = _catalog_cards_count(total)
    if language_code == "az":
        return f"{cards_count} tapıldı"
    if language_code == "en":
        return f"{cards_count} found"
    if total % 10 == 1 and total % 100 != 11:
        return f"Найдена {cards_count}"
    return f"Найдено {cards_count}"


def build_branded_seo_title(title: str, *, brand: str = "KidsMap", limit: int = 65) -> str:
    suffix = f" | {brand}"
    normalized_title = _normalize_text(title)
    available_length = max(limit - len(suffix), 1)
    return f"{Truncator(normalized_title).chars(available_length, truncate='…')}{suffix}"


def _absolute_uri(request, url: str) -> str:
    if not url:
        return ""
    if url.startswith(("http://", "https://")):
        return url
    return build_public_absolute_uri(request, url)


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
    district_label = ""
    if district:
        from catalog.services.locations import get_location_translation
        district_label = get_location_translation(district)
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
        from catalog.services.locations import get_location_translation
        summary.append(_("Регион / район: %(district)s") % {"district": get_location_translation(district)})
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
    home_url = _absolute_uri(request, reverse("home"))
    catalog_url = _absolute_uri(request, reverse("place_list"))
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
                    "url": _absolute_uri(request, place.get_absolute_url()),
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
    language_code = (get_language() or request.LANGUAGE_CODE or "az").split("-", 1)[0]
    title_base = _catalog_title_base(selected=selected, is_new_page=is_new_page)
    title_with_page = title_base
    if int(page_number or 1) > 1:
        title_with_page = _("%(title)s — страница %(page)s") % {"title": title_base, "page": int(page_number)}

    filter_summary = _catalog_filter_summary(selected, is_new_page=is_new_page)
    cards_count = _catalog_cards_count(total_count)
    cards_found = _catalog_cards_found(total_count)
    if filter_summary:
        filters_text = "; ".join(filter_summary)
        if language_code == "az":
            description = f"{title_base}. {filters_text}. KidsMap seçməsində hazırda {cards_count} var."
        elif language_code == "en":
            description = f"{title_base}. {filters_text}. There are currently {cards_count} in this KidsMap selection."
        else:
            description = f"{title_base}. {filters_text}. Сейчас в подборке {cards_count} на KidsMap."
    elif is_new_page:
        description = _("%(title)s. Смотрите свежие карточки, фильтруйте по рейтингу, фото и проверке на KidsMap.") % {
            "title": title_base
        }
    else:
        description = _("%(title)s. Фильтры по категории, региону, метро, возрасту и цене на KidsMap.") % {
            "title": title_base
        }

    if filter_summary:
        intro = f"{title_base}. {cards_found}. {'; '.join(filter_summary)}."
    elif language_code == "az":
        intro = f"{title_base}. KidsMap kataloqunda {cards_found}."
    elif language_code == "en":
        intro = f"{title_base}. {cards_found} in the KidsMap catalog."
    else:
        intro = f"{title_base}. {cards_found} в каталоге KidsMap."

    breadcrumb_name = _("Новое в каталоге") if is_new_page else _("Каталог")
    breadcrumb_items = [
        {"name": str(_("Главная")), "url": reverse("home")},
        {
            "name": str(breadcrumb_name),
            "url": reverse("place_new" if is_new_page else "place_list"),
        },
    ]
    # A category filter is the one narrowing that also exists as a level in the
    # place card trail, so keep the two chains identical up to that point.
    selected_category = _normalize_text(selected.get("category"))
    if selected_category and not is_new_page:
        breadcrumb_items.append(
            {
                "name": str(_catalog_category_label(selected_category)),
                "url": f"{reverse('place_list')}?{urlencode({'category': selected_category})}",
            }
        )
    breadcrumb_schema_json = _build_breadcrumb_schema(
        [{"name": item["name"], "url": _absolute_uri(request, item["url"])} for item in breadcrumb_items]
    )

    position_offset = max(int(page_number or 1) - 1, 0) * 10
    item_list_schema_json = _build_item_list_schema(
        name=title_base,
        item_urls=[
            {
                "position": position_offset + idx,
                "url": _absolute_uri(request, place.get_absolute_url()),
                "name": place.name_i18n(language_code),
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
        "catalog_breadcrumb_items": breadcrumb_items,
        "catalog_item_list_schema_json": item_list_schema_json,
    }


def _place_description(place, language_code: str) -> str:
    lang = (language_code or "az").split("-")[0].lower()
    if place.description_i18n(lang):
        return _truncate_text(place.description_i18n(lang), 180)

    category_label = place.get_category_display()
    if place.category:
        category_label = place.category.name_i18n(lang)

    with override(lang):
        bits = [place.name_i18n(lang), str(category_label)]
        if place.district:
            from catalog.services.locations import get_location_translation
            bits.append(_("регион %(district)s") % {"district": get_location_translation(place.district, lang)})
        if place.metro:
            from catalog.services.locations import get_metro_translation
            bits.append(_("метро %(metro)s") % {"metro": get_metro_translation(place.metro, lang)})
        if place.age_display:
            bits.append(_("возраст %(age)s") % {"age": place.age_display})
        if place.price_range_display:
            bits.append(_("цена %(price)s") % {"price": place.price_range_display})
        return _truncate_text(". ".join(bits) + ".", 180)


def build_place_seo_payload(place, request, language_code):
    lang = (language_code or "az").split("-")[0].lower()
    with override(lang):
        gallery = place.gallery_files()
        first_image_url = _absolute_uri(request, gallery[0].url) if gallery else _absolute_uri(request, static("img/logo.svg"))
        description = _place_description(place, lang)

        category_label = place.get_category_display()
        if place.category:
            category_label = place.category.name_i18n(lang)

        if place.district:
            from catalog.services.locations import get_location_translation
            title = _("%(name)s — %(category)s для детей в регионе %(district)s | KidsMap") % {
                "name": place.name_i18n(lang),
                "category": category_label,
                "district": get_location_translation(place.district, lang),
            }
        else:
            title = _("%(name)s — кружок и секция для детей в Азербайджане | KidsMap") % {
                "name": place.name_i18n(lang),
            }

        address_payload = {
            "@type": "PostalAddress",
            "addressCountry": "AZ",
        }
        if place.address:
            address_payload["streetAddress"] = place.address
        if place.district:
            from catalog.services.locations import get_location_translation
            address_payload["addressLocality"] = get_location_translation(place.district, lang)
        else:
            address_payload["addressLocality"] = "Azerbaijan"

        schema = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": place.name_i18n(lang),
            "description": description,
            "url": _absolute_uri(request, place.get_absolute_url()),
            "image": first_image_url,
            "address": address_payload,
            "areaServed": {"@type": "Country", "name": "Azerbaijan"},
            "additionalType": str(category_label),
        }
        if place.phone1:
            schema["telephone"] = place.phone1

        SCHEMA_WEEKDAY_MAP = {
            "mon": "https://schema.org/Monday",
            "tue": "https://schema.org/Tuesday",
            "wed": "https://schema.org/Wednesday",
            "thu": "https://schema.org/Thursday",
            "fri": "https://schema.org/Friday",
            "sat": "https://schema.org/Saturday",
            "sun": "https://schema.org/Sunday",
        }
        schedule_mode = getattr(place, "schedule_mode", Place.SCHEDULE_MODE_REGULAR) or Place.SCHEDULE_MODE_REGULAR
        if schedule_mode == Place.SCHEDULE_MODE_ALWAYS_OPEN:
            schema["openingHoursSpecification"] = [
                {
                    "@type": "OpeningHoursSpecification",
                    "dayOfWeek": list(SCHEMA_WEEKDAY_MAP.values()),
                    "opens": "00:00",
                    "closes": "23:59",
                }
            ]
        elif schedule_mode == Place.SCHEDULE_MODE_REGULAR:
            opening_hours = []
            for day in place.schedule_days.prefetch_related("intervals").all():
                if day.is_closed:
                    continue
                day_schema = SCHEMA_WEEKDAY_MAP.get(day.weekday)
                if not day_schema:
                    continue
                if day.is_24_hours:
                    opening_hours.append({
                        "@type": "OpeningHoursSpecification",
                        "dayOfWeek": [day_schema],
                        "opens": "00:00",
                        "closes": "23:59",
                    })
                else:
                    for interval in day.intervals.all():
                        opening_hours.append({
                            "@type": "OpeningHoursSpecification",
                            "dayOfWeek": [day_schema],
                            "opens": interval.start_time.strftime("%H:%M"),
                            "closes": interval.end_time.strftime("%H:%M"),
                        })
            if opening_hours:
                schema["openingHoursSpecification"] = opening_hours

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
        for plan in place.pricing_plan_records.filter(is_active=True, charge_role="primary").order_by("sort_order", "id"):
            if plan.price_kind not in {"exact", "free", "range", "from"}:
                continue
            offer = {"@type": "Offer", "name": plan.title_i18n(lang), "priceCurrency": plan.currency}
            if plan.price_kind in {"exact", "free"}:
                offer["price"] = format(plan.price, ".2f")
            elif plan.price_kind == "from":
                val = plan.price_min if plan.price_min is not None else plan.price
                if val is not None:
                    offer["price"] = format(val, ".2f")
                    offer["priceSpecification"] = {
                        "@type": "PriceSpecification",
                        "minPrice": format(val, ".2f"),
                        "priceCurrency": plan.currency,
                    }
            elif plan.price_min is not None and plan.price_max is not None:
                offer["priceSpecification"] = {
                    "@type": "PriceSpecification",
                    "minPrice": format(plan.price_min, ".2f"),
                    "maxPrice": format(plan.price_max, ".2f"),
                    "priceCurrency": plan.currency,
                }
            offers.append(offer)

        if not offers:
            price_mode = getattr(place, "price_mode", Place.PRICE_MODE_TARIFFS) or Place.PRICE_MODE_TARIFFS
            if price_mode == Place.PRICE_MODE_FREE:
                free_label = {"az": "Pulsuz", "ru": "Бесплатно", "en": "Free"}.get(lang, "Бесплатно")
                offers.append({
                    "@type": "Offer",
                    "name": free_label,
                    "price": "0.00",
                    "priceCurrency": "AZN",
                })

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
            map_open_url = f"https://www.google.com/maps/dir/?api=1&destination={query}"

        breadcrumb_items = [
            {"name": str(_("Главная")), "url": reverse("home")},
            {"name": str(_("Каталог")), "url": reverse("place_list")},
        ]
        if place.category_id:
            breadcrumb_items.append(
                {
                    "name": str(category_label),
                    "url": f"{reverse('place_list')}?{urlencode({'category': place.category_id})}",
                }
            )
        breadcrumb_items.append({"name": place.name_i18n(lang), "url": place.get_absolute_url()})

        breadcrumb_schema_json = _build_breadcrumb_schema(
            [{"name": item["name"], "url": _absolute_uri(request, item["url"])} for item in breadcrumb_items]
        )

        return {
            "title": title,
            "description": description,
            "first_image_url": first_image_url,
            "schema_json": json.dumps(schema, ensure_ascii=False),
            "breadcrumb_schema_json": breadcrumb_schema_json,
            "breadcrumb_items": breadcrumb_items,
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
            {"name": _("Главная"), "url": _absolute_uri(request, reverse("home"))},
            {"name": _("Отзывы"), "url": _absolute_uri(request, reverse("site_reviews"))},
        ]
    )

    return {
        "seo_title": f"{title} | KidsMap",
        "meta_description": _truncate_text(description, 180),
        "site_reviews_breadcrumb_schema_json": breadcrumb_schema_json,
    }


def build_seo_landing_schema_payload(request, page):
    # Landings live under /catalog/<slug>/, so the catalog is their real parent
    # both in the URL and in the site hierarchy.
    breadcrumb_items = [
        {"name": str(_("Главная")), "url": reverse("home")},
        {"name": str(_("Каталог")), "url": reverse("place_list")},
        {"name": page["title"], "url": request.path},
    ]
    breadcrumb_schema = _build_breadcrumb_schema(
        [{"name": item["name"], "url": _absolute_uri(request, item["url"])} for item in breadcrumb_items]
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
        "breadcrumb_items": breadcrumb_items,
        "faq_schema_json": json.dumps(faq_schema, ensure_ascii=False),
    }
