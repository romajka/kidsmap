"""Same-origin staff adapters for the shared private editor transports."""
from django.contrib import admin
from django.urls import path

from catalog.controllers import server_draft_api
from catalog.controllers.place_editor_preview import place_editor_preview
from catalog.services.place_editor_drafts import _surface

app_name = 'admin_editor'


def _preview(request, pk, surface):
    _surface(request.user, surface)
    # Select the staff form server-side; query strings cannot change privileges.
    request.GET = request.GET.copy()
    request.GET['surface'] = surface
    return place_editor_preview(request, pk=pk)


def admin_preview(request, pk=None):
    return _preview(request, pk, 'admin')


def volunteer_preview(request, pk=None):
    return _preview(request, pk, 'volunteer')


urlpatterns = [
    path('drafts/', admin.site.admin_view(server_draft_api.draft_collection), name='server_draft_collection'),
    path('drafts/<uuid:draft_id>/', admin.site.admin_view(server_draft_api.draft_detail), name='server_draft_detail'),
    path('drafts/<uuid:draft_id>/photo/', admin.site.admin_view(server_draft_api.draft_photo), name='server_draft_photo'),
    path('drafts/<uuid:draft_id>/media/', admin.site.admin_view(server_draft_api.draft_media), name='server_draft_media'),
    path('drafts/<uuid:draft_id>/media/<uuid:media_id>/', admin.site.admin_view(server_draft_api.draft_media_file), name='server_draft_media_file'),
    path('drafts/<uuid:draft_id>/materialize/', admin.site.admin_view(server_draft_api.draft_materialize), name='server_draft_materialize'),
    path('places/preview/', admin.site.admin_view(admin_preview), name='place_editor_preview_new'),
    path('places/<int:pk>/preview/', admin.site.admin_view(admin_preview), name='place_editor_preview'),
    path('volunteer/places/preview/', admin.site.admin_view(volunteer_preview), name='volunteer_place_editor_preview_new'),
    path('volunteer/places/<int:pk>/preview/', admin.site.admin_view(volunteer_preview), name='volunteer_place_editor_preview'),
]
