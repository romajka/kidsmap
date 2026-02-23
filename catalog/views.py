from django.shortcuts import render
from .models import Place

def place_list(request):
    places = Place.objects.all()
    return render(request, "catalog/place_list.html", {"places": places})