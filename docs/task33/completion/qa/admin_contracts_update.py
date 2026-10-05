"""One-time, AST-scoped conversion of historical admin regression scenarios."""
import ast
from pathlib import Path

path = Path(__file__).resolve().parents[4] / 'src/catalog/testcases/admin.py'
source = path.read_text(encoding='utf-8')

def edit(name, old, new):
    global source
    tree = ast.parse(source)
    node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)
    lines = source.splitlines(keepends=True)
    text = ''.join(lines[node.lineno-1:node.end_lineno])
    assert old in text, name
    text = text.replace(old, new)
    source = ''.join(lines[:node.lineno-1]) + text + ''.join(lines[node.end_lineno:])

edit('create_reviewable_event', "'name': name, 'name_az': name, 'category_id': 'EDU',", "'name': name, 'name_az': name, 'description_az': 'Approved event description', 'category_id': 'EDU',")
edit('_admin_event_change_payload', '"event_format": event.event_format,', '"event_format": event.event_format,\n            "organizer_organization": str(event.organizer_organization_id or ""),\n            "organizer_specialist": str(event.organizer_specialist_id or ""),')
edit('test_place_admin_shows_coordinates_and_readiness_statuses', 'data-total="12"', 'data-total="10"')
edit('test_changelist_pagination_preserves_filters_search_and_sorting', 'district="Bakı",', 'district="baku_narimanov",')
edit('test_changelist_pagination_preserves_filters_search_and_sorting', 'district=baku', 'district=baku_narimanov')
edit('test_place_admin_bulk_action_regeocodes_selected_places', '40.5001', '40.409264')
edit('test_place_admin_bulk_action_regeocodes_selected_places', '49.9001', '49.867092')
edit('test_place_admin_bulk_action_regeocodes_selected_places', '40.1001', '40.4093')
edit('test_place_admin_bulk_action_regeocodes_selected_places', '49.1001', '49.8671')
edit('test_place_admin_can_add_change_and_delete_phone_numbers', '        self.assertEqual(self.place.phone1, "+994509998877")', '''        from catalog.models import VolunteerPlaceRevision
        from catalog.services import publication
        revision = VolunteerPlaceRevision.objects.get(place=self.place)
        self.assertEqual(revision.status, 'draft')
        self.assertEqual(self.place.phone1, '+994501112233')
        self.assertEqual(revision.payload['phone1'], '+994509998877')
        self.assertEqual(revision.payload['phone2'], '')
        self.assertEqual(revision.payload['phone3'], '+994703332211')
        revision = publication.propose(actor=self.superuser, target_type='place', target_id=self.place.pk,
            patch=revision.payload, schema_version=1, expected_version=self.place.content_version,
            revision_version=revision.version, submit=True)
        publication.review(actor=self.superuser, revision_id=revision.pk, version=revision.version, approve=True)
        self.place.refresh_from_db()
        self.assertEqual(self.place.phone1, "+994509998877")''')
edit('test_place_admin_can_save_place_as_draft_and_continue_later', '        payload = self._admin_place_change_payload()', '''        before = (self.place.status, self.place.is_active, self.place.published_at)
        payload = self._admin_place_change_payload(name_az='Candidate draft name')''')
edit('test_place_admin_can_save_place_as_draft_and_continue_later', '''        self.assertEqual(self.place.status, Place.STATUS_DRAFT)
        self.assertFalse(self.place.is_active)
        self.assertIsNone(self.place.published_at)''', '''        self.assertEqual((self.place.status, self.place.is_active, self.place.published_at), before)
        from catalog.models import VolunteerPlaceRevision
        revision = VolunteerPlaceRevision.objects.get(place=self.place)
        self.assertEqual(revision.status, 'draft')
        self.assertEqual(revision.payload['name_az'], 'Candidate draft name')
        continued = self.client.get(response['Location'])
        self.assertEqual(continued.status_code, 200)
        self.assertEqual(continued.context['adminform'].form['name_az'].value(), 'Candidate draft name')''')
edit('test_place_admin_saves_pricing_plans_from_change_form', '        self.assertEqual(len(self.place.pricing_plans), 2)', '''        from catalog.models import VolunteerPlaceRevision
        from catalog.services import publication
        revision = VolunteerPlaceRevision.objects.get(place=self.place)
        self.assertEqual(revision.status, 'draft')
        self.assertEqual(len(revision.payload['pricing_plans']), 2)
        self.assertEqual(self.place.pricing_plans, [])
        revision = publication.propose(actor=self.superuser, target_type='place', target_id=self.place.pk,
            patch=revision.payload, schema_version=1, expected_version=self.place.content_version,
            revision_version=revision.version, submit=True)
        publication.review(actor=self.superuser, revision_id=revision.pk, version=revision.version, approve=True)
        self.place.refresh_from_db()
        self.assertEqual(len(self.place.pricing_plans), 2)''')
edit('test_place_admin_saves_gallery_photo_with_draft', '        saved_photo = PlacePhoto.objects.get(place=self.place)', '''        from catalog.models import VolunteerPlaceRevision
        from catalog.services import publication
        revision = VolunteerPlaceRevision.objects.get(place=self.place)
        self.assertEqual(revision.status, 'draft')
        self.assertFalse(PlacePhoto.objects.filter(place=self.place).exists())
        self.assertEqual(len(revision.payload['gallery']), 1)
        self.assertEqual(revision.payload['gallery'][0]['order'], 1)
        revision = publication.propose(actor=self.superuser, target_type='place', target_id=self.place.pk,
            patch=revision.payload, schema_version=1, expected_version=self.place.content_version,
            revision_version=revision.version, submit=True)
        publication.review(actor=self.superuser, revision_id=revision.pk, version=revision.version, approve=True)
        saved_photo = PlacePhoto.objects.get(place=self.place)''')
# Expose form diagnostics for the remaining publication failures.
for name in ['test_event_admin_can_publish_from_change_form', 'test_place_admin_can_publish_ready_place_from_change_form']:
    edit(name, '        self.assertEqual(response.status_code, 302)', '''        if response.context and response.context.get('adminform'):
            self.assertFalse(response.context['adminform'].form.errors, response.context['adminform'].form.errors)
        self.assertEqual(response.status_code, 302)''')
ast.parse(source)
path.write_text(source, encoding='utf-8')
print('Applied scoped admin contract updates')
