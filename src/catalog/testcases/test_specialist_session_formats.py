from itertools import combinations
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.http import QueryDict
from django.test import TestCase

from catalog.testcases.specialist_document_fixtures import portrait_upload
from catalog.models import District, Region, SpecialistSpecialization
from catalog.services.specialist_proposal_drafts import proposal_forms, return_for_revision, save_proposal


class SpecialistSessionFormsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.author = users.create_user('format-author')
        cls.editor = users.create_user('format-editor', is_superuser=True, is_staff=True)
        cls.city = Region.objects.create(key='formatcity', name_ru='A', name_en='A', name_az='A')
        other = Region.objects.create(key='formatother', name_ru='B', name_en='B', name_az='B')
        cls.district = District.objects.create(key='format-a', region=cls.city, name_ru='AA', name_az='AA', name_en='AA')
        cls.other_district = District.objects.create(key='format-b', region=other, name_ru='BB', name_az='BB', name_en='BB')
        cls.direction = SpecialistSpecialization.objects.create(code='format-audit',name_ru='QA',name_az='QA',name_en='QA')

    def data(self, codes):
        data = QueryDict('', mutable=True)
        data.update({'name':'Test Formats', 'bio_ru':'QA', 'language_ru':'on', 'phone':'+994501234567',
                     'lesson_type': 'pair', 'lesson_price': '25',
                     'specializations':str(self.direction.pk), 'locations-INITIAL_FORMS':'0',
                     'locations-TOTAL_FORMS':'0', 'locations-MAX_NUM_FORMS':'30'})
        data.setlist('session_formats', list(codes))
        if 'office' in codes:
            data.update({'locations-TOTAL_FORMS':'1','locations-0-region':self.city.pk,
                         'locations-0-address':'Test office','locations-0-is_active':'on'})
        if 'visit' in codes:
            data['visit_region'] = self.city.pk
            data.setlist('visit_districts', [self.district.pk])
        return data

    def save(self, data, *, submit, key=None, version=0):
        return save_proposal(actor=self.author, draft_id=key or uuid4(), expected_version=version,
                             data=data, files={'photo': portrait_upload()} if submit else {}, submit=submit)

    def test_all_seven_combinations_survive_draft_submission_and_return(self):
        for size in (1, 2, 3):
            for codes in combinations(('online','office','visit'), size):
                with self.subTest(codes=codes):
                    data = self.data(codes)
                    draft = self.save(data, submit=False)
                    form, _ = proposal_forms(actor=self.author, payload=draft.payload)
                    self.assertIn('session_formats', form.fields)
                    self.assertEqual(tuple(form['session_formats'].value()), codes)
                    draft = self.save(data, submit=True, key=draft.pk, version=1)
                    person = draft.submitted_specialist
                    self.assertEqual((person.offers_online, person.offers_office, person.offers_visits),
                                     tuple(code in codes for code in ('online','office','visit')))
                    self.assertEqual(person.visit_districts.count(), int('visit' in codes))
                    return_for_revision(actor=self.editor,specialist_id=person.pk,comment='QA')
                    draft.refresh_from_db()
                    form, _ = proposal_forms(actor=self.author, payload=draft.payload, draft=draft)
                    self.assertEqual(tuple(form['session_formats'].value()), codes)
                    if 'visit' in codes:
                        self.assertEqual(form['visit_districts'].value(), [self.district.pk])

    def test_invalid_area_and_incomplete_drafts(self):
        cases = [
            ((), {}, 'session_formats'),
            (('visit',), {'visit_region':''}, 'visit_region'),
            (('visit',), {'visit_districts':[]}, 'visit_districts'),
            (('visit',), {'visit_districts':[self.other_district.pk]}, 'visit_districts'),
        ]
        for codes, changes, field in cases:
            with self.subTest(codes=codes, field=field, changes=changes):
                data = self.data(codes)
                for key,value in changes.items():
                    if isinstance(value,list):
                        data.setlist(key,value)
                    else:
                        data[key] = value
                if self.other_district.pk not in data.getlist('visit_districts'):
                    draft = self.save(data, submit=False)
                    self.assertIsNone(draft.submitted_specialist_id)
                with self.assertRaises(ValidationError) as error:
                    self.save(data, submit=True)
                self.assertIn(field, error.exception.form.errors)

    def test_citywide_visits_need_no_office_or_district(self):
        data = self.data(('visit',))
        data.setlist('visit_districts', [])
        data['visit_citywide'] = 'on'
        form, _ = proposal_forms(actor=self.author, data=data, files={'photo': portrait_upload()}, submit=True)
        self.assertTrue(form.is_valid(), form.errors)
        profile = self.save(data, submit=True).submitted_specialist
        self.assertTrue(profile.visit_citywide)
        self.assertEqual(profile.practice_locations.count(), 0)

    def test_deselection_clears_visit_area_and_retires_office_on_resubmission(self):
        data = self.data(('office', 'visit'))
        draft = self.save(data, submit=True)
        person = draft.submitted_specialist
        office = person.practice_locations.get()
        return_for_revision(actor=self.editor, specialist_id=person.pk, comment='QA')
        draft.refresh_from_db()
        from catalog.services.specialist_proposal_drafts import proposal_data

        data = proposal_data(draft.payload)
        data.setlist('session_formats', ['online'])
        # Browser may include stale hidden data; the explicit selection wins.
        reloaded = self.save(data, key=draft.pk, version=draft.version, submit=True)
        self.assertEqual(reloaded.submitted_specialist_id, person.pk)
        person.refresh_from_db()
        office.refresh_from_db()
        self.assertEqual((person.offers_online, person.offers_office, person.offers_visits), (True, False, False))
        self.assertIsNone(person.visit_region_id)
        self.assertFalse(person.visit_citywide)
        self.assertFalse(person.visit_districts.exists())
        self.assertFalse(office.is_active)
        self.assertEqual(office.address, 'Test office')

    def test_legacy_draft_without_valid_office_does_not_promote_office(self):
        data = self.data(('office',))
        del data['session_formats']
        data['consultation_format'] = 'both'
        data['locations-0-address'] = '   '
        payload = {key: data.getlist(key) for key in data}
        form, _ = proposal_forms(actor=self.author, payload=payload)
        self.assertEqual(form['session_formats'].value(), ['online'])
        payload['locations-0-address'] = ['Test office']
        form, _ = proposal_forms(actor=self.author, payload=payload)
        self.assertEqual(form['session_formats'].value(), ['online', 'office'])
