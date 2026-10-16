"""Actor/target/cutoff boundaries of explicit-save working-copy retirement."""
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from catalog.models import ServerDraft
from catalog.services import server_drafts, publication
from catalog.testcases.utils import create_quality_place

class StaleDraftRetirementTests(TestCase):
    def setUp(self):
        from catalog.testcases.utils import ensure_quality_subcategory
        ensure_quality_subcategory('EDU')
        self.owner=get_user_model().objects.create_user('offer07_test_owner')
        self.other=get_user_model().objects.create_user('offer07_test_other')
        self.place=create_quality_place(owner=self.owner,created_by=self.owner)
        self.second=create_quality_place(owner=self.owner,created_by=self.owner)
        self.cutoff=timezone.now()
    def draft(self, *, target=None, actor=None, newer=False):
        target=target or self.place
        d=ServerDraft.objects.create(actor=actor or self.owner,target_type='place',target_id=target.pk,schema_version=publication.SCHEMA_VERSION,source_version=target.content_version,fields={'description_az':'Preserve fictional input'},photo_name='drafts/fictional.webp')
        ServerDraft.objects.filter(pk=d.pk).update(saved_at=self.cutoff+timedelta(seconds=1) if newer else self.cutoff-timedelta(seconds=1))
        return d
    def finish(self, draft_id=None):
        return server_drafts.mark_explicit_save(user=self.owner,draft_id=draft_id,place=self.place,target_id=self.place.pk,cutoff=self.cutoff)
    def test_missing_id_retires_older_same_actor_target_and_preserves_payload(self):
        a=self.draft();self.finish();a.refresh_from_db()
        self.assertEqual(a.materialized_place_id,self.place.pk)
        self.assertEqual(a.fields,{'description_az':'Preserve fictional input'})
        self.assertEqual(a.photo_name,'drafts/fictional.webp')
    def test_newer_copy_is_not_retired_even_if_its_id_is_supplied(self):
        a=self.draft(newer=True);self.finish(str(a.pk));a.refresh_from_db();self.assertIsNone(a.materialized_place_id)
    def test_other_actor_and_other_target_are_preserved(self):
        mine=self.draft();foreign=self.draft(actor=self.other);second=self.draft(target=self.second)
        self.finish(str(mine.pk))
        foreign.refresh_from_db();second.refresh_from_db();self.assertIsNone(foreign.materialized_place_id);self.assertIsNone(second.materialized_place_id)
    def test_mismatched_id_does_not_authorize_retirement(self):
        mine=self.draft();foreign=self.draft(actor=self.other);self.finish(str(foreign.pk));mine.refresh_from_db();self.assertIsNone(mine.materialized_place_id)
    def test_creation_keeps_unrelated_null_target_drafts(self):
        data=dict(actor=self.owner,target_type='place',schema_version=publication.SCHEMA_VERSION,source_version=0,fields={})
        used=ServerDraft.objects.create(**data);other=ServerDraft.objects.create(**data)
        server_drafts.mark_explicit_save(user=self.owner,draft_id=str(used.pk),place=self.place,target_id=None,cutoff=self.cutoff)
        used.refresh_from_db();other.refresh_from_db();self.assertEqual(used.materialized_place_id,self.place.pk);self.assertIsNone(other.materialized_place_id)
    def test_consumed_copy_write_conflicts_and_completion_is_idempotent(self):
        d=self.draft();self.finish(str(d.pk));self.finish(str(d.pk));d.refresh_from_db()
        with self.assertRaises(server_drafts.DraftConflict):
            server_drafts.save(user=self.owner,data={'draft_id':str(d.pk),'target_type':'place','target_id':self.place.pk,'schema_version':publication.SCHEMA_VERSION,'source_version':d.source_version,'expected_version':d.version,'fields':d.fields})
    def test_unauthorized_actor_cannot_retire_owners_copy(self):
        from django.core.exceptions import PermissionDenied
        d=self.draft()
        with self.assertRaises(PermissionDenied):
            server_drafts.mark_explicit_save(user=self.other,draft_id=None,place=self.place,target_id=self.place.pk,cutoff=self.cutoff)
        d.refresh_from_db();self.assertIsNone(d.materialized_place_id)
    def test_invalid_explicit_ajax_save_leaves_draft_resumable(self):
        from uuid import uuid4
        from django.urls import reverse
        d=self.draft();self.client.force_login(self.owner)
        page=self.client.get(reverse('owner_place_edit',args=[self.place.pk]))
        response=self.client.post(reverse('owner_photo_edit_save',args=[self.place.pk]),{
            'photo_request_id':str(uuid4()),'form_action':'save_draft',
            'publication_token':page.context['form']['publication_token'].value(),
            'name_az':self.place.name_az,'description_az':self.place.description_az,
            'category':self.place.category_id,'nature':'business','nested_pricing':'{',
        })
        self.assertEqual(response.status_code,422,response.content[:200])
        d.refresh_from_db();self.assertIsNone(d.materialized_place_id)
    def test_consumed_copy_photo_write_conflicts_without_touching_history(self):
        d=self.draft();self.finish(str(d.pk));d.refresh_from_db()
        with self.assertRaises(server_drafts.DraftConflict):
            server_drafts.upload_photo(user=self.owner,draft_id=d.pk,expected_version=d.version,file=None)
        d.refresh_from_db();self.assertEqual(d.photo_name,'drafts/fictional.webp')
