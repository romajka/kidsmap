from types import SimpleNamespace
from unittest.mock import Mock

from django.contrib import messages
from django.test import SimpleTestCase
from django.utils.translation import override

from catalog.controllers.owner_places_controller import OwnerPlacesController
from catalog.domain_admin.place_admin.operations import PlaceAdminOperationsMixin
from catalog.services.geocoding import PlaceGeocodingLookupResult, PlaceGeocodingResult


class GeocodingFeedbackTests(SimpleTestCase):
    def setUp(self):
        self.enterContext(override("ru"))

    def test_admin_and_owner_explain_ambiguous_matches_and_provider_errors(self):
        for reason, expected in (
            ("ambiguous", "Точный адрес не определён"),
            ("provider_error", "Сервис поиска адреса недоступен"),
        ):
            with self.subTest(reason=reason):
                result = PlaceGeocodingResult(updated=False, reason=reason)
                lookup = PlaceGeocodingLookupResult(resolved=False, reason=reason, query="ичери шяхяр")
                message, level = PlaceAdminOperationsMixin()._build_admin_coordinate_refresh_feedback(
                    geocoding_result=result, saved_prefix="Изменения сохранены."
                )
                self.assertIn(expected, str(message))
                self.assertNotEqual(level, messages.SUCCESS)
                self.assertIn(expected, OwnerPlacesController._build_create_geocoding_message(None, geocoding_result=lookup))
                self.assertIn(expected, OwnerPlacesController._build_manual_refresh_message(None, geocoding_result=result))

    def test_bulk_feedback_counts_only_truly_missing_addresses_as_missing(self):
        reasons = ["updated", "unchanged", "missing_query", "not_found", "ambiguous", "location_unresolved", "provider_error"]
        model_admin = Mock(spec=PlaceAdminOperationsMixin)
        model_admin.message_user = Mock()
        model_admin.geocoding_service = Mock()
        model_admin._refresh_place_coordinates_with_audit.side_effect = [
            PlaceGeocodingResult(updated=reason == "updated", reason=reason) for reason in reasons
        ]
        queryset = Mock()
        queryset.iterator.return_value = range(len(reasons))
        PlaceAdminOperationsMixin.refresh_coordinates(model_admin, SimpleNamespace(user=None), queryset)
        feedback = str(model_admin.message_user.call_args.args[1])
        for label in ("обновлено 1", "без изменений 1", "без адреса 1", "не найдено 1",
                      "требуют уточнения 2", "ошибки сервиса 1"):
            self.assertIn(label, feedback)
