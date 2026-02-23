from django.shortcuts import render, get_object_or_404
from .models import Place


def place_list(request):
    qs = Place.objects.all()

    category = request.GET.get("category", "").strip()
    district = request.GET.get("district", "").strip()
    age = request.GET.get("age", "").strip()
    price_max = request.GET.get("price_max", "").strip()

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

    context = {
        "places": qs,
        "selected": {
            "category": category,
            "district": district,
            "age": age,
            "price_max": price_max,
        },
        "categories": Place.CATEGORY_CHOICES,
    }
    return render(request, "catalog/place_list.html", context)

def place_detail(request, pk: int):
    place = get_object_or_404(Place, pk=pk)
    return render(request, "catalog/place_detail.html", {"place": place})


def about(request):
    return render(request, "pages/about.html")


def contacts(request):
    return render(request, "pages/contacts.html")
