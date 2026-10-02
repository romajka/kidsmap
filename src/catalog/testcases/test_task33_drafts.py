"""Stage09 transport, persistence and privacy regressions."""
import json
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from catalog.models import Place
from catalog.testcases.utils import create_quality_place


class DraftApiTests(TestCase):
    def setUp(self):
        user = get_user_model()
        self.owner = user.objects.create_user(username='draft_owner', password='synthetic')
        self.other = user.objects.create_user(username='draft_other', password='synthetic')
        self.place = create_quality_place(owner=self.owner, created_by=self.owner)
        self.client.force_login(self.owner)

    def post(self, data, url=None, client=None):
        return (client or self.client).post(url or reverse('server_draft_collection'),
            data=json.dumps(data), content_type='application/json')

    def test_incomplete_create_resume_and_retry_do_not_make_place(self):
        data={'target_type':'place','schema_version':1,'expected_version':0,'fields':{'description_az':'Yarımçıq'}}
        first=self.post(data);self.assertEqual(first.status_code,201,first.content)
        draft=first.json();self.assertEqual(draft['version'],1);self.assertEqual(draft['status'],'server_saved')
        self.assertIsNone(draft['target_id']);self.assertEqual(draft['fields']['description_az'],'Yarımçıq')
        second=self.post({**data,'draft_id':draft['draft_id'],'expected_version':1})
        self.assertEqual(second.status_code,200,second.content);self.assertEqual(second.json()['draft_id'],draft['draft_id'])
        self.assertEqual(Place.objects.count(),1)
        another=Client();another.force_login(self.owner)
        resumed=another.get(reverse('server_draft_detail',args=[draft['draft_id']]))
        self.assertEqual(resumed.status_code,200);self.assertEqual(resumed.json()['fields']['description_az'],'Yarımçıq')

    def test_edit_draft_never_writes_live_and_stale_version_preserves_input(self):
        old=self.place.description_az;version=self.place.content_version
        body={'target_type':'place','target_id':self.place.pk,'schema_version':1,'source_version':version,
              'expected_version':0,'fields':{'description_az':'First','price_from':'42'}}
        created=self.post(body);self.assertEqual(created.status_code,201,created.content)
        self.place.refresh_from_db();self.assertEqual(self.place.description_az,old)
        conflict=self.post({**body,'draft_id':created.json()['draft_id'],'fields':{'description_az':'Second'}})
        self.assertEqual(conflict.status_code,409);self.assertEqual(conflict.json()['submitted_fields']['description_az'],'Second')
        self.assertEqual(conflict.json()['version'],1)

    def test_foreign_actor_cannot_read_or_update(self):
        body={'target_type':'place','target_id':self.place.pk,'schema_version':1,'source_version':self.place.content_version,'expected_version':0,'fields':{'description_az':'Private'}}
        created=self.post(body);self.assertEqual(created.status_code,201,created.content)
        draft_id=created.json()['draft_id'];other=Client();other.force_login(self.other)
        self.assertEqual(other.get(reverse('server_draft_detail',args=[draft_id])).status_code,403)
        self.assertEqual(self.post({**body,'draft_id':draft_id,'expected_version':1},client=other).status_code,403)

    def test_revocation_stops_update_and_list_hides_draft(self):
        from catalog.models import OwnerTeamMembership
        grant=OwnerTeamMembership.objects.create(place=self.place,owner=self.owner,member=self.other,role='EDITOR')
        self.client.force_login(self.other)
        body={'target_type':'place','target_id':self.place.pk,'schema_version':1,'source_version':self.place.content_version,'expected_version':0,'fields':{'description_az':'Employee'}}
        created=self.post(body);self.assertEqual(created.status_code,201,created.content)
        grant.is_active=False;grant.save()
        draft_id=created.json()['draft_id']
        self.assertEqual(self.post({**body,'draft_id':draft_id,'expected_version':1}).status_code,403)
        self.assertEqual(self.client.get(reverse('server_draft_detail',args=[draft_id])).status_code,403)
        self.assertEqual(self.client.get(reverse('server_draft_collection')).json()['drafts'],[])

    def test_create_materialize_missing_name_then_idempotent(self):
        body={'target_type':'place','schema_version':1,'expected_version':0,'fields':{'description_az':'Short'}}
        created=self.post(body);self.assertEqual(created.status_code,201,created.content)
        url=reverse('server_draft_materialize',args=[created.json()['draft_id']])
        missing=self.client.post(url,data=json.dumps({'expected_version':1}),content_type='application/json')
        self.assertEqual(missing.status_code,422);self.assertEqual(Place.objects.count(),1)
        self.assertIn('fields',missing.json())

    def test_photo_requires_successful_upload_and_is_private(self):
        from io import BytesIO
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        body={'target_type':'place','schema_version':1,'expected_version':0,'fields':{}}
        created=self.post(body);draft_id=created.json()['draft_id']
        url=reverse('server_draft_photo',args=[draft_id]);detail=reverse('server_draft_detail',args=[draft_id])
        bad=self.client.post(url,{'expected_version':'1','photo':SimpleUploadedFile('bad.jpg',b'garbage',content_type='image/jpeg')})
        self.assertEqual(bad.status_code,422);self.assertFalse(self.client.get(detail).json()['photo_saved'])
        buffer=BytesIO();Image.new('RGB',(20,20),'red').save(buffer,'JPEG')
        uploaded=self.client.post(url,{'expected_version':'1','photo':SimpleUploadedFile('ok.jpg',buffer.getvalue(),content_type='image/jpeg')})
        self.assertEqual(uploaded.status_code,200,uploaded.content);self.assertTrue(uploaded.json()['photo_saved'])
        other=Client();other.force_login(self.other)
        self.assertEqual(other.get(url).status_code,403)
        self.assertEqual(self.client.get(url).status_code,200)

    def test_materialize_retry_returns_same_place(self):
        body={'target_type':'place','schema_version':1,'expected_version':0,'fields':{'name_az':'Fresh draft location','category':str(self.place.category_id)}}
        created=self.post(body);self.assertEqual(created.status_code,201,created.content)
        url=reverse('server_draft_materialize',args=[created.json()['draft_id']])
        first=self.client.post(url,data=json.dumps({'expected_version':1}),content_type='application/json')
        self.assertEqual(first.status_code,200,first.content)
        first_id=first.json()['materialized_place_id'];self.assertIsNotNone(first_id)
        second=self.client.post(url,data=json.dumps({'expected_version':1}),content_type='application/json')
        self.assertEqual(second.status_code,200,second.content)
        self.assertEqual(second.json()['materialized_place_id'],first_id)
        self.assertEqual(Place.objects.count(),2)
        new_place=Place.objects.get(pk=first_id)
        self.assertFalse(new_place.is_public)

    def test_client_draft_id_makes_first_post_idempotent(self):
        from uuid import uuid4
        identifier=str(uuid4())
        body={'draft_id':identifier,'target_type':'place','schema_version':1,'expected_version':0,'fields':{'description_az':'Network retry'}}
        first=self.post(body);self.assertIn(first.status_code,(200,201),first.content)
        second=self.post(body);self.assertEqual(second.status_code,200,second.content)
        self.assertEqual(second.json()['draft_id'],identifier);self.assertEqual(second.json()['version'],1)
        changed=self.post({**body,'fields':{'description_az':'Different'}})
        self.assertEqual(changed.status_code,409)
        from catalog.models import ServerDraft
        self.assertEqual(ServerDraft.objects.count(),1)

    def test_500_response_keeps_submitted_text(self):
        from unittest.mock import patch
        body={'target_type':'place','schema_version':1,'expected_version':0,'fields':{'description_az':'Unsaved text'}}
        with patch('catalog.controllers.server_draft_api.service.save',side_effect=OSError('synthetic storage unavailable')):
            response=self.post(body)
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.json()['submitted_fields']['description_az'],'Unsaved text')

    def test_account_switch_cannot_access_create_draft(self):
        created=self.post({'target_type':'place','schema_version':1,'expected_version':0,'fields':{'name_az':'Private'}})
        identifier=created.json()['draft_id'];other=Client();other.force_login(self.other)
        self.assertEqual(other.get(reverse('server_draft_detail',args=[identifier])).status_code,403)
        self.assertEqual(other.get(reverse('server_draft_collection')).json()['drafts'],[])

    def test_csrf_and_transport_reject_mutation_without_token(self):
        protected=Client(enforce_csrf_checks=True);protected.force_login(self.owner)
        body={'target_type':'place','schema_version':1,'expected_version':0,'fields':{}}
        denied=self.post(body,client=protected);self.assertEqual(denied.status_code,403)
        bad=self.post({**body,'owner_id':self.other.pk});self.assertEqual(bad.status_code,400)
        self.assertEqual(self.post({**body,'fields':{'photo':'places/public.png'}}).status_code,400)

    def test_changed_source_requires_reconciliation_before_update(self):
        body={'target_type':'place','target_id':self.place.pk,'schema_version':1,'source_version':self.place.content_version,'expected_version':0,'fields':{'description_az':'Private'}}
        created=self.post(body);self.assertEqual(created.status_code,201,created.content)
        Place.objects.filter(pk=self.place.pk).update(content_version=self.place.content_version+1)
        conflict=self.post({**body,'draft_id':created.json()['draft_id'],'expected_version':1,'fields':{'description_az':'New input'}})
        self.assertEqual(conflict.status_code,409);self.assertEqual(conflict.json()['submitted_fields']['description_az'],'New input')

    def test_materialize_keeps_uploaded_photo_outside_public_media(self):
        from io import BytesIO
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        from catalog.models import ServerDraft
        from catalog.services.server_drafts import private_storage
        body={'target_type':'place','schema_version':1,'expected_version':0,'fields':{'name_az':'Photo draft place','category':str(self.place.category_id)}}
        created=self.post(body);identifier=created.json()['draft_id']
        buffer=BytesIO();Image.new('RGB',(20,20),'blue').save(buffer,'JPEG')
        uploaded=self.client.post(reverse('server_draft_photo',args=[identifier]),{'expected_version':'1','photo':SimpleUploadedFile('blue.jpg',buffer.getvalue(),content_type='image/jpeg')})
        self.assertEqual(uploaded.status_code,200,uploaded.content)
        materialized=self.client.post(reverse('server_draft_materialize',args=[identifier]),data=json.dumps({'expected_version':2}),content_type='application/json')
        self.assertEqual(materialized.status_code,200,materialized.content)
        place=Place.objects.get(pk=materialized.json()['materialized_place_id'])
        self.assertFalse(bool(place.photo));self.assertFalse(place.is_public)
        draft=ServerDraft.objects.get(pk=identifier);self.assertTrue(private_storage().exists(draft.photo_name))

    def test_invalid_relation_and_numeric_type_leave_submitted_text(self):
        base={'target_type':'place','schema_version':1,'expected_version':0}
        foreign=self.post({**base,'fields':{'category':99999999}})
        self.assertEqual(foreign.status_code,400);self.assertEqual(foreign.json()['submitted_fields']['category'],99999999)
        numeric=self.post({**base,'fields':{'age_from':'not a number'}})
        self.assertEqual(numeric.status_code,400);self.assertEqual(numeric.json()['submitted_fields']['age_from'],'not a number')

    def test_private_responses_forbid_shared_cache(self):
        created=self.post({'target_type':'place','schema_version':1,'expected_version':0,'fields':{'description_az':'Private'}})
        identifier=created.json()['draft_id']
        for response in (created,self.client.get(reverse('server_draft_detail',args=[identifier])),self.client.get(reverse('server_draft_collection'))):
            self.assertIn('no-store',response.get('Cache-Control',''),response.status_code)


class DraftConcurrencyTests(__import__('django.test').test.TransactionTestCase):
    def test_two_devices_with_same_version_only_one_writes(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import close_old_connections
        from catalog.services import server_drafts
        user=get_user_model().objects.create_user(username='draft_race')
        draft=server_drafts.save(user=user,data={'target_type':'place','schema_version':1,'expected_version':0,'fields':{'description_az':'Base'}})
        barrier=Barrier(2)
        def write(value):
            close_old_connections();barrier.wait(timeout=5)
            try:
                changed=server_drafts.save(user=user,data={'draft_id':str(draft.pk),'target_type':'place','schema_version':1,'expected_version':1,'fields':{'description_az':value}})
                return ('saved',changed.version)
            except server_drafts.DraftConflict:
                return ('conflict',None)
            finally: close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(write,['Device A','Device B']))
        self.assertEqual(sorted(status for status,_ in results),['conflict','saved'])
        draft.refresh_from_db();self.assertEqual(draft.version,2)
        self.assertIn(draft.fields['description_az'],['Device A','Device B'])

    def test_simultaneous_first_retry_one_draft(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from uuid import uuid4
        from django.db import close_old_connections
        from catalog.services import server_drafts
        from catalog.models import ServerDraft
        user=get_user_model().objects.create_user(username='draft_first_race')
        identifier=str(uuid4());barrier=Barrier(2)
        payload={'draft_id':identifier,'target_type':'place','schema_version':1,'expected_version':0,'fields':{'description_az':'Same text'}}
        def create(_):
            close_old_connections();barrier.wait(timeout=5)
            try: return str(server_drafts.save(user=user,data=payload).pk)
            finally: close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool: ids=list(pool.map(create,[1,2]))
        self.assertEqual(ids,[identifier,identifier]);self.assertEqual(ServerDraft.objects.count(),1)
