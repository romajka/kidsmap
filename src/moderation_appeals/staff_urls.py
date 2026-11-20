from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path("", admin.site.admin_view(views.queue), name="appeal_queue"),
    path("<int:pk>/", admin.site.admin_view(views.review), name="appeal_review"),
]
