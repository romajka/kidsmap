from django.urls import path
from .views import home, place_list, place_detail, about, contacts

urlpatterns = [
    path("", home, name="home"),
    path("catalog/", place_list, name="place_list"),
    path("about/", about, name="about"),
    path("contacts/", contacts, name="contacts"),
    path("place/<int:pk>/", place_detail, name="place_detail"),
]
