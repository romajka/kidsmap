"""Unapplied SOCIAL12 candidate regression; own QA import path only."""
from datetime import timedelta
from django.test import TestCase,Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import override
from catalog.models import Activity,Specialist,Event,SiteSettings
from catalog.testcases.utils import create_ready_place
from catalog.services.review_versions import submit_review,moderate_candidate,review_types

class ReactionConflictRecoveryTests(TestCase):
 def setUp(self):
  U=get_user_model();self.author=U.objects.create_user('s12author');self.voter=U.objects.create_user('s12voter');self.inactive=U.objects.create_user('s12inactive',is_active=False);self.admin=U.objects.create_superuser('s12admin','s12@example.invalid','fictional')
  place=create_ready_place();spec=Specialist.objects.create(name='Fictional S12',status='published',is_active=True)
  self.targets={'place':place,'activity':Activity.objects.create(place=place,status='published',name_az='Fictional S12 activity'),'specialist':spec,'event':Event.objects.create(name='Fictional S12 event',name_az='Fictional S12 event',organizer_specialist=spec,organizer_resolution='resolved',category=place.category,status='published',event_format='online',start_datetime=timezone.now()+timedelta(days=5),end_datetime=timezone.now()+timedelta(days=5,hours=1))}
  site=SiteSettings.get_solo();site.events_section_enabled=site.specialists_section_enabled=True;site.save();self.cases={}
  for kind,target in self.targets.items():
   h,old=submit_review(target=target,user=self.author,rating=4,text='Fictional old current');moderate_candidate(head=h,revision_id=old.pk,actor=self.admin,approve=True)
   h,new=submit_review(target=target,user=self.author,rating=5,text='Fictional new current',expected_revision_id=old.pk);moderate_candidate(head=h,revision_id=new.pk,actor=self.admin,approve=True);self.cases[kind]=(h,old.pk,new.pk)
 def state(self,kind):
  h,_,_=self.cases[kind];h.refresh_from_db();return(h.current_revision_id,h.candidate_revision_id,h.likes_count,h.dislikes_count,review_types()[kind][3].objects.filter(review=h).count())
 def react(self,kind,revision,client=None):
  h,_,_=self.cases[kind];return(client or self.client).post(reverse('typed_review_action',args=[kind,h.pk,'react']),{'revision_id':revision,'value':'1'})
 def test_stale_reaction_offers_localized_get_recovery_without_write(self):
  self.client.force_login(self.voter)
  for kind,(_,old,new) in self.cases.items():
   before=self.state(kind)
   for lang in ['az','ru','en']:
    with self.subTest(kind=kind,lang=lang),override(lang):
     response=self.react(kind,old);self.assertEqual(response.status_code,409);self.assertContains(response,'data-review-reaction-conflict',status_code=409);self.assertTemplateUsed(response,'catalog/review_reaction_conflict.html');self.assertContains(response,'role="alert"',status_code=409);self.assertContains(response,'href="'+reverse('typed_reviews',args=[kind,self.targets[kind].pk])+'"',status_code=409);self.assertNotContains(response,'Fictional old current',status_code=409);self.assertEqual(self.state(kind),before)
 def test_current_reaction_toggle_and_counters_remain_unchanged(self):
  self.client.force_login(self.voter)
  for kind,(_,old,new) in self.cases.items():
   with self.subTest(kind=kind):
    self.assertEqual(self.react(kind,new).status_code,302);self.assertEqual(self.state(kind)[2:],(1,0,1));self.assertEqual(self.react(kind,new).status_code,302);self.assertEqual(self.state(kind)[2:],(0,0,0))
 def test_anonymous_inactive_and_self_keep_forbidden_response(self):
  for user in [None,self.inactive,self.author]:
   self.client.logout()
   if user:self.client.force_login(user)
   for kind,(_,old,new) in self.cases.items():
    with self.subTest(kind=kind,user=bool(user)):
     before=self.state(kind);response=self.react(kind,old);self.assertEqual(response.status_code,403);self.assertTemplateNotUsed(response,'catalog/review_reaction_conflict.html');self.assertEqual(self.state(kind),before)
 def test_missing_csrf_is_denied_before_recovery(self):
  client=Client(enforce_csrf_checks=True);client.force_login(self.voter)
  for kind,(_,old,new) in self.cases.items():
   with self.subTest(kind=kind):
    before=self.state(kind);response=self.react(kind,old,client);self.assertEqual(response.status_code,403);self.assertTemplateNotUsed(response,'catalog/review_reaction_conflict.html');self.assertEqual(self.state(kind),before)
