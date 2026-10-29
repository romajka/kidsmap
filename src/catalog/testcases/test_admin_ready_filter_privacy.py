"""Ready membership and counts must use the same authorized copy as each row."""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from catalog.models import Place, VolunteerPlaceRevision
from catalog.testcases.utils import create_ready_place


class AdminReadyFilterPrivacyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.editor = get_user_model().objects.create_superuser(
            "ready-filter-editor", "", "fictional"
        )
        cls.viewer = get_user_model().objects.create_user(
            "ready-filter-viewer", is_staff=True
        )
        cls.viewer.user_permissions.add(Permission.objects.get(
            content_type__app_label="catalog", codename="view_place"
        ))
        cls.place = create_ready_place(
            district="baku_nasimi", description_az="",
            status=Place.STATUS_DRAFT, is_active=False,
        )
        VolunteerPlaceRevision.objects.create(
            place=cls.place, author=cls.editor, status="draft",
            payload={"description_az": "Uşaqlar üçün saxlanmış özəl təsvir."},
        )

    def listing(self, user, *, ready=False):
        self.client.force_login(user)
        response = self.client.get(
            reverse("admin:catalog_place_changelist"),
            {"publication_state": "ready", "deleted_state": "active"} if ready else {},
        )
        self.assertEqual(response.status_code, 200)
        return response

    def test_view_only_ready_count_does_not_measure_private_saved_copy(self):
        response = self.listing(self.viewer)
        model_admin = admin.site._registry[Place]
        row = next(p for p in response.context["cl"].result_list if p.pk == self.place.pk)
        self.assertFalse(row.km_saved_candidate_allowed)
        self.assertFalse(model_admin._list_readiness(row).is_ready)
        counts = model_admin._place_dashboard_counts(response.wsgi_request)
        self.assertEqual(counts["quick_ready"], 0)
        self.assertEqual(counts["stat_ready"], 0)

    def test_view_only_ready_filter_excludes_live_incomplete_private_ready_card(self):
        response = self.listing(self.viewer, ready=True)
        self.assertEqual(list(response.context["cl"].result_list), [])

    def test_authorized_editor_sees_saved_ready_card_in_count_and_filter(self):
        response = self.listing(self.editor, ready=True)
        rows = list(response.context["cl"].result_list)
        self.assertEqual([p.pk for p in rows], [self.place.pk])
        self.assertTrue(rows[0].km_saved_candidate_allowed)
        model_admin = admin.site._registry[Place]
        self.assertTrue(model_admin._list_readiness(rows[0]).is_ready)
        counts = model_admin._place_dashboard_counts(response.wsgi_request)
        self.assertEqual(counts["quick_ready"], 1)
        self.assertEqual(counts["stat_ready"], 1)
