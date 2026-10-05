"""Synthetic Event bridge on dedicated loopback; actual Django and isolated QA04."""
import importlib.util,json,mimetypes,threading
from pathlib import Path
spec=importlib.util.spec_from_file_location('qa04_commands',Path(__file__).resolve().parents[2]/'qa04/commands.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
BaselineRunner=base.BaselineRunner
dump=base.dump

def main(mode,labels):
    assert mode=='probe'
    code=base.main(mode,labels)
    if code:return code
    from datetime import timedelta
    from zoneinfo import ZoneInfo
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.contrib.staticfiles import finders
    from django.db import close_old_connections
    from django.test import Client
    from django.urls import reverse
    from django.utils import timezone
    from django.utils.translation import override
    from catalog.models import Organization,Specialist,Event,Category,SiteSettings
    from catalog.services import event_domain
    from catalog.services.review_versions import submit_review,moderate_candidate
    from catalog.testcases.utils import create_quality_place
    from http.cookies import SimpleCookie
    from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
    from urllib.parse import urlsplit,parse_qs
    settings.TASK33_R1_WRITE_MODE='all'
    roles=('public','owner','person','venue','reviewer','author')
    users={role:get_user_model().objects.create_user('qa26_'+role) for role in roles if role!='public'}
    users['reviewer'].is_staff=True;users['reviewer'].is_superuser=True;users['reviewer'].save()
    site=SiteSettings.get_solo();site.events_section_enabled=True;site.save()
    now=timezone.now();baku=ZoneInfo('Asia/Baku')
    day=(now+timedelta(days=10)).astimezone(baku).replace(hour=23,minute=30,second=0,microsecond=0)
    org=Organization.objects.create(owner=users['owner'],created_by=users['owner'],name_az='QA26 ORGANIZER AZ',name_ru='QA26 ORGANIZER RU',name_en='QA26 ORGANIZER EN',status='published',approved_at=now)
    person=Specialist.objects.create(name='QA26 INDEPENDENT PERSON',verified_person_user=users['person'],person_verified_at=now,status='published',is_active=True,slug='qa26-independent')
    venue=create_quality_place(owner=users['venue'],created_by=users['venue'],name_az='QA26 HISTORIC VENUE',name_ru='QA26 HISTORIC VENUE',name_en='QA26 HISTORIC VENUE',address='QA26 HISTORIC ADDRESS',lat='40.400000',lng='49.800000',district='baku_yasamal')
    category=Category.objects.create(code='qa26-event',name_az='QA26 CATEGORY',name_ru='QA26 CATEGORY',name_en='QA26 CATEGORY')
    events={}
    def create(label,start=None,end=None,online=False,publish=True,specialist=False):
        values={'name_az':'QA26 '+label.upper(),'name_ru':'QA26 '+label.upper(),'name_en':'QA26 '+label.upper(),'description_az':'QA26 synthetic event description','description_ru':'QA26 synthetic event description','description_en':'QA26 synthetic event description','category_id':category.code,'start_datetime':start or day,'end_datetime':end or day+timedelta(hours=2),'event_format':'online' if online else 'physical','organizer_specialist_id':person.pk if specialist else None,'organizer_organization_id':None if specialist else org.pk,'related_place_id':None if online else venue.pk,'address':'' if online else venue.address,'age_from':6,'age_to':12,'price_text':'15 AZN','phone':'+994501234567'}
        actor=users['person' if specialist else 'owner'];event=event_domain.create_event(actor=actor,values=values)
        if publish:event=event_domain.publish_event(actor=users['reviewer'],event_id=event.pk,expected_updated_at=event.updated_at.isoformat())
        events[label]=event;return event
    create('physical');create('online',online=True,specialist=True)
    create('past',start=now-timedelta(days=2),end=now-timedelta(days=1))
    cancelled=create('cancelled');events['cancelled']=event_domain.cancel_event(actor=users['owner'],event_id=cancelled.pk,expected_updated_at=cancelled.updated_at.isoformat(),reason='QA26 cancelled fixture')
    moved=create('rescheduled');events['rescheduled']=event_domain.reschedule_event(actor=users['owner'],event_id=moved.pk,start_datetime=day+timedelta(days=2),end_datetime=day+timedelta(days=2,hours=2),expected_updated_at=moved.updated_at.isoformat(),reason='QA26 moved fixture')
    create('draft',publish=False,online=True)
    for label,status in [('pending','pending'),('rejected','rejected'),('deleted','published')]:
        e=create(label,publish=status=='published');Event.objects.filter(pk=e.pk).update(status=status,deleted_at=now if label=='deleted' else None)
    # Change today's Place without modifying the approved occurrence snapshots.
    from catalog.services.location_assignment import set_location_override
    venue.address='QA26 TODAY ADDRESS';venue.lat=40.9;venue.lng=49.9
    set_location_override(venue,actor=users['reviewer'],city='baku',district='baku_narimanov',reason='QA26 synthetic authorized movement')
    venue.save()
    head,revision=submit_review(target=events['physical'],user=users['author'],rating=5,text='QA26 APPROVED REVIEW')
    moderate_candidate(head=head,revision_id=revision.pk,actor=users['reviewer'],approve=True)
    submit_review(target=events['physical'],user=users['author'],rating=1,text='QA26 PENDING EDIT')
    submit_review(target=events['online'],user=users['author'],rating=1,text='QA26 FOREIGN PENDING')
    clients={role:Client(enforce_csrf_checks=True,raise_request_exception=False) for role in roles}
    for role,client in clients.items():
        if role!='public':client.force_login(users[role])
    paths={}
    for lang in ('az','ru','en'):
        with override(lang):
            paths[lang]={label:e.get_absolute_url() for label,e in events.items()}
            paths[lang].update(create=reverse('owner_event_create'),edit=reverse('owner_event_edit',args=[events['draft'].pk]),dashboard=reverse('owner_places_dashboard'),landing=reverse('events_landing'),admin=reverse('admin:catalog_event_change',args=[events['draft'].pk]),admin_physical=reverse('admin:catalog_event_change',args=[events['physical'].pk]),admin_add=reverse('admin:catalog_event_add'),admin_list=reverse('admin:catalog_event_changelist'),jsi18n=reverse('admin:jsi18n'),select_type=reverse('owner_place_create'))
    allowed={p for row in paths.values() for p in row.values()};requests=[];token=base.OUTPUT.name
    locks={role:threading.RLock() for role in roles}
    def state():
        result={}
        for label,e in events.items():
            e.refresh_from_db();result[label]={'status':e.status,'version':e.updated_at.isoformat(),'format':e.event_format,'organizer_resolution':e.organizer_resolution,'has_place':bool(e.related_place_id),'has_coords':e.lat is not None or e.lng is not None,'address':e.address,'snapshot':e.venue_snapshot,'name':e.name_az,'admin_name':e.name,'has_photo':bool(e.photo),'start':e.start_datetime.isoformat() if e.start_datetime else None,'end':e.end_datetime.isoformat() if e.end_datetime else None}
        result['created']=[{'name':e.name_az,'status':e.status,'format':e.event_format,'resolved':e.organizer_resolution,'has_place':bool(e.related_place_id),'has_coords':e.lat is not None or e.lng is not None,'address':e.address,'start':e.start_datetime.isoformat() if e.start_datetime else None,'end':e.end_datetime.isoformat() if e.end_datetime else None} for e in Event.objects.filter(name_az__startswith='QA26 BROWSER')]
        return result
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):self.surface('GET')
        def do_POST(self):self.surface('POST')
        def json(self,value):
            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps(value).encode())
        def surface(self,method):
            parsed=urlsplit(self.path);path=parsed.path;cookies=SimpleCookie(self.headers.get('Cookie',''));role=cookies['qa26_actor'].value if 'qa26_actor' in cookies else 'public'
            if role not in clients:self.send_error(403);return
            if path.startswith('/qa26/session/') and method=='GET':
                role=path.rsplit('/',1)[-1];lang=parse_qs(parsed.query).get('lang',['az'])[0]
                if role not in clients or lang not in ('az','ru','en'):self.send_error(400);return
                clients[role].cookies[settings.LANGUAGE_COOKIE_NAME]=lang
                self.send_response(200);self.send_header('Set-Cookie','qa26_actor='+role+'; Path=/; HttpOnly; SameSite=Lax');self.end_headers();return
            if path=='/qa26/fixtures' and method=='GET':self.json({'runtime':{'base':str(settings.BASE_DIR),'static':str(finders.find('admin/css/pages/kidsmap_admin_form_shell.css')),'event':__import__('inspect').getfile(Event),'domain':event_domain.__file__},'paths':paths,'ids':{'org':org.pk,'person':person.pk,'venue':venue.pk,'category':category.code},'date':day.date().isoformat(),'end_date':(day+timedelta(hours=2)).date().isoformat(),'start':day.isoformat(),'end':(day+timedelta(hours=2)).isoformat(),'previous_start':day.isoformat(),'token':token});return
            if path=='/qa26/state' and method=='GET':self.json(state());close_old_connections();return
            if path=='/qa26/finish' and method=='GET':
                if parse_qs(parsed.query).get('token')!=[token]:self.send_error(403);return
                base.dump('browser-bridge.json',{'status':'PASS','requests':requests,'synthetic_only':True});self.json({'finished':True});threading.Thread(target=self.server.shutdown,daemon=True).start();return
            if path in ('/qa-font.css','/qa-font.ttf') and method=='GET':
                resource=Path('/root/task33-browser-tools')/('material22.css' if path.endswith('.css') else 'material.ttf');self.send_response(200);self.send_header('Access-Control-Allow-Origin','*');self.send_header('Content-Type','text/css' if path.endswith('.css') else 'font/ttf');self.end_headers();self.wfile.write(resource.read_bytes());return
            if path.startswith('/static/') and method=='GET':
                name=path[len('/static/'):]
                if '..' in Path(name).parts or Path(name).suffix.lower() not in {'.css','.js','.svg','.png','.jpg','.jpeg','.webp','.woff','.woff2','.ttf','.ico'}:self.send_error(404);return
                found=finders.find(name)
                if not found:self.send_error(404);return
                self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(found)[0] or 'application/octet-stream');self.end_headers();self.wfile.write(Path(found).read_bytes());return
            if path.startswith('/media/') and method=='GET':
                media_root=Path(settings.MEDIA_ROOT).resolve();media=(media_root/path[len('/media/'):]).resolve()
                if not media.is_relative_to(media_root) or not media.is_file() or media.suffix.lower() not in {'.png','.jpg','.jpeg','.webp'}:self.send_error(404);return
                self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(media)[0] or 'application/octet-stream');self.end_headers();self.wfile.write(media.read_bytes());return
            if path not in allowed:self.send_error(404);return
            data=b''
            if method=='POST':
                size=int(self.headers.get('Content-Length','0'))
                if size>200000:self.send_error(413);return
                data=self.rfile.read(size)
            with locks[role]:
                try:
                    client=clients[role];response=client.generic(method,self.path,data=data,content_type=self.headers.get('Content-Type','application/x-www-form-urlencoded'),HTTP_HOST='127.0.0.1:8786',HTTP_ORIGIN='http://127.0.0.1:8786') if method=='POST' else client.get(self.path,HTTP_HOST='127.0.0.1:8786')
                    requests.append({'role':role,'path':path,'method':method,'status':response.status_code});self.send_response(response.status_code)
                    for name in ('Content-Type','Location','Cache-Control','X-Content-Type-Options'):
                        if response.has_header(name):self.send_header(name,response[name])
                    for morsel in response.cookies.values():self.send_header('Set-Cookie',morsel.OutputString())
                    self.end_headers();self.wfile.write(response.content)
                finally:close_old_connections()
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',8786),Handler);timer=threading.Timer(2400,server.shutdown);timer.daemon=True;timer.start()
    base.dump('browser-ready.json',{'port':8786,'loopback_only':True,'synthetic_only':True})
    try:server.serve_forever(poll_interval=.2)
    finally:timer.cancel();server.server_close()
    return 0 if (base.OUTPUT/'browser-bridge.json').exists() else 1
