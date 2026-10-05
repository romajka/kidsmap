"""Stage23 R1 contracts on QA04 disposable PostgreSQL; synthetic identities only."""
import hashlib
import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.serializers.json import DjangoJSONEncoder
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.translation import override

from catalog.models import (
    Organization, OrganizationGrant, Place, PlaceLike, PlacePhoto,
    PlaceReview, PlaceReviewReaction, PlaceReviewRevision, PricingPlan,
)
from catalog.services.business_team import has_action
from catalog.services.catalog_conversion import apply_plan, build_plan, reconciliation
from catalog.services.organization_ownership import request_join
from catalog.services.review_versions import submit_review, moderate_candidate, respond_to_review
from catalog.services.staff_roles import VOLUNTEER_GROUP
from catalog.testcases.utils import create_quality_place


def rows_digest(model):
    fields = [field.attname for field in model._meta.concrete_fields]
    rows = list(model.objects.order_by('pk').values_list(*fields))
    payload = json.dumps(rows, cls=DjangoJSONEncoder, sort_keys=True, separators=(',', ':'))
    return len(rows), hashlib.sha256(payload.encode()).hexdigest()


class R1AcceptanceTests(TestCase):
    def setUp(self):
        User = get_user_model()
        def account(name, **extra):
            return User.objects.create_user(username='qa23_' + name, email=name + '@example.invalid', **extra)
        self.parent = account('parent')
        self.standalone_owner = account('standalone')
        self.network_owner = account('network')
        self.selected_manager = account('selected')
        self.all_manager = account('all')
        self.volunteer = account('volunteer', is_staff=True)
        self.volunteer.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
        self.moderator = User.objects.create_superuser('qa23_moderator', 'moderator@example.invalid', 'synthetic')
        self.standalone = create_quality_place(owner=self.standalone_owner, created_by=self.standalone_owner,
                                               name='Standalone', name_az='Müstəqil', with_subcategory=True)
        self.branch_a = create_quality_place(owner=self.network_owner, created_by=self.network_owner,
                                             name='Branch A', name_az='Filial A', with_subcategory=True)
        self.branch_b = create_quality_place(owner=self.network_owner, created_by=self.network_owner,
                                             name='Branch B', name_az='Filial B', with_subcategory=True)
        self.same_address_other = create_quality_place(owner=self.standalone_owner, created_by=self.standalone_owner,
            name='Independent same address', name_az='Ayrı məkan', address=self.branch_a.address,
            lat=self.branch_a.lat, lng=self.branch_a.lng, with_subcategory=True)
        self.organization = Organization.objects.create(owner=self.network_owner, created_by=self.network_owner,
                                                         name_az='Süni şəbəkə')
        for branch in (self.branch_a, self.branch_b):
            request_join(actor=self.network_owner, place_id=branch.pk, organization_id=self.organization.pk)
            branch.refresh_from_db()
        for user, scope in ((self.selected_manager, 'selected_places'), (self.all_manager, 'all_network')):
            grant = OrganizationGrant.objects.create(organization=self.organization, owner=self.network_owner,
                member=user, role='EDITOR', actions=['place.view', 'place.edit', 'place.reviews.reply'], scope=scope,
                base_ownership_version=self.organization.ownership_version)
            if scope == 'selected_places':
                grant.selected_places.add(self.branch_a)

    def test_seven_roles_and_false_same_address_match(self):
        edit = lambda user, place: has_action(user=user, target=place, action='place.edit')
        self.assertFalse(edit(self.parent, self.standalone))
        self.assertTrue(edit(self.standalone_owner, self.standalone))
        self.assertFalse(edit(self.standalone_owner, self.branch_a))
        self.assertTrue(edit(self.network_owner, self.branch_a))
        self.assertTrue(edit(self.network_owner, self.branch_b))
        self.assertTrue(edit(self.selected_manager, self.branch_a))
        self.assertFalse(edit(self.selected_manager, self.branch_b))
        self.assertFalse(edit(self.selected_manager, self.same_address_other))
        self.assertTrue(edit(self.all_manager, self.branch_a))
        self.assertTrue(edit(self.all_manager, self.branch_b))
        self.assertFalse(edit(self.all_manager, self.same_address_other))
        self.assertFalse(edit(self.volunteer, self.branch_a))
        self.assertTrue(has_action(user=self.moderator, target=self.branch_a, action='place.publish'))
        self.assertFalse(has_action(user=self.network_owner, target=self.branch_a, action='place.publish'))
        self.assertFalse(has_action(user=self.selected_manager, target=self.branch_a, action='place.reviews.moderate'))

    def test_conversion_preserves_each_source_row_and_urls_after_resume(self):
        plan = PricingPlan.objects.create(place=self.standalone, product_type='lesson', price='31')
        photo = PlacePhoto.objects.create(place=self.standalone, image='places/gallery/qa23-synthetic.jpg')
        favorite = PlaceLike.objects.create(place=self.standalone, user=self.parent)
        review = PlaceReview.objects.create(place=self.standalone, user=self.parent, rating=4,
                                            text='Synthetic parent review', status='approved')
        reaction = PlaceReviewReaction.objects.create(review=review, user=self.selected_manager, value=1)
        models = (Place, PricingPlan, PlacePhoto, PlaceLike, PlaceReview, PlaceReviewRevision, PlaceReviewReaction)
        before = {model.__name__: rows_digest(model) for model in models}
        with override('az'):
            url_az = self.standalone.get_absolute_url()
        with override('ru'):
            url_ru = self.standalone.get_absolute_url()
        dry_run = build_plan()
        self.assertEqual({model.__name__: rows_digest(model) for model in models}, before)
        interrupted = apply_plan(dry_run, batch_size=1, max_batches=1)
        self.assertEqual(interrupted['checkpoint'], 1)
        completed = apply_plan(dry_run, batch_size=1)
        repeated = apply_plan(dry_run, batch_size=1)
        self.assertEqual(completed['checkpoint'], len(dry_run['entries']))
        self.assertEqual(repeated['checkpoint'], len(dry_run['entries']))
        self.assertEqual(reconciliation(dry_run['digest'])['mapping_total'], len(dry_run['entries']))
        self.assertEqual({model.__name__: rows_digest(model) for model in models}, before)
        for language, expected in (('az', url_az), ('ru', url_ru)):
            with override(language):
                self.assertEqual(Place.objects.get(pk=self.standalone.pk).get_absolute_url(), expected)
        self.assertEqual((plan.pk, photo.pk, favorite.pk, review.pk, reaction.pk),
                         (PricingPlan.objects.get(pk=plan.pk).pk, PlacePhoto.objects.get(pk=photo.pk).pk,
                          PlaceLike.objects.get(pk=favorite.pk).pk, PlaceReview.objects.get(pk=review.pk).pk,
                          PlaceReviewReaction.objects.get(pk=reaction.pk).pk))

    def test_post_conversion_review_actions_are_target_scoped_and_staff_moderated(self):
        conversion = build_plan()
        apply_plan(conversion, batch_size=2)
        head_a, candidate_a = submit_review(target=self.branch_a, user=self.parent, rating=5,
            text='Synthetic parent review A')
        head_b, candidate_b = submit_review(target=self.branch_b, user=self.parent, rating=4,
            text='Synthetic parent review B')
        with self.assertRaises(PermissionError):
            moderate_candidate(head=head_a, revision_id=candidate_a.pk, actor=self.network_owner, approve=True)
        moderate_candidate(head=head_a, revision_id=candidate_a.pk, actor=self.moderator, approve=True)
        moderate_candidate(head=head_b, revision_id=candidate_b.pk, actor=self.moderator, approve=True)
        respond_to_review(head=head_a, actor=self.network_owner, revision_id=candidate_a.pk,
                          kind='reply', text='Synthetic owner response')
        client = Client()
        client.force_login(self.selected_manager)
        def reply(head, revision):
            return client.post(reverse('typed_review_action', args=['place', head.pk, 'reply']),
                               {'revision_id': revision.pk, 'text': 'Synthetic manager response'})
        self.assertEqual(reply(head_a, candidate_a).status_code, 302)
        self.assertEqual(reply(head_b, candidate_b).status_code, 403)
        future = create_quality_place(owner=self.network_owner, created_by=self.network_owner,
                                      name='Future branch', name_az='Yeni filial', with_subcategory=True)
        request_join(actor=self.network_owner, place_id=future.pk, organization_id=self.organization.pk)
        self.assertTrue(has_action(user=self.all_manager, target=future, action='place.edit'))
        self.assertFalse(has_action(user=self.selected_manager, target=future, action='place.edit'))

    def test_volunteer_proposal_requires_separate_staff_decision(self):
        from catalog.models import VolunteerPlaceRevision
        from catalog.services import volunteer_proposals, publication
        organization = volunteer_proposals.create_and_propose(actor=self.volunteer, kind='organization',
            patch={'name_az': 'Könüllü təşkilat', 'description_az': 'Sintetik könüllü təklifi'}, submit=True)
        revision = VolunteerPlaceRevision.objects.get(organization=organization.organization)
        organization.organization.refresh_from_db()
        self.assertNotEqual(organization.organization.status, 'published')
        self.assertFalse(has_action(user=self.volunteer, target=organization.organization, action='organization.edit'))
        publication.review(actor=self.moderator, revision_id=revision.pk, version=revision.version, approve=True)
        organization.organization.refresh_from_db()
        self.assertEqual(organization.organization.status, 'published')
        self.assertIsNone(organization.organization.owner_id)

    def test_new_post_switch_row_survives_conversion_reconciliation(self):
        plan = build_plan()
        apply_plan(plan, batch_size=2)
        new_place = create_quality_place(owner=self.standalone_owner, created_by=self.standalone_owner,
                                         name='Post-switch row', name_az='Sonrakı yer', with_subcategory=True)
        self.assertFalse(reconciliation(plan['digest'])['retained_counts_match'])
        self.assertTrue(Place.objects.filter(pk=new_place.pk, name_az='Sonrakı yer').exists())
