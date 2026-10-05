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
    settings.PUBLIC_BASE_URL='https://kidsmap.az'
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group
    from django.contrib.staticfiles import finders
    from django.db import close_old_connections
    from django.test import Client
    from django.urls import reverse
    from django.utils import timezone
    from django.utils.translation import override
    from catalog.models import Organization, OrganizationGrant, Place, VolunteerPlaceRevision
    from catalog.services import organization_ownership, publication
    from catalog.services.review_versions import submit_review, moderate_candidate
    from catalog.testcases.utils import create_quality_place
    from http.cookies import SimpleCookie
    from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
    from urllib.parse import urlsplit, parse_qs

    settings.PRIVATE_MEDIA_ROOT = str(base.OUTPUT / 'private-documents')
    settings.TASK33_R1_WRITE_MODE = 'all'
    roles = ('public','person','manager','foreign','volunteer','staff','reviewer','applicant')
    users = {role:get_user_model().objects.create_user('qa25_'+role) for role in roles if role!='public'}
    for role in ('staff','reviewer','volunteer'):
        users[role].is_staff=True
        users[role].save(update_fields=['is_staff'])
    from catalog.services.staff_roles import VOLUNTEER_GROUP
    users['volunteer'].groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
    from django.contrib.auth.models import Permission
    for role in ('staff','reviewer'):
        users[role].user_permissions.add(*Permission.objects.filter(codename__in=['view_specialist','change_specialist']))
    users['reviewer'].user_permissions.add(*Permission.objects.filter(codename__in=['review_specialist_documents','review_specialist_claim']))
    organization=Organization.objects.create(owner=users['manager'],created_by=users['manager'],
        name_az='QA25 SYNTHETIC BUSINESS',status='published',approved_at=timezone.now())
    business_place=create_quality_place(owner=users['manager'],created_by=users['manager'])
    organization_ownership.request_join(actor=users['manager'],place_id=business_place.pk,organization_id=organization.pk)
    business_place.refresh_from_db()
    OrganizationGrant.objects.create(organization=organization,owner=users['manager'],member=users['foreign'],
        base_ownership_version=organization.ownership_version,scope='all_network',actions=['organization.view','place.view','place.edit'])
    from catalog.services.place_access import has_place_permission
    assert all(has_place_permission(user=users[role],place=business_place,permission_code='place.edit') for role in ('manager','foreign'))
    from django.core.files.uploadedfile import SimpleUploadedFile
    from catalog.models import Specialist,SpecialistDocument,SpecialistPracticeLocation,SpecialistSpecialization,SiteSettings
    site=SiteSettings.get_solo();site.specialists_section_enabled=True;site.save()
    person=Specialist.objects.create(name='QA25 SYNTHETIC PERSON',name_alt='QA25 SYNTHETIC PERSON',slug='qa25-synthetic',
        owner=users['manager'],verified_person_user=users['person'],person_verified_at=timezone.now(),status='published',is_active=True,consultation_format='online',
        bio_az='QA25 synthetic biography',bio_ru='QA25 synthetic biography',bio_en='QA25 synthetic biography',
        language_az=True,language_ru=True,language_en=True,phone='+994501234567')
    specialization=SpecialistSpecialization.objects.create(code='qa28-localized-specialization',name='QA28 Specialization',name_az='QA28 İxtisas',name_ru='QA28 Специализация',name_en='QA28 Specialization',is_active=True)
    person.specializations.add(specialization)
    from datetime import date, timedelta
    from catalog.services.specialist_domain import propose_employment, confirm_employment
    from catalog.models import SpecialistEmployment, SpecialistClaim
    employment={}
    for label,role,start,end in [('current','QA25 CURRENT ROLE',date.today()-timedelta(days=30),None),('history','QA25 HISTORICAL ROLE',date(2020,1,1),date(2021,1,1)),('pending','QA25 PENDING ROLE',date.today(),None)]:
        link=propose_employment(actor=users['manager'],specialist_id=person.pk,organization_id=organization.pk,role=role,start_date=start,end_date=end)
        link=confirm_employment(actor=users['manager'],employment_id=link.pk,side='organization',expected_version=link.version)
        if label!='pending':link=confirm_employment(actor=users['person'],employment_id=link.pk,side='person',expected_version=link.version)
        employment[label]=link
    unclaimed=Specialist.objects.create(name='QA25 UNCLAIMED PERSON',slug='qa25-unclaimed',created_by=users['manager'],status='published',is_active=True,consultation_format='online')
    foreign_person=Specialist.objects.create(name='QA25 FOREIGN PERSON',slug='qa25-foreign',verified_person_user=users['foreign'],person_verified_at=timezone.now(),status='published',is_active=True)
    foreign_document=SpecialistDocument.objects.create(specialist=foreign_person,document_type='identity',name='QA25 FOREIGN IDENTITY',file=SimpleUploadedFile('foreign.pdf',b'%PDF-synthetic-only'))
    SpecialistPracticeLocation.objects.create(specialist=person,address='QA25 RETIRED PRIVATE LOCATION',
        is_active=False,is_primary=False,price_per_session=999)
    documents={}
    for kind,status,name,publish in [('identity','approved','QA25 PRIVATE IDENTITY',False),('certificate','pending','QA25 PENDING CERTIFICATE',True),('certificate','approved','QA25 PUBLIC CERTIFICATE',True)]:
        document=SpecialistDocument.objects.create(specialist=person,document_type=kind,status=status,name=name,
          file=SimpleUploadedFile('proof.pdf',b'%PDF-synthetic-only'),is_published=publish,
          opted_in_by=users['person'] if publish else None,opted_in_at=timezone.now() if publish else None)
        documents['identity' if kind=='identity' else status]=document
    clients = {role:Client(enforce_csrf_checks=True,raise_request_exception=False) for role in roles}
    for role,client in clients.items():
        if role!='public':client.force_login(users[role])
    paths={}
    for lang in ('az','ru','en'):
        with override(lang):
            admin_path=('/' if lang=='az' else '/'+lang+'/')+'admin/catalog/specialist/'+str(person.pk)+'/change/'
            paths[lang]={role:(admin_path if role in ('staff','reviewer') else reverse('specialist_detail',args=[person.slug])) for role in roles}
            paths[lang]['person']=reverse('specialist_workspace_profile',args=[person.pk])
            paths[lang]['legacy_editor']=reverse('owner_specialist_edit',args=[person.pk])
            paths[lang]['index']=reverse('specialist_workspace_index')
            for screen in ('claims','invitations','certificates','review'):
                paths[lang][screen]=reverse('specialist_workspace_'+screen,args=[unclaimed.pk if screen=='claims' else person.pk])
            paths[lang]['org']=reverse('organization_specialists',args=[organization.pk])
            paths[lang]['claim_review']=reverse('specialist_workspace_review',args=[unclaimed.pk])
            paths[lang]['foreign_certificates']=reverse('specialist_workspace_certificates',args=[foreign_person.pk])
            paths[lang]['foreign_document']=reverse('serve_specialist_document',args=[foreign_document.pk])
            paths[lang]['jsi18n']=('/' if lang=='az' else '/'+lang+'/')+'admin/jsi18n/'
            for kind,document in documents.items():
                paths[lang]['document_'+kind]=reverse('serve_specialist_document',args=[document.pk])
    allowed={path for row in paths.values() for path in row.values()}
    allowed.add(reverse('admin:jsi18n'))
    requests=[];token=base.OUTPUT.name
    locks={role:threading.RLock() for role in roles}
    def invariant():
        return {'documents':SpecialistDocument.objects.count(),'public':SpecialistDocument.objects.filter(is_published=True).count()}
    initial=invariant()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):self.handle_surface('GET')
        def do_POST(self):self.handle_surface('POST')
        def json(self,value):
            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps(value).encode())
        def handle_surface(self,method):
            parsed=urlsplit(self.path);path=parsed.path
            cookies=SimpleCookie(self.headers.get('Cookie',''))
            role=cookies['qa25_actor'].value if 'qa25_actor' in cookies else 'public'
            if role not in clients:self.send_error(403);return
            if path.startswith('/qa28/session/') and method=='GET':
                role=path.rsplit('/',1)[-1]
                lang=parse_qs(parsed.query).get('lang',['az'])[0]
                if role not in clients or lang not in ('az','ru','en'):self.send_error(400);return
                clients[role].cookies[settings.LANGUAGE_COOKIE_NAME]=lang
                self.send_response(200);self.send_header('Set-Cookie','qa25_actor='+role+'; Path=/; HttpOnly; SameSite=Lax');self.end_headers();return
            if path=='/qa28/fixtures' and method=='GET':self.json({'paths':paths,'token':token,'ids':{'person':person.pk,'unclaimed':unclaimed.pk,'foreign':foreign_person.pk,'identity':documents['identity'].pk,'pending':documents['pending'].pk,'approved':documents['approved'].pk,'foreign_document':foreign_document.pk,'employment_pending':employment['pending'].pk}});return
            if path=='/qa28/state' and method=='GET':
                def document_state(d):
                    from catalog.controllers.specialist_workspace import document_version
                    d.refresh_from_db();return {'status':d.status,'published':d.is_published,'version':document_version(d)}
                link=SpecialistEmployment.objects.get(pk=employment['pending'].pk)
                self.json({'employment_status':link.status,'employment_version':link.version,'browser_proposal_pending':SpecialistEmployment.objects.filter(specialist=person,role='QA25 BROWSER PROPOSAL',status='pending').count(),'claims_pending':SpecialistClaim.objects.filter(specialist=unclaimed,status='pending').count(),'claims_approved':SpecialistClaim.objects.filter(specialist=unclaimed,status='approved').count(),'unclaimed_person_verified':Specialist.objects.filter(pk=unclaimed.pk,verified_person_user=users['applicant']).exists(),'documents':{kind:document_state(d) for kind,d in documents.items()},'document_count':SpecialistDocument.objects.filter(specialist=person).count()});close_old_connections();return
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
            if path not in allowed:self.send_error(404);return
            if method=='POST':
                size=int(self.headers.get('Content-Length','0'))
                if size>200000:self.send_error(413);return
                data=self.rfile.read(size)
            with locks[role]:
                try:
                    client=clients[role]
                    response=client.generic(method,self.path,data=data,content_type=self.headers.get('Content-Type','application/x-www-form-urlencoded'),HTTP_HOST='127.0.0.1:8788',HTTP_ORIGIN='http://127.0.0.1:8788') if method=='POST' else client.get(self.path,HTTP_HOST='127.0.0.1:8788')
                    requests.append({'role':role,'path':path,'method':method,'status':response.status_code})
                    self.send_response(response.status_code)
                    for name in ('Content-Type','Location','Retry-After','Cache-Control','Content-Disposition','X-Content-Type-Options'):
                        if response.has_header(name):self.send_header(name,response[name])
                    for morsel in response.cookies.values():self.send_header('Set-Cookie',morsel.OutputString())
                    self.end_headers()
                    if response.streaming:
                        self.wfile.write(b''.join(response.streaming_content))
                        for closer in response._resource_closers:closer()
                    else:self.wfile.write(response.content)
                finally:close_old_connections()
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',8788),Handler)
    timer=threading.Timer(2400,server.shutdown);timer.daemon=True;timer.start()
    base.dump('browser-ready.json',{'port':8788,'loopback_only':True,'synthetic_only':True})
    try:server.serve_forever(poll_interval=.2)
    finally:timer.cancel();server.server_close()
    return 0 if (base.OUTPUT/'browser-bridge.json').exists() else 1
