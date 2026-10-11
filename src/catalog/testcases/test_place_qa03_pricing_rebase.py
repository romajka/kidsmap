"""Canonical immediate price projections must not conflict with their own candidate."""
import copy
from decimal import Decimal
from unittest.mock import patch
from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from catalog.models import Place, VolunteerPlaceRevision
from catalog.services.volunteer_places import revision_base_matches
from catalog.testcases.test_task33_publication import PublicationFixture


class MixedProjectionTests(PublicationFixture,TestCase):
    def setUp(self):
        super().setUp()
        plan = self.place.pricing_plan_records.get(); plan.price=Decimal('15.00'); plan.save()
        self.place.refresh_from_db()

    def mixed(self,submit=False,extra=None):
        incoming = self.s.snapshot(self.place,'place')
        incoming.update(name_ru='QA candidate identity',address='QA candidate address')
        incoming['pricing_plans'][0]['price']='18.00'
        if extra: incoming.update(extra)
        return self.propose(incoming,submit=submit)

    def resubmit(self,revision):
        self.place.refresh_from_db()
        incoming = self.s.snapshot(self.place,'place'); incoming.update(copy.deepcopy(revision.payload))
        return self.propose(incoming,revision_version=revision.version)

    def test_mixed_draft_rebases_projections_without_echo_rollback(self):
        old_identity = self.place.name_ru
        revision = self.mixed(); self.place.refresh_from_db()
        live = self.s.snapshot(self.place,'place')
        self.assertEqual(self.place.price_from,Decimal('18.00'))
        self.assertEqual(self.place.name_ru,old_identity)
        for field in self.s.PRICES:
            self.assertEqual(revision.base_snapshot[field],live[field],field)
            self.assertNotIn(field,revision.payload)

    def test_save_reload_submit_review_has_no_self_conflict(self):
        revision = self.resubmit(self.mixed())
        self.assertTrue(revision_base_matches(revision,self.place))
        self.client.force_login(self.staff)
        response = self.client.get(reverse('admin:volunteer_review',args=[self.place.pk]))
        self.assertFalse(response.context['conflict'])
        self.assertContains(response,'value="approve"')
        self.approve(revision); self.place.refresh_from_db()
        self.assertEqual(self.place.name_ru,'QA candidate identity')
        self.assertEqual(self.place.address,'QA candidate address')
        self.assertEqual(self.place.price_from,Decimal('18.00'))

    def test_direct_submit_and_repeat_price_only_keep_tariff_identity(self):
        plan_id = self.place.pricing_plan_records.get().pk
        self.approve(self.mixed(submit=True))
        self.place.refresh_from_db()
        self.assertEqual(self.place.price_from,Decimal('18.00'))
        self.assertEqual(self.place.pricing_plan_records.get().pk,plan_id)
        revision = VolunteerPlaceRevision.objects.get(place=self.place)
        incoming = self.s.snapshot(self.place,'place')
        incoming['pricing_plans'][0]['price']='21.00'
        revision = self.propose(incoming,revision_version=revision.version)
        self.approve(revision); self.place.refresh_from_db()
        self.assertEqual(self.place.price_from,Decimal('21.00'))
        self.assertEqual(self.place.pricing_plan_records.get().pk,plan_id)

    def test_real_second_writer_conflict_is_retained(self):
        revision = self.resubmit(self.mixed())
        Place.objects.filter(pk=self.place.pk).update(name_ru='QA other editor')
        self.assertFalse(revision_base_matches(revision,Place.objects.get(pk=self.place.pk)))
        with self.assertRaises(ValidationError): self.approve(revision)
        self.assertEqual(Place.objects.get(pk=self.place.pk).name_ru,'QA other editor')

    def test_nonoverlapping_second_writer_field_is_preserved(self):
        revision = self.resubmit(self.mixed())
        Place.objects.filter(pk=self.place.pk).update(phone1='0501112223')
        self.approve(revision); self.place.refresh_from_db()
        self.assertEqual(self.place.phone1,'0501112223')

    def test_stale_source_and_candidate_versions_cannot_write(self):
        source = self.place.content_version; revision = self.mixed()
        with self.assertRaises(ValidationError):
            self.propose({'name_ru':'Stale source'},expected_version=source,revision_version=revision.version)
        with self.assertRaises(ValidationError):
            self.propose({'name_ru':'Stale revision'},revision_version=revision.version-1)
        self.place.refresh_from_db(); self.assertEqual(self.place.price_from,Decimal('18.00'))

    def test_exception_after_immediate_write_rolls_back_all_changes(self):
        before = self.s.snapshot(self.place,'place'); version = self.place.content_version
        with patch.object(VolunteerPlaceRevision,'save',side_effect=RuntimeError('QA failed revision write')):
            with self.assertRaises(RuntimeError): self.mixed()
        self.place.refresh_from_db()
        self.assertEqual(self.s.snapshot(self.place,'place'),before)
        self.assertEqual(self.place.content_version,version)
        self.assertFalse(VolunteerPlaceRevision.objects.filter(place=self.place).exists())

    def test_structure_and_nonexplicit_changes_remain_gated(self):
        for nonexplicit in (True,False):
            incoming = copy.deepcopy(self.place.pricing_plans)
            incoming[0]['price']='18.00'
            if not nonexplicit: incoming[0]['title_az']='New gated condition'
            revision = self.propose({'pricing_plans':incoming},explicit_save=not nonexplicit,submit=False,
                revision_version=VolunteerPlaceRevision.objects.filter(place=self.place).values_list('version',flat=True).first() or 0)
            self.place.refresh_from_db()
            self.assertEqual(self.place.price_from,Decimal('15.00'))
            self.assertIn('pricing_plans',revision.payload)

    def test_explicit_different_projection_is_not_discarded_as_an_echo(self):
        revision=self.mixed(extra={'price_from':'19.00'})
        self.place.refresh_from_db()
        self.assertEqual(self.place.price_from,Decimal('18.00'))
        self.assertEqual(revision.base_snapshot['price_from'],'18.00')
        self.assertEqual(revision.payload['price_from'],'19.00')

    def test_all_five_projection_fields_and_range_bounds_rebase(self):
        cases=[('lesson',1,'one_time','',None,False,'price_per_lesson'),
               ('lesson',8,'one_time','',None,False,'price_per_8_lessons'),
               ('membership',1,'recurring','month',1,False,'price_per_month'),
               ('lesson',1,'one_time','',None,True,'price_to')]
        for product,quantity,billing,interval,count,ranged,field in cases:
            with self.subTest(field=field):
                VolunteerPlaceRevision.objects.filter(place=self.place).delete()
                plan=self.place.pricing_plan_records.get()
                plan.product_type=product;plan.quantity=quantity;plan.quantity_unit='lesson' if product=='lesson' else ''
                plan.billing_mode=billing;plan.billing_interval=interval;plan.billing_interval_count=count
                plan.price_kind='range' if ranged else 'exact';plan.price=None if ranged else Decimal('15.00')
                plan.price_min=Decimal('15.00') if ranged else None;plan.price_max=Decimal('17.00') if ranged else None
                plan.save();self.place.refresh_from_db()
                incoming=self.s.snapshot(self.place,'place');incoming['name_ru']='QA projected identity'
                if ranged:incoming['pricing_plans'][0].update(price_min='18.00',price_max='20.00')
                else:incoming['pricing_plans'][0]['price']='18.00'
                revision=self.propose(incoming,submit=False);self.place.refresh_from_db()
                live=self.s.snapshot(self.place,'place')
                self.assertEqual(live[field],'20.00' if ranged else '18.00')
                for key in self.s.PRICES:
                    self.assertEqual(revision.base_snapshot[key],live[key],key)
                    self.assertNotIn(key,revision.payload)


class ConcurrentMixedProjectionTests(PublicationFixture,TransactionTestCase):
    def test_separate_connections_serialize_same_version_and_refuse_loser(self):
        import queue
        import threading
        from django.db import connections
        plan=self.place.pricing_plan_records.get();plan.price=Decimal('15.00');plan.save()
        self.place.refresh_from_db()
        initial=self.s.snapshot(self.place,'place');version=self.place.content_version
        barrier=threading.Barrier(2);results=queue.Queue()
        def write(actor,amount,name):
            try:
                incoming=copy.deepcopy(initial);incoming['pricing_plans'][0]['price']=amount
                incoming['name_ru']=name;barrier.wait(timeout=10)
                revision=self.s.propose(actor=actor,target_type='place',target_id=self.place.pk,patch=incoming,
                    schema_version=1,expected_version=version,revision_version=0,submit=False,explicit_save=True)
                results.put(('saved',amount,name,revision.pk))
            except ValidationError as error:results.put(('conflict',error.code))
            except Exception as error:results.put(('unexpected',type(error).__name__,str(error)))
            finally:connections.close_all()
        threads=[threading.Thread(target=write,args=(self.owner,'18.00','QA owner concurrent')),
                 threading.Thread(target=write,args=(self.staff,'21.00','QA authorized staff concurrent'))]
        for thread in threads:thread.start()
        for thread in threads:thread.join(timeout=20)
        self.assertFalse(any(thread.is_alive() for thread in threads),'Concurrent write did not finish')
        rows=[results.get_nowait() for _ in range(2)]
        self.assertEqual(sorted(row[0] for row in rows),['conflict','saved'],rows)
        winner=next(row for row in rows if row[0]=='saved')
        self.place.refresh_from_db();revision=VolunteerPlaceRevision.objects.get(place=self.place)
        self.assertEqual(str(self.place.price_from),winner[1]);self.assertEqual(revision.payload['name_ru'],winner[2])
        self.assertNotIn('price_from',revision.payload)
