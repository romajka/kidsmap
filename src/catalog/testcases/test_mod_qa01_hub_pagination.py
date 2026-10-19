"""Regression for moderation-hub pagination and preserved filters."""
from html.parser import HTMLParser
from urllib.parse import parse_qs,urlsplit
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group,Permission
from django.test import TestCase
from django.utils import timezone,translation
from catalog.models import Organization,VolunteerPlaceRevision
from catalog.services import volunteer_proposals

class Links(HTMLParser):
    def __init__(self):super().__init__();self.hrefs=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':
            href=dict(attrs).get('href','')
            if 'page=' in href:self.hrefs.append(href)

class ModerationHubPaginationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User=get_user_model();cls.reviewer=User.objects.create_user('page_reviewer',is_staff=True)
        cls.reviewer.user_permissions.add(Permission.objects.get(content_type__app_label='catalog',codename='change_place'))
        cls.bare=User.objects.create_user('page_bare',is_staff=True);cls.vol=User.objects.create_user('page_vol',is_staff=True)
        group,_=Group.objects.get_or_create(name='KidsMap Volunteers');cls.vol.groups.add(group)
        for i in range(32):
            org=Organization.objects.create(created_by=cls.vol,owner=None,name_az=f'QA Queue {i:02d}')
            volunteer_proposals.propose(actor=cls.vol,kind='organization',target_id=org.pk,patch={'description_az':'Synthetic candidate'},expected_version=org.content_version,revision_version=0,submit=True)
        cls.date=timezone.now().date().isoformat()

    def hub(self,lang):return('/'if lang=='az'else'/'+lang+'/')+'admin/volunteer/moderation/'
    def links(self,response):
        parser=Links();parser.feed(response.content.decode());return parser.hrefs
    def filters(self):return{'entity':'organization','status':'pending','new_or_edit':'new','author':[str(self.vol.pk),str(self.vol.pk)],'from':self.date,'to':self.date}

    def test_first_page_offers_next_with_all_filters_and_no_duplicate_page(self):
        self.client.force_login(self.reviewer)
        for lang in('ru','az','en'):
            with self.subTest(lang=lang),translation.override(lang):
                filters=self.filters();response=self.client.get(self.hub(lang),{**filters,'page':['999','1']})
                self.assertEqual(response.status_code,200);self.assertEqual(len(response.context['page']),25)
                self.assertEqual(response.context['counts']['pending'],32)
                next_links=[h for h in self.links(response)if parse_qs(urlsplit(h).query).get('page')==['2']]
                self.assertEqual(len(next_links),1)
                parsed=parse_qs(urlsplit(next_links[0]).query)
                for key,value in filters.items():self.assertEqual(parsed[key],value if isinstance(value,list)else[value])
                self.assertFalse(any(parse_qs(urlsplit(h).query).get('page')==['0']for h in self.links(response)))

    def test_last_page_offers_previous_and_has_distinct_candidate_rows(self):
        self.client.force_login(self.reviewer)
        for lang in('ru','az','en'):
            with self.subTest(lang=lang),translation.override(lang):
                first=self.client.get(self.hub(lang),self.filters());last=self.client.get(self.hub(lang),{**self.filters(),'page':'2'})
                self.assertEqual(last.status_code,200);self.assertEqual(len(last.context['page']),7)
                self.assertTrue({r['id']for r in first.context['page']}.isdisjoint({r['id']for r in last.context['page']}))
                previous=[h for h in self.links(last)if parse_qs(urlsplit(h).query).get('page')==['1']]
                self.assertEqual(len(previous),1)
                self.assertFalse(any(parse_qs(urlsplit(h).query).get('page')==['3']for h in self.links(last)))

    def test_empty_invalid_and_out_of_range_keep_existing_contract(self):
        self.client.force_login(self.reviewer)
        response=self.client.get(self.hub('ru'),{'entity':'program','status':'pending'})
        self.assertEqual(response.status_code,200);self.assertEqual(len(response.context['page']),0);self.assertEqual(self.links(response),[])
        invalid=self.client.get(self.hub('ru'),{'status':'invalid'})
        self.assertEqual(invalid.status_code,400);self.assertContains(invalid,'hub-filter-error',status_code=400)
        far=self.client.get(self.hub('ru'),{**self.filters(),'page':'999'})
        self.assertEqual(far.status_code,200);self.assertEqual(far.context['page'].number,2);self.assertEqual(len(far.context['page']),7)

    def test_denied_roles_and_get_navigation_do_not_change_candidates(self):
        before=list(VolunteerPlaceRevision.objects.order_by('pk').values('pk','status','version','payload'))
        for actor in(self.bare,self.vol):
            self.client.force_login(actor);self.assertEqual(self.client.get(self.hub('ru')).status_code,403)
        self.client.logout();self.assertEqual(self.client.get(self.hub('ru')).status_code,302)
        self.client.force_login(self.reviewer)
        self.assertEqual(self.client.post(self.hub('ru')).status_code,405)
        self.assertEqual(before,list(VolunteerPlaceRevision.objects.order_by('pk').values('pk','status','version','payload')))
