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
    from datetime import datetime,timedelta
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
    from catalog.services import event_domain,event_queries,event_calendar
    from catalog.services.review_versions import submit_review,moderate_candidate
    from catalog.testcases.utils import create_quality_place
    from http.cookies import SimpleCookie
    from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
    from urllib.parse import urlsplit,parse_qs
    settings.TASK33_R1_WRITE_MODE='all'
    roles=('public','owner','person','venue','reviewer','author')
    users={role:get_user_model().objects.create_user('qa27_'+role) for role in roles if role!='public'}
    users['reviewer'].is_staff=True;users['reviewer'].is_superuser=True;users['reviewer'].save()
    site=SiteSettings.get_solo();site.events_section_enabled=True;site.save()
    now=timezone.now();baku=ZoneInfo('Asia/Baku')
    local_now=now.astimezone(baku)
    month_start=local_now.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
    next_month=(month_start+timedelta(days=32)).replace(day=1)
    previous_month=(month_start-timedelta(days=1)).replace(day=1)
    day=next_month.replace(day=15,hour=23,minute=30)
    org=Organization.objects.create(owner=users['owner'],created_by=users['owner'],name_az='QA27 ORGANIZER AZ',name_ru='QA27 ORGANIZER RU',name_en='QA27 ORGANIZER EN',status='published',approved_at=now)
    person=Specialist.objects.create(name='QA27 INDEPENDENT PERSON',verified_person_user=users['person'],person_verified_at=now,status='published',is_active=True,slug='qa27-independent')
    venue=create_quality_place(owner=users['venue'],created_by=users['venue'],name_az='QA27 HISTORIC VENUE',name_ru='QA27 HISTORIC VENUE',name_en='QA27 HISTORIC VENUE',address='QA27 HISTORIC ADDRESS',lat='40.400000',lng='49.800000',district='baku_yasamal')
    category=Category.objects.create(code='qa27-event',name_az='QA27 CATEGORY',name_ru='QA27 CATEGORY',name_en='QA27 CATEGORY')
    events={}
    def create(label,start=None,end=None,online=False,publish=True,specialist=False,title=None,az_only=False):
        values={'name_az':'QA27 '+label.upper(),'name_ru':'QA27 '+label.upper(),'name_en':'QA27 '+label.upper(),'description_az':'QA27 synthetic event description','description_ru':'QA27 synthetic event description','description_en':'QA27 synthetic event description','category_id':category.code,'start_datetime':start or day,'end_datetime':end or day+timedelta(hours=2),'event_format':'online' if online else 'physical','organizer_specialist_id':person.pk if specialist else None,'organizer_organization_id':None if specialist else org.pk,'related_place_id':None if online else venue.pk,'address':'' if online else venue.address,'age_from':6,'age_to':12,'price_text':'15 AZN','phone':'+994501234567'}
        if title:
            for lang in ('az','ru','en'):values['name_'+lang]=title+' '+lang.upper()
        if az_only:values['name_ru']=values['name_en']=''
        actor=users['person' if specialist else 'owner'];event=event_domain.create_event(actor=actor,values=values)
        if publish:event=event_domain.publish_event(actor=users['reviewer'],event_id=event.pk,expected_updated_at=event.updated_at.isoformat())
        events[label]=event;return event
    create('physical');create('online',online=True,specialist=True)
    create('past',start=now-timedelta(days=2),end=now-timedelta(days=1))
    cancelled=create('cancelled');events['cancelled']=event_domain.cancel_event(actor=users['owner'],event_id=cancelled.pk,expected_updated_at=cancelled.updated_at.isoformat(),reason='QA27 cancelled fixture')
    moved=create('rescheduled');events['rescheduled']=event_domain.reschedule_event(actor=users['owner'],event_id=moved.pk,start_datetime=day+timedelta(days=2),end_datetime=day+timedelta(days=2,hours=2),expected_updated_at=moved.updated_at.isoformat(),reason='QA27 moved fixture')
    create('draft',publish=False,online=True)
    for label,status in [('pending','pending'),('rejected','rejected'),('deleted','published')]:
        e=create(label,publish=status=='published');Event.objects.filter(pk=e.pk).update(status=status,deleted_at=now if label=='deleted' else None)
    calendar_labels=[]
    for index in range(18):
        label='calendar%02d'%index
        start=day.replace(hour=10,minute=0)+timedelta(days=index%6,hours=index//6)
        title='QA27 CALENDAR %02d'%index
        if index==0:title+=' '+('LONGCALENDARTITLEWITHOUTSPACES'*7)
        create(label,start=start,end=start+timedelta(hours=1),title=title,az_only=index==1)
        calendar_labels.append(label)
    create('calendar_multi',start=day.replace(hour=0,minute=0)-timedelta(days=1),end=day.replace(hour=0,minute=0)+timedelta(days=2),title='QA27 CALENDAR MULTI DAY')
    create('calendar_online',online=True,specialist=True,title='QA27 CALENDAR ONLINE')
    cancelled_calendar=create('calendar_cancelled',title='QA27 CALENDAR CANCELLED')
    events['calendar_cancelled']=event_domain.cancel_event(actor=users['owner'],event_id=cancelled_calendar.pk,expected_updated_at=cancelled_calendar.updated_at.isoformat(),reason='QA27 calendar cancellation')
    changed_calendar=create('calendar_rescheduled',title='QA27 CALENDAR RESCHEDULED')
    events['calendar_rescheduled']=event_domain.reschedule_event(actor=users['owner'],event_id=changed_calendar.pk,start_datetime=day+timedelta(days=4),end_datetime=day+timedelta(days=4,hours=2),expected_updated_at=changed_calendar.updated_at.isoformat(),reason='QA27 calendar movement')
    calendar_labels+=['calendar_multi','calendar_online','calendar_cancelled','calendar_rescheduled']
    archive_start=previous_month.replace(day=15,hour=10)
    create('archive',start=archive_start,end=archive_start+timedelta(hours=2),title='QA27 ARCHIVE EVENT')
    calendar_fixture={'month':day.strftime('%Y-%m'),'date':day.date().isoformat(),'archive_month':archive_start.strftime('%Y-%m'),'archive_date':archive_start.date().isoformat(),'matching_ids':[events[label].pk for label in calendar_labels],'physical_ids':[events[label].pk for label in calendar_labels if label!='calendar_online'],'labels':{label:events[label].pk for label in calendar_labels},'archive_id':events['archive'].pk,'multiday_dates':[(day+timedelta(days=offset)).date().isoformat()for offset in (-1,0,1)]}
    selected_start=day.replace(hour=0,minute=0)
    calendar_fixture['selected_physical_ids']=[events[label].pk for label in calendar_labels if label!='calendar_online' and events[label].end_datetime>selected_start and events[label].start_datetime<selected_start+timedelta(days=1)]
    calendar_fixture['day_ids']={}
    for offset in (-1,0,1,2,3,4,5):
        start=selected_start+timedelta(days=offset)
        calendar_fixture['day_ids'][start.date().isoformat()]=[events[label].pk for label in calendar_labels if events[label].end_datetime>start and events[label].start_datetime<start+timedelta(days=1)]
    # Change today's Place without modifying the approved occurrence snapshots.
    from catalog.services.location_assignment import set_location_override
    venue.address='QA27 TODAY ADDRESS';venue.lat=40.9;venue.lng=49.9
    set_location_override(venue,actor=users['reviewer'],city='baku',district='baku_narimanov',reason='QA27 synthetic authorized movement')
    venue.save()
    head,revision=submit_review(target=events['physical'],user=users['author'],rating=5,text='QA27 APPROVED REVIEW')
    moderate_candidate(head=head,revision_id=revision.pk,actor=users['reviewer'],approve=True)
    submit_review(target=events['physical'],user=users['author'],rating=1,text='QA27 PENDING EDIT')
    submit_review(target=events['online'],user=users['author'],rating=1,text='QA27 FOREIGN PENDING')
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
        result['created']=[{'name':e.name_az,'status':e.status,'format':e.event_format,'resolved':e.organizer_resolution,'has_place':bool(e.related_place_id),'has_coords':e.lat is not None or e.lng is not None,'address':e.address,'start':e.start_datetime.isoformat() if e.start_datetime else None,'end':e.end_datetime.isoformat() if e.end_datetime else None} for e in Event.objects.filter(name_az__startswith='QA27 BROWSER')]
        return result
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):self.surface('GET')
        def do_POST(self):self.surface('POST')
        def json(self,value):
            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps(value).encode())
        def surface(self,method):
            parsed=urlsplit(self.path);path=parsed.path;cookies=SimpleCookie(self.headers.get('Cookie',''));role=cookies['qa27_actor'].value if 'qa27_actor' in cookies else 'public'
            if role not in clients:self.send_error(403);return
            if path.startswith('/qa27/session/') and method=='GET':
                role=path.rsplit('/',1)[-1];lang=parse_qs(parsed.query).get('lang',['az'])[0]
                if role not in clients or lang not in ('az','ru','en'):self.send_error(400);return
                clients[role].cookies[settings.LANGUAGE_COOKIE_NAME]=lang
                self.send_response(200);self.send_header('Set-Cookie','qa27_actor='+role+'; Path=/; HttpOnly; SameSite=Lax');self.end_headers();return
            if path=='/qa27/fixtures' and method=='GET':self.json({'runtime':{'base':str(settings.BASE_DIR),'static':str(finders.find('admin/css/pages/kidsmap_admin_form_shell.css')),'event':__import__('inspect').getfile(Event),'domain':event_domain.__file__,'query':event_queries.__file__,'calendar':event_calendar.__file__,'controller':__import__('inspect').getfile(__import__('catalog.controllers.place_controller',fromlist=['PlaceController']).PlaceController)},'calendar':calendar_fixture,'paths':paths,'ids':{'org':org.pk,'person':person.pk,'venue':venue.pk,'category':category.code},'date':day.date().isoformat(),'end_date':(day+timedelta(hours=2)).date().isoformat(),'start':day.isoformat(),'end':(day+timedelta(hours=2)).isoformat(),'previous_start':day.isoformat(),'token':token});return
            if path=='/qa27/cohort' and method=='POST':
                params=parse_qs(parsed.query)
                if params.get('token')!=[token] or params.get('enabled') not in (['0'],['1']):self.send_error(403);return
                local_site=SiteSettings.get_solo();local_site.events_section_enabled=params['enabled']==['1'];local_site.save();self.json({'enabled':local_site.events_section_enabled,'synthetic_only':True});return
            if path=='/qa27/state' and method=='GET':self.json(state());close_old_connections();return
            if path=='/qa27/finish' and method=='GET':
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
                    client=clients[role];response=client.generic(method,self.path,data=data,content_type=self.headers.get('Content-Type','application/x-www-form-urlencoded'),HTTP_HOST='127.0.0.1:8787',HTTP_ORIGIN='http://127.0.0.1:8787') if method=='POST' else client.get(self.path,HTTP_HOST='127.0.0.1:8787')
                    requests.append({'role':role,'path':path,'method':method,'status':response.status_code});self.send_response(response.status_code)
                    for name in ('Content-Type','Location','Cache-Control','X-Content-Type-Options'):
                        if response.has_header(name):self.send_header(name,response[name])
                    for morsel in response.cookies.values():self.send_header('Set-Cookie',morsel.OutputString())
                    self.end_headers();self.wfile.write(response.content)
                finally:close_old_connections()
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',8787),Handler);timer=threading.Timer(2400,server.shutdown);timer.daemon=True;timer.start()
    base.dump('browser-ready.json',{'port':8787,'loopback_only':True,'synthetic_only':True})
    try:server.serve_forever(poll_interval=.2)
    finally:timer.cancel();server.server_close()
    return 0 if (base.OUTPUT/'browser-bridge.json').exists() else 1
