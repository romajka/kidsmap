from django.shortcuts import render, get_object_or_404
from .models import Place

def place_list(request):
    places = Place.objects.all()
    return render(request, "catalog/place_list.html", {"places": places})

def place_detail(request, pk: int):
    place = get_object_or_404(Place, pk=pk)
    return render(request, "catalog/place_detail.html", {"place": place})