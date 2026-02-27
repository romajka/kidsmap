from django.urls import path
from .views import (
    home,
    place_list,
    place_new,
    place_detail,
    place_detail_legacy,
    toggle_place_like,
    add_place_review,
    add_site_review,
    track_event,
    seo_landing,
    about,
    contacts,
)

urlpatterns = [
    path("", home, name="home"),
    path("catalog/", place_list, name="place_list"),
    path("catalog/new/", place_new, name="place_new"),
    path("catalog/<slug:seo_slug>/", seo_landing, name="seo_landing"),
    path("about/", about, name="about"),
    path("contacts/", contacts, name="contacts"),
    path("place/<int:pk>/", place_detail_legacy, name="place_detail_legacy"),
    path("place/<int:pk>-<str:slug>/", place_detail, name="place_detail"),
    path("place/<int:pk>/like/", toggle_place_like, name="toggle_place_like"),
    path("place/<int:pk>/review/", add_place_review, name="add_place_review"),
    path("review/", add_site_review, name="add_site_review"),
    path("events/track/", track_event, name="track_event"),
]
