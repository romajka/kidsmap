from django.test import SimpleTestCase
from catalog.services.place_identity import identity_fields, check_duplicates


class PlaceIdentityContactTests(SimpleTestCase):
    def test_public_link_identity_whitelists_business_fields_and_rejects_credentials(self):
        data=identity_fields({'public_links':[
            {'label':'Official site','url':'https://academy.example.invalid','internal_note':'NeverExportMarker'},
            {'label':'Unsafe','url':'https://user:password@example.invalid/private'}]})
        self.assertEqual(data['public_links'],[{'label':'Official site','url':'https://academy.example.invalid'}])

    def test_website_lookup_finds_a_public_contact_link_and_reports_exact_field(self):
        fields=identity_fields({'name_az':'Little Academy','address':'Avenue 10',
            'public_links':[{'label':'Website','url':'https://academy.example.invalid/'}]})
        snapshot={'records':[{'key':'place:1','id':1,'draft_id':None,'status':'draft','is_public':False,
            'versions':[{'source':'candidate','version':3,'stale':False,'fields':fields}]}],
            'generated_at':'2026-10-29','coverage':{'complete_within_access':True}}
        result=check_duplicates(None,{'website':'https://academy.example.invalid'},registry=snapshot)
        self.assertEqual(result['results'][0]['evidence'][0]['matched_fields'],['public_links'])

    def test_legacy_urls_with_credentials_are_not_exported(self):
        fields=identity_fields({'website':'https://user:secret@example.invalid/',
            'instagram':'https://user:secret@instagram.com/academy'})
        self.assertEqual((fields['website'],fields['instagram']),('',''))
