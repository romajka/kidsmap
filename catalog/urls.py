from django.urls import path
from .views import place_list, place_detail

urlpatterns = [
    path("", place_list, name="place_list"),
    path("place/<int:pk>/", place_detail, name="place_detail"),
]