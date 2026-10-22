"""WhatsApp-disabled edits must stop counting organization WhatsApp as a contact."""
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from catalog.models import Place
from catalog.services.place_readiness import readiness_data_from_form
from catalog.services.contact_policy import contact_client_config
from catalog.services.permanent_place_rules import client_rules


class FormContactInheritanceTests(SimpleTestCase):
    def form(self, mode):
        return SimpleNamespace(instance=Place(whatsapp_mode='legacy'), cleaned_data={'whatsapp_mode': mode}, cleaned_schedule_days=[], is_bound=True)

    def test_readiness_uses_posted_mode_without_mutating_stored_instance(self):
        for mode in ('none', 'same', 'separate', 'legacy'):
            with self.subTest(mode=mode):
                form = self.form(mode)
                with patch('catalog.services.place_readiness.inherited_contact', side_effect=lambda place: '+13104564918' if place.whatsapp_mode == 'legacy' else ''):
                    data = readiness_data_from_form(form)
                self.assertEqual(bool(data.other_contact), mode == 'legacy')
                self.assertEqual(form.instance.whatsapp_mode, 'legacy')

    def test_client_required_flag_uses_displayed_mode(self):
        for mode in ('none', 'same', 'legacy'):
            form = self.form(mode)
            with patch('catalog.services.place_readiness.inherited_contact', side_effect=lambda place: '+13104564918' if place.whatsapp_mode == 'legacy' else ''), patch('catalog.services.contact_policy.contact_client_config', return_value={}):
                rules = client_rules(form)
            self.assertEqual(rules['contact_required'], mode != 'legacy')


class ContactClientModeMapTests(SimpleTestCase):
    def config(self, *, phone='', whatsapp='+13104564918', website='', affiliation=True):
        place = Place(organization_id=42, whatsapp_mode='legacy')
        organization = SimpleNamespace(phone=phone, whatsapp=whatsapp, website=website)
        with patch('catalog.models.Subcategory.objects.filter') as taxonomy, patch('catalog.models.Organization.objects.filter') as organizations, patch('catalog.services.organization_ownership.affiliation_current', return_value=affiliation):
            taxonomy.return_value.values_list.return_value = []
            organizations.return_value.first.return_value = organization
            return contact_client_config(place)

    def test_organization_whatsapp_only_is_inherited_only_in_legacy_mode(self):
        config = self.config()
        self.assertTrue(config['inherited'])
        self.assertEqual(config['inherited_by_mode'], {'legacy': True, 'same': False, 'separate': False, 'none': False})

    def test_phone_or_site_stays_available_when_whatsapp_disabled(self):
        for contact in ({'phone': '+994504274393'}, {'website': 'https://example.invalid'}):
            config = self.config(**contact)
            self.assertTrue(all(config['inherited_by_mode'].values()))

    def test_unconfirmed_affiliation_never_counts_in_any_mode(self):
        config = self.config(affiliation=False)
        self.assertFalse(config['inherited'])
        self.assertFalse(any(config['inherited_by_mode'].values()))
