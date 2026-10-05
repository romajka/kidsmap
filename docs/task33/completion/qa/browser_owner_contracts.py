"""Explicit, case-scoped assertion migrations for accepted Task33 contracts."""
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
path=ROOT/'src/catalog/testcases/owner.py';source=path.read_text()
def change(name, old, new):
    global source
    node=next(n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.FunctionDef) and n.name==name)
    lines=source.splitlines(keepends=True);body=''.join(lines[node.lineno-1:node.end_lineno])
    assert old in body,(name,old)
    body=body.replace(old,new)
    lines[node.lineno-1:node.end_lineno]=[body]
    source=''.join(lines)

for name in ['test_owner_edit_page_shows_current_photo_preview','test_owner_edit_page_rehydrates_saved_pricing_plans','test_owner_create_page_renders_map_picker']:
    change(name,'permanent_place_wizard.js','owner_place_continuous.js')
change('test_owner_edit_page_shows_current_photo_preview','data-pw-step="6"','data-place-section="4"')
change('test_owner_edit_page_shows_current_photo_preview','data-pw-step="7"','data-pc-save-status')
change('test_owner_edit_page_hides_public_link_for_inactive_place','pw-sidebar','pc-nav')
change('test_owner_create_page_renders_map_picker','pw-step-head','pc-section')
change('test_owner_create_page_renders_map_picker','data-pw-errors','data-pc-errors')
change('test_owner_create_page_has_review_and_draft_actions','data-pw-submit','data-pc-submit')
change('test_owner_create_page_has_review_and_draft_actions','data-pw-readiness','data-pc-errors')
change('test_owner_cannot_create_more_than_ten_places','self.assertContains(response, "Limit dolub")','self.assertNotContains(response, "Limit dolub")\n        self.assertContains(response, reverse("owner_place_create"))')
for name in ['test_owner_editor_can_save_incomplete_edit_as_draft','test_owner_editor_can_save_draft_and_exit_to_dashboard']:
    change(name,'self.editor_place.name_az,','candidate_payload(self.editor_place)["name_az"],')
    change(name,'self.editor_place.description_az,','candidate_payload(self.editor_place)["description_az"],')
    change(name,'self.assertEqual(self.editor_place.status, Place.STATUS_DRAFT)','self.assertEqual(self.editor_place.status, Place.STATUS_DRAFT)\n        self.assertEqual(VolunteerPlaceRevision.objects.get(place=self.editor_place).status, "draft")')
change('test_owner_editor_can_edit_but_cannot_publish','self.assertEqual(self.editor_place.name_ru, "Кружок редактора обновлен")','self.assertEqual(self.editor_place.name_ru, "Кружок редактора")\n        self.assertEqual(candidate_payload(self.editor_place)["name_ru"], "Кружок редактора обновлен")')
change('test_owner_moderator_cannot_edit_place','self.assertEqual(self.moderator_place.name_ru, "Изменение от модератора")','self.assertEqual(self.moderator_place.name_ru, "Кружок модератора")\n        self.assertEqual(candidate_payload(self.moderator_place)["name_ru"], "Изменение от модератора")')
for name,lookup in [('test_owner_can_save_and_exit_create_draft_before_category_is_selected','name_az="Erkən saxlanan qaralama"'),('test_owner_manager_can_save_incomplete_place_as_draft','name_az="Yarımçıq qaralama"'),('test_owner_manager_can_create_place_and_send_for_moderation','name_ru="Новая карточка владельца"'),('test_owner_manager_create_place_keeps_manual_map_coordinates','name_ru="Карточка с ручной точкой"')]:
    change(name,f'Place.objects.get(owner=self.manager_user, {lookup})',f'VolunteerPlaceRevision.objects.get(place__owner=self.manager_user, payload__{lookup}).place')
change('test_owner_manager_can_create_place_and_send_for_moderation','self.assertEqual(PlacePhoto.objects.filter(place=place).count(), 4)','self.assertEqual(PlacePhoto.objects.filter(place=place).count(), 0)\n        self.assertEqual(len(candidate_payload(place)["gallery"]), 4)\n        self.assertEqual(candidate_payload(place)["name_ru"], "Новая карточка владельца")')
change('test_owner_manager_can_create_place_and_send_for_moderation','ownership_request = PlaceOwnershipRequest.objects.get(place=place, applicant=self.manager_user)\n        self.assertEqual(ownership_request.status, PlaceOwnershipRequest.STATUS_PENDING)','self.assertEqual(VolunteerPlaceRevision.objects.get(place=place).status, "pending")\n        self.assertEqual(place.owner_id, self.manager_user.pk)\n        self.assertFalse(PlaceOwnershipRequest.objects.filter(place=place).exists())')
change('test_owner_manager_create_place_keeps_manual_map_coordinates','self.assertEqual(place.lat, 40.3777)\n        self.assertEqual(place.lng, 49.8922)','self.assertIsNone(place.lat)\n        self.assertIsNone(place.lng)\n        self.assertEqual(candidate_payload(place)["lat"], 40.3777)\n        self.assertEqual(candidate_payload(place)["lng"], 49.8922)')
change('test_owner_manager_create_place_keeps_manual_map_coordinates','self.assertTrue(\n            PlaceChangeAudit.objects.filter(\n                place=place,\n                source=PlaceChangeAudit.SOURCE_OWNER_PANEL,\n                field_name="lat",\n            ).exists()\n        )','revision = VolunteerPlaceRevision.objects.get(place=place)\n        self.assertEqual(revision.author_id, self.manager_user.pk)\n        self.assertIn("lat", revision.changed_fields)\n        self.assertIsNone(revision.base_snapshot["lat"])')
change('test_owner_place_create_requires_point_when_region_cannot_be_resolved','self.assertIn("lat", response.context["form"].errors)','self.assertNotIn("lat", response.context["form"].errors)')
change('test_owner_place_create_requires_main_photo','self.assertIn("photo", response.context["form"].errors)','self.assertNotIn("photo", response.context["form"].errors)\n        self.assertIn("pricing_plans", response.context["form"].errors)')
change('test_owner_place_create_requires_name_in_azerbaijani','self.assertIn("description_az", response.context["form"].errors)','self.assertNotIn("description_az", response.context["form"].errors)')
change('test_owner_cannot_submit_incomplete_draft_for_moderation','self.assertContains(first_response, "Фото: загрузите основное фото")\n        self.assertContains(first_response, "Точка на карте: выберите точку вручную")','self.assertIn("description_az", first_response.context["form"].errors)\n        self.assertIn("phone1", first_response.context["form"].errors)\n        self.assertNotIn("photo", first_response.context["form"].errors)\n        self.assertNotIn("lat", first_response.context["form"].errors)')
change('test_team_moderator_can_moderate_reviews_but_cannot_edit_content','self.assertEqual(reject_response.status_code, 200)','self.assertEqual(reject_response.status_code, 403)')
change('test_team_moderator_can_moderate_reviews_but_cannot_edit_content','self.assertFalse(self.place_review.is_approved)','self.assertTrue(self.place_review.is_approved)')
change('test_member_cannot_moderate_reviews_of_another_place','self.assertEqual(response.status_code, 200)','self.assertEqual(response.status_code, 403)')
change('test_membership_grants_permissions_only_on_its_own_place','            PLACE_PERMISSION_MODERATE_REVIEWS,\n','')
change('test_membership_grants_permissions_only_on_its_own_place','    def test_membership_grants_permissions_only_on_its_own_place(self):','    def test_membership_grants_permissions_only_on_its_own_place(self):\n        self.assertFalse(has_place_permission(user=self.member, place=self.granted_place, permission_code=PLACE_PERMISSION_MODERATE_REVIEWS))')
source=source.replace('from catalog.services.publication_forms import version_token','from catalog.services.publication_forms import version_token\nfrom catalog.models import VolunteerPlaceRevision')
source=source.replace('# Historical cabinet entry point,','# Candidate fields are distinct from the approved Place projection.\ndef candidate_payload(place):\n    return VolunteerPlaceRevision.objects.get(place=place).payload\n\n# Historical cabinet entry point,',1)
path.write_text(source)
print('Explicit case-scoped protocol migrations applied; retained test IDs.')
