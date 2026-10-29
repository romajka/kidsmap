from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connections, transaction, connection
from django.test import TestCase, TransactionTestCase
from catalog.models import Category, Place, VolunteerPlaceRevision, ServerDraft
from catalog.services.publication_forms import create_from_form


class PlaceIdentityCreateTests(TestCase):
    def setUp(self):
        self.editor=get_user_model().objects.create_superuser('create-identity-editor','','fictional')
        self.category=Category.objects.create(code='QA_CREATE_ID',name_az='Creation category')
        self.place=Place(slug='create-fixture',name='Balaca Club',name_az='Balaca Club',category=self.category,
            address='Original Avenue 10',created_by=self.editor,status='draft',is_active=False)
        Place.objects.bulk_create([self.place])
        VolunteerPlaceRevision.objects.create(place=self.place,author=self.editor,status='pending',
            payload={'name_az':'Saved Balaca Club','address':'Saved Avenue 20'})

    def form(self,name='Saved Balaca Club',address='Saved Avenue 20'):
        return SimpleNamespace(instance=Place(name=name,name_az=name,category=self.category,address=address),
            cleaned_data={'name':name},data={})

    def test_shared_create_rechecks_candidate_before_creating_base_or_saving_files(self):
        with patch('catalog.models.Place.objects.create') as create:
            with self.assertRaises(ValidationError):create_from_form(actor=self.editor,form=self.form(),submit=False)
        create.assert_not_called()
        self.assertEqual(Place.objects.count(),1)

    def test_shared_create_checks_stored_identity_even_when_candidate_was_renamed(self):
        with self.assertRaises(ValidationError):
            create_from_form(actor=self.editor,form=self.form('Balaca Club','Original Avenue 10'),submit=False)
        self.assertEqual(Place.objects.count(),1)

    def test_private_current_draft_can_be_excluded_without_hiding_other_places(self):
        from catalog.services.place_identity import guard_new_place
        draft=ServerDraft.objects.create(actor=self.editor,target_type='place',fields={
            'name_az':'Personal New Club','address':'Personal Street 30'})
        with self.assertRaises(ValidationError):guard_new_place(self.editor,draft.fields)
        guard_new_place(self.editor,draft.fields,exclude_draft_id=str(draft.pk))
        with self.assertRaises(ValidationError):
            guard_new_place(self.editor,{'name_az':'Saved Balaca Club','address':'Saved Avenue 20'},exclude_draft_id=str(draft.pk))

    def test_branch_confirmation_cannot_bypass_same_address_duplicate(self):
        form=self.form();form.cleaned_data['create_as_distinct_branch']=True
        with self.assertRaises(ValidationError):create_from_form(actor=self.editor,form=form,submit=False)


class PlaceIdentityRaceTests(TransactionTestCase):
    def test_two_actors_cannot_create_the_same_identity_at_once(self):
        if connection.vendor!='postgresql':self.skipTest('PostgreSQL transaction lock required')
        from catalog.services.place_identity import guard_new_place
        category=Category.objects.create(code='QA_RACE_ID',name_az='Race category')
        actors=[get_user_model().objects.create_superuser(f'race-identity-{i}','','fictional') for i in range(2)]
        barrier=Barrier(2)
        def create(actor_id):
            close_old_connections()
            try:
                actor=get_user_model().objects.get(pk=actor_id)
                barrier.wait(timeout=10)
                try:
                    with transaction.atomic():
                        values={'name_az':'Parallel Learning House','address':'Parallel Avenue 10'}
                        guard_new_place(actor,values)
                        Place.objects.create(name=values['name_az'],category=category,created_by=actor,
                            status='draft',is_active=False,**values)
                    return 'created'
                except ValidationError:return 'duplicate'
            finally:connections['default'].close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            result=list(pool.map(create,[actor.pk for actor in actors]))
        self.assertEqual(sorted(result),['created','duplicate'])
        self.assertEqual(Place.objects.filter(name_az='Parallel Learning House').count(),1)
