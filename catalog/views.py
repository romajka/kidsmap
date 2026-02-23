from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Place

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


def home(request):
    categories = [
        {"code": "SPRT", "title": "Спорт"},
        {"code": "ART", "title": "Творчество"},
        {"code": "MUS", "title": "Музыка и сцена"},
        {"code": "EDU", "title": "Образование"},
        {"code": "TECH", "title": "Технологии"},
        {"code": "FUN", "title": "Досуг"},
    ]
    return render(request, "pages/home.html", {"home_categories": categories})


def place_list(request):
    qs = Place.objects.filter(is_active=True)

    category = request.GET.get("category", "").strip()
    district = request.GET.get("district", "").strip()
    metro = request.GET.get("metro", "").strip()
    age = request.GET.get("age", "").strip()
    price_from = request.GET.get("price_from", "").strip()
    price_to = request.GET.get("price_to", "").strip()
    price_max = request.GET.get("price_max", "").strip()
    sort = request.GET.get("sort", "new").strip()

    if category:
        qs = qs.filter(category=category)
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
        "selected": {
            "category": category,
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
    }
    return render(request, "catalog/place_list.html", context)

def place_detail(request, pk: int):
    place = get_object_or_404(Place.objects.prefetch_related("gallery"), pk=pk)
    return render(
        request,
        "catalog/place_detail.html",
        {"place": place, "language": request.LANGUAGE_CODE},
    )


def about(request):
    return render(request, "pages/about.html")


def contacts(request):
    return render(request, "pages/contacts.html")
