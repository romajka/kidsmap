from django.urls import path

from .controllers.parent_guides import parent_guide, parent_guide_index

urlpatterns = [
    path('', parent_guide_index, name='parent_guide_index'),
    path('<slug:slug>/', parent_guide, name='parent_guide'),
]
