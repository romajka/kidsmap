"""Independent stage22 negative contracts; synthetic fixtures and isolated QA04 only."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone,translation

from catalog.models import (PlaceReview, PlaceReviewReaction, Activity, Event, Specialist,
    Organization, AccountDeletionRequest, Category, SiteSettings)
from catalog.services.review_versions import (submit_review, moderate_candidate,
    normalize_reviews, rating_summary, respond_to_review, ReviewConflict, ReviewCooldown)
from catalog.testcases.utils import create_quality_place


class ReviewFixtures:
    def setUp(self):
        Category.objects.get_or_create(code='EDU',defaults={'name':'Fixture education'})
        User=get_user_model()
        self.author=User.objects.create_user('ind22-author',email='author22@example.invalid')
        self.owner=User.objects.create_user('ind22-owner')
        self.other=User.objects.create_user('ind22-other')
        self.staff=User.objects.create_superuser('ind22-reviewer','staff22@example.invalid','synthetic-only')
        self.place=create_quality_place(owner=self.owner,created_by=self.owner)
        self.activity=Activity.objects.create(place=self.place,status='published',name_az='Yerli fəaliyyət',description_az='Approved activity facts')
        self.specialist=Specialist.objects.create(owner=self.owner,name='Independent specialist',status='published',is_active=True)
        site=SiteSettings.get_solo();site.events_section_enabled=True;site.save(update_fields=['events_section_enabled'])
        self.event=Event.objects.create(owner=self.owner,name='Independent event',category=self.place.category,status='published',
            start_datetime=timezone.now()+timedelta(days=1),end_datetime=timezone.now()+timedelta(days=1,hours=1))

    def approved(self,target=None,rating=4):
        head, revision=submit_review(target=target or self.place,user=self.author,rating=rating,text='Approved synthetic review',author_name='Synthetic original author')
        moderate_candidate(head=head,revision_id=revision.pk,actor=self.staff,approve=True)
        head.refresh_from_db()
        return head,revision


@override_settings(PLACE_REVIEW_COOLDOWN_SECONDS=120)
class IndependentReviewContracts(ReviewFixtures,TestCase):
    def test_typed_rating_contributions_never_mix_and_pending_keeps_approved(self):
        targets=[self.place,self.activity,self.specialist,self.event]
        for rating,target in enumerate(targets,start=1):
            head,old=self.approved(target,rating)
            edited,new=submit_review(target=target,user=self.author,rating=5,text='Candidate private text')
            self.assertEqual(edited.pk,head.pk)
            self.assertEqual(rating_summary(target),{'average':float(rating),'count':1})
            self.assertEqual(edited.current_revision_id,old.pk)
            moderate_candidate(head=edited,revision_id=new.pk,actor=self.staff,approve=False)
            self.assertEqual(rating_summary(target),{'average':float(rating),'count':1})
        organization=Organization.objects.create(name_az='No combined rating')
        self.assertIsNone(rating_summary(organization))

    def test_legacy_selection_preserves_source_ids_texts_and_reactions(self):
        now=timezone.now()
        sources=[]
        for text,status,rating in [('Older approval','approved',2),('Later approval','approved',5),('Newest rejected','rejected',1)]:
            row=PlaceReview(place=self.place,user=self.author,text=text,rating=rating,status=status,is_current=False)
            row._version_service=True;row.save();sources.append(row)
        for index,row in enumerate(sources):
            PlaceReview.objects.filter(pk=row.pk).update(moderated_at=now+timedelta(seconds=index))
        reaction=PlaceReviewReaction.objects.create(review=sources[0],user=self.other,value=1)
        from django.db.models import Avg,Count
        before=PlaceReview.objects.filter(place=self.place,status='approved',is_approved=True).aggregate(average=Avg('rating'),count=Count('pk'))
        self.assertEqual(before,{'average':3.5,'count':2})
        normalize_reviews(PlaceReview)
        current=PlaceReview.objects.get(place=self.place,user=self.author,is_current=True)
        self.assertEqual(current.pk,sources[1].pk)
        self.assertEqual(set(PlaceReview.objects.filter(place=self.place).values_list('pk','text')), {(row.pk,row.text)for row in sources})
        reaction.refresh_from_db()
        self.assertEqual(reaction.review_id,sources[0].pk)
        self.assertEqual(reaction.revision.text,'Older approval')
        self.assertEqual(rating_summary(self.place),{'average':5.0,'count':1})
        normalize_reviews(PlaceReview)
        self.assertEqual(PlaceReview.objects.get(is_current=True,place=self.place).pk,current.pk)

    def test_unknown_authors_same_name_session_remain_separate_sources(self):
        a=PlaceReview.objects.create(place=self.place,text='Unknown A',author_name='Identical name',session_key='same',rating=2)
        b=PlaceReview.objects.create(place=self.place,text='Unknown B',author_name='Identical name',session_key='same',rating=5)
        normalize_reviews(PlaceReview)
        self.assertEqual(set(PlaceReview.objects.filter(place=self.place,is_current=True).values_list('pk',flat=True)),{a.pk,b.pk})
        self.assertEqual(rating_summary(self.place),{'average':3.5,'count':2})

    def test_owner_moderation_denied_but_reply_report_scoped(self):
        head,revision=self.approved()
        with self.assertRaises(PermissionError): moderate_candidate(head=head,revision_id=revision.pk,actor=self.owner,approve=False)
        with self.assertRaises(PermissionError): respond_to_review(head=head,actor=self.other,revision_id=revision.pk,kind='reply',text='Foreign reply')
        self.client.force_login(self.owner)
        for name in ('owner_review_approve','owner_review_reject'):
            self.assertEqual(self.client.post(reverse(name,args=[head.pk])).status_code,403)
        respond_to_review(head=head,actor=self.owner,revision_id=revision.pk,kind='reply',text='Public business reply')
        respond_to_review(head=head,actor=self.owner,revision_id=revision.pk,kind='report',text='Private business report')
        response=self.client.get(reverse('typed_reviews',args=['place',self.place.pk]))
        self.assertContains(response,'Public business reply')
        self.assertNotContains(response,'Private business report')
        head.refresh_from_db();self.assertEqual(head.current_revision_id,revision.pk)

    def test_cross_parent_reaction_and_stale_revision_are_rejected(self):
        head,revision=self.approved()
        other_place=create_quality_place()
        foreign,foreign_revision=self.approved(other_place)
        with self.assertRaises(ValidationError): PlaceReviewReaction.objects.create(review=head,revision=foreign_revision,user=self.other,value=1)
        self.client.force_login(self.other)
        response=self.client.post(reverse('typed_review_action',args=['place',head.pk,'react']),{'revision_id':foreign_revision.pk,'value':'1'})
        self.assertEqual(response.status_code,409)
        self.assertFalse(head.reactions.exists())

    def test_approval_starts_new_reaction_counter_and_preserves_old_pk(self):
        head,first=self.approved()
        old=PlaceReviewReaction.objects.create(review=head,revision=first,user=self.other,value=1)
        head,second=submit_review(target=self.place,user=self.author,rating=2,text='Revised approved text')
        moderate_candidate(head=head,revision_id=second.pk,actor=self.staff,approve=True)
        head.refresh_from_db()
        self.assertEqual((head.likes_count,head.dislikes_count),(0,0))
        old.refresh_from_db();self.assertEqual(old.revision_id,first.pk)
        self.assertEqual(old.revision.text,'Approved synthetic review')
        with self.assertRaises(ReviewConflict): respond_to_review(head=head,actor=self.owner,revision_id=first.pk,kind='reply',text='Stale reply')

    def test_staff_without_review_permission_cannot_approve_candidate(self):
        staff=get_user_model().objects.create_user('ind22-unprivileged-staff',is_staff=True)
        head,revision=submit_review(target=self.activity,user=self.author,rating=5,text='Private candidate')
        with self.assertRaises(PermissionError): moderate_candidate(head=head,revision_id=revision.pk,actor=staff,approve=True)
        head.refresh_from_db();self.assertIsNone(head.current_revision_id)

    def test_reply_rechecks_owner_revocation_at_locked_write_boundary(self):
        from catalog.models import Place
        from catalog.services.review_versions import business_can_respond
        head,revision=self.approved()
        first_check=True
        def revoke_after_check(**kwargs):
            nonlocal first_check
            permitted=business_can_respond(**kwargs)
            if first_check:
                first_check=False
                Place.objects.filter(pk=self.place.pk).update(owner=self.other,ownership_version=2)
            return permitted
        with patch('catalog.services.review_versions.business_can_respond',side_effect=revoke_after_check):
            with self.assertRaises(PermissionError):
                respond_to_review(head=head,actor=self.owner,revision_id=revision.pk,kind='reply',text='Former owner reply')
        self.assertFalse(revision.responses.exists())

    def test_hidden_target_rejects_public_submit_without_creating_review(self):
        Activity.objects.filter(pk=self.activity.pk).update(status='draft')
        self.client.force_login(self.author)
        response=self.client.post(reverse('typed_reviews',args=['activity',self.activity.pk]),{'rating':'5','text':'Hidden target attempt'})
        self.assertEqual(response.status_code,404)
        self.assertFalse(self.activity.reviews.exists())

    def test_staff_admin_renders_typed_workflow_links_and_readonly_version_history(self):
        self.client.force_login(self.staff)
        for kind,target in [('place',self.place),('activity',self.activity),('specialist',self.specialist),('event',self.event)]:
            with self.subTest(kind=kind):
                head,revision=self.approved(target)
                url=reverse('admin:catalog_'+head._meta.model_name+'_change',args=[head.pk])
                response=self.client.get(url)
                self.assertEqual(response.status_code,200)
                self.assertContains(response,reverse('typed_reviews',args=[kind,target.pk]))
                self.assertContains(response,revision.text)
                admin_form=response.context['adminform']
                self.assertTrue({field.name for field in head._meta.fields}.issubset(set(admin_form.readonly_fields)))
                self.assertFalse(admin_form.form.fields)
                self.assertNotContains(response,'name="text"')
                if kind=='place':
                    for action in ('approve','hide','reject'):
                        self.assertNotContains(response,'href="'+reverse('admin:catalog_placereview_'+action,args=[head.pk])+'"')
                    for stale in ('name="_save"','name="_continue"','Вы можете редактировать текст'):
                        self.assertNotContains(response,stale)
                    self.assertContains(response,'История отзыва доступна только для чтения')
        place_head=self.place.reviews.get(is_current=True)
        for lang,labels in [('az',('KidsMap yoxlaması','Tarixçə','Xidmət məlumatları və göstəricilər')),
                            ('en',('KidsMap review','History','Service details and metrics'))]:
            with self.subTest(admin_language=lang),translation.override(lang):
                self.client.cookies[settings.LANGUAGE_COOKIE_NAME]=lang
                response=self.client.get(reverse('admin:catalog_placereview_change',args=[place_head.pk]),HTTP_ACCEPT_LANGUAGE=lang)
                self.assertEqual(response.status_code,200)
                self.assertContains(response,'<html lang="'+lang+'"')
                for label in labels:
                    self.assertContains(response,label)
                self.assertFalse(response.context['adminform'].form.fields)

    def test_malformed_edit_revision_returns_client_error_without_candidate_write(self):
        head,revision=self.approved(self.activity)
        self.client.force_login(self.author)
        response=self.client.post(reverse('typed_reviews',args=['activity',self.activity.pk]),
            {'rating':'4','text':'Valid candidate body','expected_revision_id':'not-a-version'})
        self.assertEqual(response.status_code,400)
        head.refresh_from_db();self.assertEqual(head.current_revision_id,revision.pk)
        self.assertIsNone(head.candidate_revision_id)
        self.assertEqual(head.revisions.count(),1)
        self.client.force_login(self.staff)
        for malformed in ('²', '0', '-1', '9'*5000):
            with self.subTest(action_revision=malformed):
                response=self.client.post(reverse('typed_review_action',args=['activity',head.pk,'approve']),
                    {'revision_id':malformed})
                self.assertEqual(response.status_code,400)
                head.refresh_from_db();self.assertEqual(head.current_revision_id,revision.pk)
                self.assertIsNone(head.candidate_revision_id)
                self.assertEqual(head.revisions.count(),1)

    def test_published_event_review_route_and_deleted_event_visibility(self):
        self.assertEqual(self.client.get(reverse('typed_reviews',args=['event',self.event.pk])).status_code,200)
        Event.objects.filter(pk=self.event.pk).update(deleted_at=timezone.now())
        self.assertEqual(self.client.get(reverse('typed_reviews',args=['event',self.event.pk])).status_code,404)

    def test_event_review_route_does_not_expose_undated_expired_or_disabled_target(self):
        url=reverse('typed_reviews',args=['event',self.event.pk])
        original_start=self.event.start_datetime;original_end=self.event.end_datetime
        Event.objects.filter(pk=self.event.pk).update(start_datetime=None)
        self.assertEqual(self.client.get(url).status_code,404)
        Event.objects.filter(pk=self.event.pk).update(start_datetime=original_start,end_datetime=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.client.get(url).status_code,404)
        Event.objects.filter(pk=self.event.pk).update(end_datetime=original_end)
        site=SiteSettings.get_solo();site.events_section_enabled=False;site.save(update_fields=['events_section_enabled'])
        self.assertEqual(self.client.get(url).status_code,404)

    def test_voter_deletion_removes_all_typed_reactions_and_refreshes_visible_counters(self):
        from catalog.services.review_retention import dispose_typed_reviews
        from catalog.services.review_versions import review_types,refresh_reactions
        targets=[self.place,self.activity,self.specialist,self.event]
        heads=[]
        for target in targets:
            head,revision=self.approved(target)
            reaction_type=next(types[3]for types in review_types().values()if isinstance(head,types[1]))
            reaction_type.objects.create(review=head,revision=revision,user=self.other,value=1)
            refresh_reactions(head);head.refresh_from_db()
            self.assertEqual(head.likes_count,1)
            heads.append(head)
        dispose_typed_reviews(user_id=self.other.pk,disposition='anonymize_approved_delete_other')
        for head in heads:
            head.refresh_from_db();self.assertEqual((head.likes_count,head.dislikes_count),(0,0))
            self.assertFalse(head.reactions.filter(user=self.other).exists())
        # Exercise the full deletion hook too: Place reactions are removed
        # earlier than the shared typed-retention helper in that path.
        from catalog.services.account_deletion import finalize_account_deletion
        from catalog.testcases.test_account_deletion import TEST_POLICY
        for head in heads:
            reaction_type=next(types[3]for types in review_types().values()if isinstance(head,types[1]))
            reaction_type.objects.create(review=head,revision=head.current_revision,user=self.other,value=-1)
            refresh_reactions(head)
        cutoff=timezone.now()
        request=AccountDeletionRequest.objects.create(user=self.other,status='SCHEDULED',scheduled_for=cutoff,policy_version=TEST_POLICY['version'],policy_snapshot=TEST_POLICY)
        self.assertEqual(finalize_account_deletion(request.pk,now=cutoff).outcome,'completed')
        for head in heads:
            head.refresh_from_db();self.assertEqual((head.likes_count,head.dislikes_count),(0,0))
            self.assertFalse(head.reactions.exists())
            self.assertEqual(head.user_id,self.author.pk)

    def test_anonymization_covers_all_typed_approved_history_and_candidates(self):
        from catalog.services.review_retention import dispose_typed_reviews
        for target in [self.place,self.activity,self.specialist,self.event]:
            head,first=self.approved(target)
            head,second=submit_review(target=target,user=self.author,rating=3,text='Second approved',author_name='Second identity')
            moderate_candidate(head=head,revision_id=second.pk,actor=self.staff,approve=True)
            head,pending=submit_review(target=target,user=self.author,rating=1,text='Private pending identity',author_name='Candidate identity')
        deleted,anonymized=dispose_typed_reviews(user_id=self.author.pk,disposition='anonymize_approved_delete_other')
        self.assertEqual(anonymized,4)
        for target in [self.place,self.activity,self.specialist,self.event]:
            head=target.reviews.get(is_current=True)
            self.assertIsNone(head.user_id);self.assertEqual(head.author_name,'');self.assertTrue(head.is_anonymous)
            self.assertIsNone(head.candidate_revision_id)
            self.assertEqual(head.revisions.count(),2)
            for revision in head.revisions.all():
                self.assertEqual(revision.author_name,'');self.assertTrue(revision.is_anonymous)

    def test_disposition_delete_all_removes_all_typed_versions(self):
        from catalog.services.review_retention import dispose_typed_reviews
        for target in [self.place,self.activity,self.specialist,self.event]: self.approved(target)
        deleted,anonymized=dispose_typed_reviews(user_id=self.author.pk,disposition='delete_all')
        self.assertEqual((deleted,anonymized),(4,0))
        for target in [self.place,self.activity,self.specialist,self.event]: self.assertFalse(target.reviews.exists())

    def test_account_deletion_cutoff_is_not_early_and_includes_exact_boundary(self):
        from catalog.testcases.test_account_deletion import TEST_POLICY
        from catalog.services.account_deletion import finalize_account_deletion
        head,revision=self.approved(self.activity)
        cutoff=timezone.now()+timedelta(days=30)
        request=AccountDeletionRequest.objects.create(user=self.author,status='SCHEDULED',scheduled_for=cutoff,policy_version=TEST_POLICY['version'],policy_snapshot=TEST_POLICY)
        result=finalize_account_deletion(request.pk,now=cutoff-timedelta(microseconds=1))
        self.assertEqual(result.outcome,'skipped')
        head.refresh_from_db();self.assertEqual(head.user_id,self.author.pk)
        result=finalize_account_deletion(request.pk,now=cutoff)
        self.assertEqual(result.outcome,'completed')
        head.refresh_from_db();revision.refresh_from_db()
        self.assertIsNone(head.user_id);self.assertEqual(revision.author_name,'');self.assertTrue(revision.is_anonymous)


class IndependentReviewConcurrency(ReviewFixtures,TransactionTestCase):
    @override_settings(PLACE_REVIEW_COOLDOWN_SECONDS=120)
    def test_two_first_activity_submits_claim_only_one_candidate(self):
        barrier=Barrier(2)
        def submit(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    head,revision=submit_review(target=self.activity,user=self.author,rating=4,text=f'Concurrent candidate {index}',enforce_cooldown=True)
                    return ('submitted',head.pk)
                except ReviewCooldown: return ('cooldown',None)
            finally: close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(submit,[1,2]))
        self.assertEqual(sorted(status for status,pk in results),['cooldown','submitted'])
        self.assertEqual(self.activity.reviews.count(),1)
        self.assertEqual(self.activity.reviews.get().revisions.count(),1)

    def test_two_reviewers_decide_candidate_only_once(self):
        head,revision=submit_review(target=self.place,user=self.author,rating=5,text='One candidate')
        barrier=Barrier(2)
        def decide(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    moderate_candidate(head=head,revision_id=revision.pk,actor=self.staff,approve=True)
                    return 'approved'
                except ReviewConflict: return 'conflict'
            finally: close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(decide,[1,2]))
        self.assertEqual(sorted(results),['approved','conflict'])
        head.refresh_from_db();self.assertEqual(head.current_revision_id,revision.pk)
        self.assertEqual(head.revisions.count(),1)
