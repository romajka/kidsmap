from django.urls import path

from .controllers.parent_guides import parent_guide

urlpatterns = [path('<slug:slug>/', parent_guide, name='parent_guide')]
