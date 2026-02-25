import json


def build_place_seo_payload(place, request, language_code):
    gallery = place.gallery_files()
    first_image_url = request.build_absolute_uri(gallery[0].url) if gallery else ""
    description = place.description_i18n(language_code) or place.name_i18n(language_code)

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
            "addressLocality": place.district or "Baku",
            "addressCountry": "AZ",
        },
    }

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

    return {
        "description": description,
        "first_image_url": first_image_url,
        "schema_json": json.dumps(schema, ensure_ascii=False),
        "map_embed_url": map_embed_url,
        "map_open_url": map_open_url,
    }


def build_seo_landing_schema_payload(request, page):
    breadcrumb_schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Главная",
                "item": request.build_absolute_uri("/"),
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": page["title"],
                "item": request.build_absolute_uri(request.path),
            },
        ],
    }
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
        "breadcrumb_schema_json": json.dumps(breadcrumb_schema, ensure_ascii=False),
        "faq_schema_json": json.dumps(faq_schema, ensure_ascii=False),
    }
