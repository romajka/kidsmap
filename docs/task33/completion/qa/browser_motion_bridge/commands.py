"""Synthetic seven-role loopback bridge; no production data or transport."""
import importlib.util
import json
import mimetypes
import threading
from pathlib import Path

spec = importlib.util.spec_from_file_location('qa04_commands', Path(__file__).resolve().parents[3]/'qa04/commands.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
BaselineRunner = base.BaselineRunner
dump = base.dump

def main(mode, labels):
    assert mode == 'probe'
    code = base.main(mode, labels)
    if code:
        return code
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group
    from django.contrib.staticfiles import finders
    from django.db import close_old_connections
    from django.test import Client
    from django.urls import reverse
    from django.utils import timezone
    from django.utils.translation import override
    from catalog.models import Organization, OrganizationGrant, Place, VolunteerPlaceRevision, Program, Activity, OfferingGroup, PricingPlan
    from catalog.services import organization_ownership, publication
    from catalog.services.review_versions import submit_review, moderate_candidate
    from catalog.testcases.utils import create_quality_place
    from http.cookies import SimpleCookie
    from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
    from urllib.parse import urlsplit, parse_qs

    settings.LOCALIZED_PLACE_URLS_ENABLED = True
    settings.PUBLIC_BASE_URL = 'https://kidsmap.az'
    settings.TASK33_R1_WRITE_MODE = 'all'
    roles = ('parent','standalone_owner','network_owner','selected_manager','all_network','volunteer','moderator')
    users = {role:get_user_model().objects.create_user('qa23_'+role,email=role+'@example.invalid') for role in roles}
    users['volunteer'].is_staff = True
    users['volunteer'].save(update_fields=['is_staff'])
    users['volunteer'].groups.add(Group.objects.get_or_create(name='KidsMap Volunteers')[0])
    users['moderator'].is_staff = users['moderator'].is_superuser = True
    users['moderator'].save(update_fields=['is_staff','is_superuser'])
    standalone = create_quality_place(owner=users['standalone_owner'],created_by=users['standalone_owner'],name_az='QA23 STANDALONE',name_ru='QA23 STANDALONE',name_en='QA23 STANDALONE',photo='',cover_photo='',lat=None,lng=None)
    organization = Organization.objects.create(owner=users['network_owner'],created_by=users['network_owner'],name_az='QA23 NETWORK',status='published',approved_at=timezone.now())
    branch = create_quality_place(owner=users['network_owner'],created_by=users['network_owner'],name_az='QA23 SELECTED BRANCH',name_ru='QA23 SELECTED BRANCH',name_en='QA23 SELECTED BRANCH',photo='',cover_photo='',lat=None,lng=None)
    organization_ownership.request_join(actor=users['network_owner'],place_id=branch.pk,organization_id=organization.pk)
    branch.refresh_from_db()
    for role,scope in [('selected_manager','selected_places'),('all_network','all_network')]:
        grant = OrganizationGrant.objects.create(organization=organization,owner=users['network_owner'],member=users[role],base_ownership_version=organization.ownership_version,scope=scope,actions=['organization.view','place.view','place.edit'])
        if scope=='selected_places':
            grant.selected_places.add(branch)
    future = create_quality_place(owner=users['network_owner'],created_by=users['network_owner'],name_az='QA23 FUTURE BRANCH',name_ru='QA23 FUTURE BRANCH',name_en='QA23 FUTURE BRANCH',photo='',cover_photo='',lat=None,lng=None)
    organization_ownership.request_join(actor=users['network_owner'],place_id=future.pk,organization_id=organization.pk)
    future.refresh_from_db()
    volunteer = create_quality_place(created_by=users['volunteer'],owner=None,name_az='QA23 VOLUNTEER',name_ru='QA23 VOLUNTEER',name_en='QA23 VOLUNTEER',status='draft',is_active=False,photo='',cover_photo='',lat=None,lng=None)
    publication.propose(actor=users['volunteer'],target_type='place',target_id=volunteer.pk,patch={'description_az':'QA23 VOLUNTEER PENDING'},schema_version=1,expected_version=volunteer.content_version,revision_version=0,submit=True,explicit_save=True)
    head,approved = submit_review(target=branch,user=users['parent'],rating=5,text='QA23 APPROVED REVIEW',author_name='Synthetic parent')
    moderate_candidate(head=head,revision_id=approved.pk,actor=users['moderator'],approve=True)
    head,pending = submit_review(target=branch,user=users['parent'],rating=4,text='QA23 PENDING REVIEW',author_name='Synthetic parent')
    clients = {role:Client(enforce_csrf_checks=True,raise_request_exception=False) for role in roles}
    for role,client in clients.items():
        client.force_login(users[role])
    paths = {}
    branch.description_ru = 'Учебный центр с занятиями по возрасту, регулярным расписанием и открытой связью с родителями. ' * 4
    branch.description_en = 'Learning centre with age appropriate groups, a regular schedule and clear communication with parents. ' * 4
    branch.save(update_fields=['description_ru','description_en'])

    # Direct synthetic approved display fixtures; not claimed as browser publication.
    for lang in ('az','ru','en'):
        setattr(organization,'name_'+lang,'QA AUDIT ORGANIZATION '+lang.upper())
        setattr(organization,'description_'+lang,'QA AUDIT APPROVED ORGANIZATION DESCRIPTION '+lang.upper())
    organization.phone='+994501234567';organization.save()
    program=Program.objects.create(organization=organization,created_by=users['network_owner'],
        name_az='QA AUDIT PROGRAM AZ',name_ru='QA AUDIT PROGRAM RU',name_en='QA AUDIT PROGRAM EN',
        description_az='QA AUDIT APPROVED DESCRIPTION AZ',description_ru='QA AUDIT APPROVED DESCRIPTION RU',description_en='QA AUDIT APPROVED DESCRIPTION EN',
        category=branch.category,status='published',approved_at=timezone.now())
    activity=Activity.objects.create(place=branch,program=program,status='published',supplement_az='QA AUDIT LOCAL AZ',supplement_ru='QA AUDIT LOCAL RU',supplement_en='QA AUDIT LOCAL EN')
    group=OfferingGroup.objects.create(activity=activity,name_az='QA AUDIT GROUP',name_ru='QA AUDIT GROUP',name_en='QA AUDIT GROUP',age_from=5,age_to=8,language='az',schedule_text='Saturday 10:00',conditions_az='QA AUDIT LOCAL CONDITIONS')
    from decimal import Decimal
    PricingPlan.objects.create(offering_group=group,product_type='lesson',price=Decimal('25'))
    private_activity=Activity.objects.create(place=branch,name_az='QA AUDIT PRIVATE ACTIVITY',status='draft')
    private_org=Organization.objects.create(owner=users['network_owner'],name_az='QA AUDIT PRIVATE ORGANIZATION',status='draft')

    for lang in ('az','ru','en'):
        with override(lang):
            paths[lang] = {
                'parent':reverse('typed_reviews',args=['place',branch.pk]),
                'standalone_owner':reverse('owner_place_edit',args=[standalone.pk]),
                'network_owner':reverse('organization_workspace_detail',args=[organization.pk]),
                'selected_manager':reverse('organization_workspace_detail',args=[organization.pk]),
                'all_network':reverse('organization_workspace_detail',args=[organization.pk]),
                'volunteer':('/' if lang=='az' else '/'+lang+'/')+'admin/volunteer/',
                'moderator':reverse('typed_reviews',args=['place',branch.pk]),
                'future':reverse('organization_workspace_branch',args=[organization.pk,future.pk]),
                'write':reverse('typed_reviews',args=['place',branch.pk]),
                'jsi18n':reverse('admin:jsi18n'),
                'drafts':reverse('server_draft_collection'),
                'catalog':reverse('place_list'),
                'detail':branch.get_absolute_url(),
                'map_api':reverse('public_map'),
                'fallback_detail':standalone.get_absolute_url(),
                'program':reverse('organization_program_detail',args=[organization.pk,program.pk]),
                'program_save':reverse('organization_program_save',args=[organization.pk,program.pk]),
                'activity':reverse('activity_detail',args=[activity.pk]),
                'organization':reverse('organization_detail',args=[organization.public_id]),
                'private_activity':reverse('activity_detail',args=[private_activity.pk]),
                'private_organization':reverse('organization_detail',args=[private_org.public_id]),
            }
    allowed = {p for row in paths.values() for p in row.values()}
    allowed.add(reverse('admin:jsi18n'))
    requests = []
    token = base.OUTPUT.name
    locks = {role:threading.RLock() for role in roles}
    def invariant():
        head.refresh_from_db()
        return {'places':Place.objects.count(),'revisions':VolunteerPlaceRevision.objects.count(),'review_versions':head.revisions.count(),'review_current':head.current_revision_id,'review_candidate':head.candidate_revision_id}
    initial = invariant()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):self.handle_surface('GET')
        def do_POST(self):self.handle_surface('POST')
        def json(self,value):
            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps(value).encode())
        def handle_surface(self,method):
            parsed=urlsplit(self.path);path=parsed.path
            cookies=SimpleCookie(self.headers.get('Cookie',''))
            role=cookies['qa23_actor'].value if 'qa23_actor' in cookies else 'parent'
            if role not in clients:self.send_error(403);return
            if path.startswith('/qa28/session/') and method=='GET':
                role=path.rsplit('/',1)[-1]
                lang=parse_qs(parsed.query).get('lang',['az'])[0]
                if role not in clients or lang not in ('az','ru','en'):self.send_error(400);return
                clients[role].cookies[settings.LANGUAGE_COOKIE_NAME]=lang
                self.send_response(200);self.send_header('Set-Cookie','qa23_actor='+role+'; Path=/; HttpOnly; SameSite=Lax');self.end_headers();return

            if path=='/qa28/targeted-state' and method=='GET':
                program.refresh_from_db();activity.refresh_from_db()
                rev=getattr(program,'content_revision',None)
                self.json({'program_name':program.name_az,'description':program.description_az,'status':program.status,
                    'revision_status':rev.status if rev else None,'revision_version':rev.version if rev else None,
                    'revision_payload':rev.payload if rev else {},'activity_snapshot':activity.program_snapshot,'supplement':activity.supplement_az})
                close_old_connections();return
            if path=='/qa28/fixtures' and method=='GET':self.json({'paths':paths,'token':token});return
            if path=='/qa28/cohort-off' and method=='POST':
                if parse_qs(parsed.query).get('token')!=[token]:self.send_error(403);return
                settings.TASK33_R1_WRITE_MODE='off';self.json({'write_mode':'off'});return
            if path=='/qa28/invariants' and method=='GET':
                current=invariant();self.json({'unchanged':current==initial});close_old_connections();return
            if path=='/qa28/finish' and method=='GET':
                if parse_qs(parsed.query).get('token')!=[token]:self.send_error(403);return
                base.dump('browser-bridge.json',{'status':'PASS','requests':requests,'synthetic_only':True,'unchanged':invariant()==initial})
                self.json({'finished':True});threading.Thread(target=self.server.shutdown,daemon=True).start();return
            if path in ('/qa-font.css','/qa-font.ttf') and method=='GET':
                resource=Path('/root/task33-browser-tools')/('material22.css' if path.endswith('.css') else 'material.ttf')
                self.send_response(200);self.send_header('Access-Control-Allow-Origin','*');self.send_header('Content-Type','text/css' if path.endswith('.css') else 'font/ttf');self.end_headers();self.wfile.write(resource.read_bytes());return
            if path.startswith('/static/') and method=='GET':
                name=path[len('/static/'):]
                if '..' in Path(name).parts or Path(name).suffix.lower() not in {'.css','.js','.svg','.png','.jpg','.jpeg','.webp','.woff','.woff2','.ttf','.ico'}:self.send_error(404);return
                found=finders.find(name)
                if not found:self.send_error(404);return
                self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(found)[0] or 'application/octet-stream');self.end_headers();self.wfile.write(Path(found).read_bytes());return
            if path.startswith('/media/responsive-images/') and method=='GET':
                media_root=Path(settings.MEDIA_ROOT).resolve()
                media=(media_root/path[len('/media/'):]).resolve()
                if not media.is_relative_to(media_root/'responsive-images') or not media.is_file() or media.suffix.lower() not in {'.png','.jpg','.jpeg','.webp'}:
                    self.send_error(404);return
                # The actual generated derivative must exist; no fabricated image response.
                self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(media)[0] or 'application/octet-stream')
                self.end_headers();self.wfile.write(media.read_bytes());return
            if path not in allowed:self.send_error(404);return
            if method=='POST':
                size=int(self.headers.get('Content-Length','0'))
                if size>20000:self.send_error(413);return
                data=self.rfile.read(size)
            with locks[role]:
                try:
                    client=clients[role]
                    response=client.generic(method,self.path,data=data,content_type=self.headers.get('Content-Type','application/x-www-form-urlencoded'),HTTP_HOST='127.0.0.1:8788',HTTP_ORIGIN='http://127.0.0.1:8788') if method=='POST' else client.get(self.path,HTTP_HOST='127.0.0.1:8788')
                    requests.append({'role':role,'path':path,'method':method,'status':response.status_code})
                    self.send_response(response.status_code)
                    for name in ('Content-Type','Location','Retry-After','Cache-Control'):
                        if response.has_header(name):self.send_header(name,response[name])
                    for morsel in response.cookies.values():self.send_header('Set-Cookie',morsel.OutputString())
                    self.end_headers();self.wfile.write(response.content)
                finally:close_old_connections()
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',8788),Handler)
    timer=threading.Timer(2400,server.shutdown);timer.daemon=True;timer.start()
    base.dump('browser-ready.json',{'port':8788,'loopback_only':True,'synthetic_only':True})
    try:server.serve_forever(poll_interval=.2)
    finally:timer.cancel();server.server_close()
    return 0 if (base.OUTPUT/'browser-bridge.json').exists() else 1
