from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Place


def place_list(request):
    qs = Place.objects.filter(is_active=True)

    category = request.GET.get("category", "").strip()
    district = request.GET.get("district", "").strip()
    age = request.GET.get("age", "").strip()
    price_max = request.GET.get("price_max", "").strip()
    sort = request.GET.get("sort", "new").strip()

    if category:
        qs = qs.filter(category=category)
    if district:
        qs = qs.filter(district__icontains=district)
    if age.isdigit():
        a = int(age)
        qs = qs.filter(age_from__lte=a, age_to__gte=a)
    if price_max.isdigit():
        pm = int(price_max)
        qs = qs.filter(price_from__lte=pm)

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
            "age": age,
            "price_max": price_max,
            "sort": sort,
        },
        "categories": Place.CATEGORY_CHOICES,
    }
    return render(request, "catalog/place_list.html", context)

def place_detail(request, pk: int):
    place = get_object_or_404(Place, pk=pk)
    return render(
        request,
        "catalog/place_detail.html",
        {"place": place, "language": request.LANGUAGE_CODE},
    )


def about(request):
    return render(request, "pages/about.html")


def contacts(request):
    return render(request, "pages/contacts.html")
