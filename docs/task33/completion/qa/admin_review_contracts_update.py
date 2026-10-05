"""Retain old regression IDs while exercising the approved versioned review API."""
import ast
from pathlib import Path
path=Path(__file__).resolve().parents[4]/'src/catalog/testcases/admin.py'
source=path.read_text(encoding='utf-8')
def replace(name, body):
    global source
    n=next(n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.FunctionDef) and n.name==name)
    lines=source.splitlines(keepends=True)
    source=''.join(lines[:n.lineno-1])+f'    def {name}(self):\n'+body+'\n'+''.join(lines[n.end_lineno:])

source=source.replace('\n\nclass TestAdminTemporaryEventInputs', '''

def create_pending_review(target, rating, text):
    from catalog.services.review_versions import submit_review
    author = User.objects.create_user('versioned_review_' + str(User.objects.count()))
    return submit_review(target=target, user=author, rating=rating, text=text)[0]


class TestAdminTemporaryEventInputs''',1)
replace('test_review_action_approve_and_reject', '''        place = create_quality_place(name='Review Place')
        first = create_pending_review(place, 5, 'Good')
        second = create_pending_review(place, 1, 'Needs review')
        response = self.client.post(reverse('admin:catalog_placereview_changelist'),
            {'action':'approve_selected', '_selected_action':[first.pk]})
        self.assertEqual(response.status_code, 302)
        first.refresh_from_db(); self.assertEqual(first.status, 'pending')
        self.assertEqual(decide_typed_review(self.client, first, kind='place', approve=True).status_code, 302)
        self.assertEqual(decide_typed_review(self.client, second, kind='place', approve=False).status_code, 302)
        first.refresh_from_db(); second.refresh_from_db(); place.refresh_from_db()
        self.assertEqual(first.status, 'approved'); self.assertTrue(first.is_approved)
        self.assertEqual(second.status, 'rejected'); self.assertFalse(second.is_approved)
        self.assertEqual(place.rating_count, 1); self.assertEqual(place.rating_avg, 5)
''')
replace('test_place_review_admin_bulk_hide_and_approve_actions', '''        from catalog.services.review_versions import submit_review
        review = create_pending_review(self.place, 4, 'Helpful review')
        self.assertEqual(decide_typed_review(self.client, review, kind='place', approve=True).status_code, 302)
        review.refresh_from_db(); approved_id = review.current_revision_id
        for action in ('hide_selected', 'approve_selected'):
            response = self.client.post(reverse('admin:catalog_placereview_changelist'),
                {'action':action, '_selected_action':[review.pk], 'index':0}, follow=True)
            self.assertEqual(response.status_code, 200)
            review.refresh_from_db()
            self.assertTrue(review.is_approved); self.assertEqual(review.current_revision_id, approved_id)
        review, candidate = submit_review(target=self.place, user=review.user, rating=3, text='New version')
        self.assertEqual(decide_typed_review(self.client, review, kind='place', approve=True).status_code, 302)
        review.refresh_from_db()
        self.assertEqual(review.current_revision_id, candidate.pk); self.assertEqual(review.rating, 3)
''')
replace('test_place_review_admin_moderation_views_update_visibility', '''        from catalog.services.review_versions import submit_review
        review = create_pending_review(self.place, 2, 'Needs review')
        url = reverse('typed_review_action', args=['place',review.pk,'approve'])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(decide_typed_review(self.client, review, kind='place', approve=True).status_code, 302)
        review.refresh_from_db(); approved_id = review.current_revision_id
        review, candidate = submit_review(target=self.place, user=review.user, rating=1, text='Rejected update')
        self.assertEqual(decide_typed_review(self.client, review, kind='place', approve=False).status_code, 302)
        review.refresh_from_db(); candidate.refresh_from_db()
        self.assertTrue(review.is_approved); self.assertEqual(review.rating, 2)
        self.assertEqual(review.current_revision_id, approved_id)
        self.assertEqual(candidate.status, 'rejected'); self.assertIsNone(review.candidate_revision_id)
        self.assertEqual(self.client.post(url, {'revision_id':candidate.pk}).status_code, 409)
''')
replace('test_place_review_bulk_approve_updates_place_rating_stats', '''        first = create_pending_review(self.place, 5, 'Great place!')
        second = create_pending_review(self.place, 4, 'Good place!')
        self.place.refresh_from_db()
        self.assertEqual(self.place.rating_count, 0); self.assertEqual(self.place.rating_avg, 0)
        legacy = self.client.post(reverse('admin:catalog_placereview_changelist'),
            {'action':'approve_selected', '_selected_action':[first.pk, second.pk]}, follow=True)
        self.assertEqual(legacy.status_code, 200)
        self.place.refresh_from_db(); self.assertEqual(self.place.rating_count, 0)
        for head in (first, second):
            self.assertEqual(decide_typed_review(self.client, head, kind='place', approve=True).status_code, 302)
        self.place.refresh_from_db()
        self.assertEqual(self.place.rating_count, 2); self.assertEqual(self.place.rating_avg, 4.5)
''')
replace('test_specialist_review_bulk_approve_updates_specialist_rating_stats', '''        review = create_pending_review(self.specialist, 5, 'Awesome specialist!')
        self.specialist.refresh_from_db(); self.assertEqual(self.specialist.rating_count, 0)
        legacy = self.client.post(reverse('admin:catalog_specialistreview_changelist'),
            {'action':'approve_selected', '_selected_action':[review.pk]}, follow=True)
        self.assertEqual(legacy.status_code, 200)
        self.specialist.refresh_from_db(); self.assertEqual(self.specialist.rating_count, 0)
        self.assertEqual(decide_typed_review(self.client, review, kind='specialist', approve=True).status_code, 302)
        self.specialist.refresh_from_db()
        self.assertEqual(self.specialist.rating_count, 1); self.assertEqual(self.specialist.rating_avg, 5)
''')
ast.parse(source); path.write_text(source,encoding='utf-8')
print('Versioned admin review regression scenarios updated')
