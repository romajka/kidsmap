import json
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.http import Http404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Place, PlaceLike

BAKU_DISTRICTS = [
    "Ясамал",
    "Насими",
    "Низами",
    "Нариманов",
    "Сабаиль",
    "Сабунчи",
    "Бинагади",
    "Сураханы",
    "Хатаи",
    "Хазар",
    "Гарадаг",
    "Пираллахы",
]

BAKU_METRO_STATIONS = [
    "Ичеришехер",
    "Сахил",
    "28 Май",
    "Гянджлик",
    "Нариман Нариманов",
    "Бакмил",
    "Улдуз",
    "Кёроглу",
    "Гара Гараев",
    "Нефтчиляр",
    "Халглар Достлугу",
    "Ахмедлы",
    "Ази Асланов",
    "Низами",
    "Эльмляр Академиясы",
    "Иншаатчылар",
    "20 Января",
    "Мемар Аджеми",
    "Насими",
    "Азадлыг Проспекти",
    "Дернегюль",
    "Джафар Джаббарлы",
    "Шах Исмаил Хатаи",
    "Автовагзал",
    "8 Ноября",
    "Ходжасан",
]

BAKU_DISTRICT_SEO = [
    ("yasamal", "Ясамал"),
    ("nasimi", "Насими"),
    ("nizami", "Низами"),
    ("narimanov", "Нариманов"),
    ("sabail", "Сабаиль"),
    ("sabunchi", "Сабунчи"),
    ("binagadi", "Бинагади"),
    ("surakhani", "Сураханы"),
    ("khatai", "Хатаи"),
    ("khazar", "Хазар"),
    ("garadagh", "Гарадаг"),
    ("pirallahi", "Пираллахы"),
]

BASE_SEO_LANDING_PAGES = {
    "kruzhki-v-baku": {
        "title": "Кружки в Баку для детей",
        "meta_description": "Кружки в Баку для детей: спорт, творчество, музыка, технологии. Сравнивайте по району, возрасту и цене на KidsMap.",
        "intro": "На этой странице собраны детские кружки в Баку с удобным фильтром по возрасту, району и бюджету. Можно быстро перейти в карточку и связаться с местом.",
        "benefits": [
            "Кружки по спорту, музыке, творчеству и технологиям",
            "Фильтрация по району, метро и возрасту ребенка",
            "Сравнение стоимости до звонка или записи",
        ],
        "catalog_query": "",
        "faq": [
            ("Как выбрать кружок для ребенка в Баку?", "Сначала определите цель: развитие, спорт или подготовка к школе. Затем сравните места по району, возрасту и цене."),
            ("С какого возраста лучше начинать кружки?", "Чаще всего с 4-6 лет, но это зависит от направления. В карточках можно отфильтровать возрастные границы."),
        ],
    },
    "kursy-dlya-detey-v-baku": {
        "title": "Курсы для детей в Баку",
        "meta_description": "Курсы для детей в Баку: языки, программирование, творчество и подготовка. Найдите подходящий курс для ребенка на KidsMap.",
        "intro": "Подборка детских курсов в Баку для школьников и дошкольников. На KidsMap можно сравнить курсы по стоимости, локации и формату занятий.",
        "benefits": [
            "Курсы по образованию, технологиям и творческим направлениям",
            "Удобный поиск рядом с домом или школой",
            "Быстрый переход к контактам и расписанию",
        ],
        "catalog_query": "?category=EDU",
        "faq": [
            ("Какие курсы популярны для детей в Баку?", "Чаще всего выбирают языковые курсы, подготовку к школе, программирование и математику."),
            ("Как понять, что курс подходит ребенку?", "Проверьте возраст, программу, формат уроков и нагрузку. Лучше сравнить 2-3 варианта перед выбором."),
        ],
    },
    "sportivnye-sekcii-v-baku": {
        "title": "Спортивные секции в Баку",
        "meta_description": "Спортивные секции в Баку для детей: футбол, гимнастика, боевые искусства и другие направления. Выберите секцию по району и цене.",
        "intro": "Секции для активных детей в Баку: от базовой физической подготовки до соревновательных направлений. Смотрите условия и выбирайте по локации.",
        "benefits": [
            "Секции для разного возраста и уровня подготовки",
            "Фильтры по району и стоимости занятий",
            "Контакты клубов в одном месте",
        ],
        "catalog_query": "?category=SPRT",
        "faq": [
            ("Какая секция лучше для начинающего?", "Для старта обычно выбирают плавание, гимнастику или общую физподготовку. Главное учитывать интерес ребенка."),
            ("Сколько раз в неделю оптимально заниматься спортом?", "Обычно 2-3 раза в неделю достаточно для прогресса без перегрузки."),
        ],
    },
    "tvorcheskie-kruzhki-v-baku": {
        "title": "Творческие кружки в Баку",
        "meta_description": "Творческие кружки в Баку для детей: рисование, лепка, актерское мастерство и музыка. Найдите занятия рядом с вами.",
        "intro": "Творческие занятия помогают ребенку развивать воображение, речь и уверенность. В каталоге можно выбрать кружки по району, возрасту и цене.",
        "benefits": [
            "Рисование, лепка, театр, музыка и другие направления",
            "Подбор по возрасту ребенка",
            "Сравнение форматов и стоимости занятий",
        ],
        "catalog_query": "?category=ART",
        "faq": [
            ("Что дают ребенку творческие кружки?", "Они развивают креативность, мелкую моторику, коммуникацию и уверенность в себе."),
            ("Нужно ли иметь талант для начала?", "Нет, большинство кружков рассчитаны на старт с нуля и постепенное развитие."),
        ],
    },
    "programmirovanie-dlya-detey-baku": {
        "title": "Программирование для детей в Баку",
        "meta_description": "Программирование для детей в Баку: курсы Scratch, Python, робототехника и STEM-направления. Подберите курс по возрасту и району.",
        "intro": "Детские IT-курсы в Баку: визуальное программирование, основы кода и проектная работа. Сравнивайте школы по цене, району и возрасту.",
        "benefits": [
            "Курсы Scratch, Python, робототехники и STEM",
            "Программы для новичков и продолжающих",
            "Удобный поиск IT-направлений рядом",
        ],
        "catalog_query": "?category=TECH",
        "faq": [
            ("С какого возраста ребенку можно на программирование?", "Обычно с 7-8 лет, а визуальные форматы возможны и раньше."),
            ("Что выбрать первым: Scratch или Python?", "Для начала чаще выбирают Scratch, потом переходят к Python."),
        ],
    },
}


def _district_seo_pages():
    pages = {}
    for slug, district in BAKU_DISTRICT_SEO:
        page_slug = f"kruzhki-v-{slug}-baku"
        pages[page_slug] = {
            "title": f"Кружки в районе {district} (Баку)",
            "meta_description": f"Кружки и секции для детей в районе {district}, Баку. Сравнивайте по возрасту, цене и метро на KidsMap.",
            "intro": f"Подборка кружков и курсов для детей в районе {district}. Используйте фильтры по возрасту, метро и цене, чтобы выбрать лучший вариант рядом.",
            "benefits": [
                f"Детские кружки и секции в районе {district}",
                "Сравнение цен и возрастных групп",
                "Контакты и быстрый переход к карточке",
            ],
            "catalog_query": f"?district={district}",
            "faq": [
                (f"Какие кружки есть в районе {district}?", "На странице собраны спортивные, образовательные и творческие направления."),
                ("Как выбрать кружок рядом с домом?", "Используйте фильтр по району и метро, затем сравните возраст, цену и расписание."),
            ],
        }
    return pages


SEO_LANDING_PAGES = {**BASE_SEO_LANDING_PAGES, **_district_seo_pages()}


def _session_key(request):
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def _set_liked_flags(places, liked_ids):
    for place in places:
        place.is_liked = place.id in liked_ids


def home(request):
    categories = [
        {"code": "SPRT", "title": "Спорт"},
        {"code": "ART", "title": "Творчество"},
        {"code": "MUS", "title": "Музыка и сцена"},
        {"code": "EDU", "title": "Образование"},
        {"code": "TECH", "title": "Технологии"},
        {"code": "FUN", "title": "Досуг"},
    ]
    session_key = _session_key(request)
    liked_ids = set(PlaceLike.objects.filter(session_key=session_key).values_list("place_id", flat=True))
    popular_places = list(Place.objects.filter(is_active=True).order_by("-likes_count", "-updated_at")[:4])
    _set_liked_flags(popular_places, liked_ids)
    map_places = [
        {
            "name": place.name_i18n(request.LANGUAGE_CODE),
            "lat": place.lat,
            "lng": place.lng,
            "url": place.get_absolute_url(),
            "category": place.get_category_display(),
        }
        for place in Place.objects.filter(is_active=True).exclude(lat__isnull=True).exclude(lng__isnull=True)
    ]
    return render(
        request,
        "pages/home.html",
        {
            "home_categories": categories,
            "meta_description": "KidsMap: каталог детских кружков и секций в Баку с фильтрами по району, возрасту и цене.",
            "seo_pages": SEO_LANDING_PAGES,
            "popular_places": popular_places,
            "map_places": map_places,
            "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
        },
    )


def place_list(request):
    return _render_place_list(request)


def place_new(request):
    recent_cutoff = timezone.now() - timedelta(days=30)
    return _render_place_list(request, force_new_only=True, created_after=recent_cutoff)


def _render_place_list(request, force_new_only: bool = False, created_after=None):
    qs = Place.objects.filter(is_active=True)
    if created_after is not None:
        qs = qs.filter(created_at__gte=created_after)
    session_key = _session_key(request)
    liked_ids = set(PlaceLike.objects.filter(session_key=session_key).values_list("place_id", flat=True))

    category = request.GET.get("category", "").strip()
    query = request.GET.get("q", "").strip()
    district = request.GET.get("district", "").strip()
    metro = request.GET.get("metro", "").strip()
    age = request.GET.get("age", "").strip()
    price_from = request.GET.get("price_from", "").strip()
    price_to = request.GET.get("price_to", "").strip()
    price_max = request.GET.get("price_max", "").strip()
    sort = request.GET.get("sort", "new").strip()
    if force_new_only:
        sort = "new"

    if category:
        qs = qs.filter(category=category)
    if query:
        qs = qs.filter(
            Q(name_ru__icontains=query)
            | Q(name_en__icontains=query)
            | Q(name_az__icontains=query)
            | Q(name__icontains=query)
            | Q(description_ru__icontains=query)
            | Q(description_en__icontains=query)
            | Q(description_az__icontains=query)
            | Q(subcategory__icontains=query)
            | Q(address__icontains=query)
        )
    if district:
        qs = qs.filter(district__icontains=district)
    if metro:
        qs = qs.filter(metro__icontains=metro)
    if age.isdigit():
        a = int(age)
        qs = qs.filter(age_from__lte=a, age_to__gte=a)
    if price_from.isdigit():
        pf = int(price_from)
        qs = qs.filter(price_from__gte=pf)
    if price_to.isdigit():
        pt = int(price_to)
        qs = qs.filter(price_to__lte=pt)
    elif price_max.isdigit():
        # Backward compatibility with old query param.
        pm = int(price_max)
        qs = qs.filter(price_to__lte=pm)

    if sort == "price_asc":
        qs = qs.order_by("price_from", "-created_at")
    elif sort == "price_desc":
        qs = qs.order_by("-price_from", "-created_at")
    else:
        sort = "new"
        qs = qs.order_by("-created_at")

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    params = request.GET.copy()
    params.pop("page", None)
    query_without_page = params.urlencode()

    context = {
        "places": page_obj.object_list,
        "page_obj": page_obj,
        "language": request.LANGUAGE_CODE,
        "query_without_page": query_without_page,
        "meta_description": (
            "Новые кружки и курсы в Баку за последние 30 дней. Смотрите свежие добавления на KidsMap."
            if force_new_only
            else "Каталог детских секций и кружков в Баку. Фильтры по категории, району, метро, возрасту и цене."
        ),
        "selected": {
            "category": category,
            "q": query,
            "district": district,
            "metro": metro,
            "age": age,
            "price_from": price_from,
            "price_to": price_to,
            "sort": sort,
        },
        "categories": Place.CATEGORY_CHOICES,
        "district_options": BAKU_DISTRICTS,
        "metro_options": BAKU_METRO_STATIONS,
        "is_new_page": force_new_only,
    }
    _set_liked_flags(context["places"], liked_ids)
    return render(request, "catalog/place_list.html", context)


def place_detail_legacy(request, pk: int):
    place = get_object_or_404(Place.objects.filter(is_active=True), pk=pk)
    return redirect(place.get_absolute_url(), permanent=True)


def place_detail(request, pk: int, slug: str):
    place = get_object_or_404(Place.objects.filter(is_active=True).prefetch_related("gallery"), pk=pk)
    session_key = _session_key(request)
    liked_ids = set(PlaceLike.objects.filter(session_key=session_key).values_list("place_id", flat=True))
    if slug != place.slug:
        return redirect(place.get_absolute_url(), permanent=True)
    place.is_liked = place.id in liked_ids

    gallery = place.gallery_files()
    first_image_url = request.build_absolute_uri(gallery[0].url) if gallery else ""
    description = place.description_i18n(request.LANGUAGE_CODE) or place.name_i18n(request.LANGUAGE_CODE)
    schema = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": place.name_i18n(request.LANGUAGE_CODE),
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
    if place.lat is not None and place.lng is not None:
        schema["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": place.lat,
            "longitude": place.lng,
        }
        query = f"{place.lat},{place.lng}"
        map_embed_url = f"https://maps.google.com/maps?q={query}&z=15&output=embed"
        map_open_url = f"https://www.google.com/maps/search/?api=1&query={query}"
    else:
        map_embed_url = ""
        map_open_url = ""

    return render(
        request,
        "catalog/place_detail.html",
        {
            "place": place,
            "language": request.LANGUAGE_CODE,
            "meta_description": description[:160],
            "seo_image_url": first_image_url,
            "place_schema_json": json.dumps(schema, ensure_ascii=False),
            "map_embed_url": map_embed_url,
            "map_open_url": map_open_url,
        },
    )


@require_POST
def toggle_place_like(request, pk: int):
    place = get_object_or_404(Place, pk=pk, is_active=True)
    session_key = _session_key(request)

    with transaction.atomic():
        lock_place = Place.objects.select_for_update().get(pk=place.pk)
        existing_like = PlaceLike.objects.filter(place=lock_place, session_key=session_key)

        if existing_like.exists():
            existing_like.delete()
            liked = False
        else:
            try:
                PlaceLike.objects.create(place=lock_place, session_key=session_key)
            except IntegrityError:
                # Two parallel requests may race; unique constraint prevents duplicates.
                pass
            liked = True

        lock_place.likes_count = PlaceLike.objects.filter(place=lock_place).count()
        lock_place.save(update_fields=["likes_count"])

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "liked": liked, "likes_count": lock_place.likes_count})

    next_url = request.POST.get("next", "").strip()
    return redirect(next_url or place.get_absolute_url())


def seo_landing(request, seo_slug: str):
    page = SEO_LANDING_PAGES.get(seo_slug)
    if not page:
        raise Http404("SEO page not found")

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

    return render(
        request,
        "catalog/seo_landing.html",
        {
            "seo_page": page,
            "seo_pages": SEO_LANDING_PAGES,
            "meta_description": page["meta_description"],
            "breadcrumb_schema_json": json.dumps(breadcrumb_schema, ensure_ascii=False),
            "faq_schema_json": json.dumps(faq_schema, ensure_ascii=False),
        },
    )


def about(request):
    return render(
        request,
        "pages/about.html",
        {"meta_description": "О проекте KidsMap: каталог детских кружков и секций в Баку."},
    )


def contacts(request):
    return render(
        request,
        "pages/contacts.html",
        {"meta_description": "Контакты проекта KidsMap."},
    )
