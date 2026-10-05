"""Synthetic typed review workflow, actor-specific clients, unchanged QA04 guards."""
import importlib.util
import json
import mimetypes
import threading
from pathlib import Path
spec=importlib.util.spec_from_file_location('qa04_commands',Path(__file__).resolve().parents[2]/'qa04/commands.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
BaselineRunner=base.BaselineRunner
dump=base.dump

def main(mode,labels):
    assert mode=='probe'
    code=base.main(mode,labels)
    if code:return code
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.contrib.staticfiles import finders
    from django.db import close_old_connections
    from django.test import Client
    from django.urls import reverse
    from django.utils import timezone
    from django.utils.translation import override
    from catalog.models import Activity,Specialist,Event,SiteSettings
    from catalog.services.review_versions import review_types,submit_review,moderate_candidate,respond_to_review,refresh_reactions
    from catalog.testcases.utils import create_quality_place
    from datetime import timedelta
    from http.cookies import SimpleCookie
    from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
    from urllib.parse import urlsplit,parse_qs
    settings.LOCALIZED_PLACE_URLS_ENABLED=True
    settings.PUBLIC_BASE_URL='https://kidsmap.az'
    site=SiteSettings.get_solo();site.specialists_section_enabled=True;site.events_section_enabled=True
    site.save(update_fields=['specialists_section_enabled','events_section_enabled'])
    # Keep production cooldown: fixture source dates are old enough for first edit.
    U=get_user_model()
    users={role:U.objects.create_user('qa22_'+role,email=role+'@example.invalid') for role in ('author','owner','voter')}
    users['staff']=U.objects.create_superuser('qa22_staff','staff@example.invalid','synthetic')
    place=create_quality_place(owner=users['owner'],created_by=users['owner'],photo='',cover_photo='',phone1='',website='',lat=None,lng=None)
    activity=Activity.objects.create(place=place,name_az='QA22 dərs',description_az='Sintetik məşğələ',status='published')
    specialist=Specialist.objects.create(owner=users['owner'],name='QA22 Specialist',slug='qa22-specialist',status='published',is_active=True)
    event=Event.objects.create(owner=users['owner'],related_place=place,category=place.category,name='QA22 Event',name_az='QA22 Tədbir',status='published',start_datetime=timezone.now()+timedelta(days=1),end_datetime=timezone.now()+timedelta(days=1,hours=2))
    targets=dict(place=place,activity=activity,specialist=specialist,event=event)
    targets['reject']=create_quality_place(owner=users['owner'],created_by=users['owner'],photo='',cover_photo='',phone1='',website='',lat=None,lng=None)
    heads={};initial={}
    for index,(kind,target) in enumerate(targets.items()):
        head,approved=submit_review(target=target,user=users['author'],rating=5-index,text='QA22 APPROVED '+kind+' </script><script>window.__qa22Injected=true</script>',author_name='Synthetic author')
        moderate_candidate(head=head,revision_id=approved.pk,actor=users['staff'],approve=True)
        head,pending=submit_review(target=target,user=users['author'],rating=1,text='QA22 PENDING '+kind,author_name='Synthetic author')
        types=review_types()['place' if kind=='reject' else kind]
        types[2].objects.filter(review=head).update(created_at=timezone.now()-timedelta(days=2))
        types[1].objects.filter(pk=head.pk).update(created_at=timezone.now()-timedelta(days=2))
        vote=types[3].objects.create(review=head,revision=approved,user=users['voter'],value=1)
        refresh_reactions(head);head.refresh_from_db()
        respond_to_review(head=head,actor=users['owner'],revision_id=approved.pk,kind='reply',text='QA22 PUBLIC REPLY '+kind)
        respond_to_review(head=head,actor=users['owner'],revision_id=approved.pk,kind='report',text='QA22 PRIVATE REPORT '+kind)
        heads[kind]=head
        initial[kind]=dict(head=head.pk,approved=approved.pk,candidate=pending.pk,reaction=vote.pk,rating=5-index)
    clients={'public':Client(enforce_csrf_checks=True,raise_request_exception=False)}
    for role,user in users.items():
        clients[role]=Client(enforce_csrf_checks=True,raise_request_exception=False);clients[role].force_login(user)
    paths={}
    for lang in ('az','ru','en'):
        with override(lang):
            paths[lang]={kind:reverse('typed_reviews',args=['place' if kind=='reject' else kind,target.pk]) for kind,target in targets.items()}
            paths[lang]['dashboard']=reverse('owner_reviews_dashboard')
            paths[lang]['admin']={kind:reverse('admin:catalog_'+head._meta.model_name+'_change',args=[head.pk]) for kind,head in heads.items()}
    allowed_get={p for values in paths.values() for key,p in values.items() if key!='admin'}|{p for values in paths.values() for p in values['admin'].values()}
    allowed_get.add(reverse('admin:jsi18n'))
    allowed_post={values[kind] for values in paths.values() for kind in targets}
    legacy={}
    for lang in ('az','ru','en'):
        with override(lang):
            legacy[lang]={action:reverse('owner_review_'+action,args=[heads['place'].pk]) for action in ('approve','reject')}
            allowed_post.update(legacy[lang].values())
            allowed_post.update(reverse('typed_review_action',args=['place' if kind=='reject' else kind,head.pk,action]) for kind,head in heads.items() for action in ('react','reply','report','approve','reject'))
    requests=[];control_token=base.OUTPUT.name
    actor_locks={actor:threading.RLock() for actor in clients}
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):self.handle_surface('GET')
        def do_POST(self):self.handle_surface('POST')
        def respond_json(self,value):
            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps(value).encode())
        def handle_surface(self,method):
            parsed=urlsplit(self.path);path=parsed.path
            cookies=SimpleCookie(self.headers.get('Cookie',''))
            actor=cookies['qa22_actor'].value if 'qa22_actor'in cookies else'public'
            if actor not in clients:self.send_error(403);return
            if path.startswith('/qa22/session/') and method=='GET':
                role=path.rsplit('/',1)[-1]
                if role not in clients:self.send_error(404);return
                language=parse_qs(parsed.query).get('lang',[None])[0]
                if language is not None and language not in ('az','ru','en'):self.send_error(400);return
                if language:clients[role].cookies[settings.LANGUAGE_COOKIE_NAME]=language
                self.send_response(200);self.send_header('Set-Cookie','qa22_actor='+role+'; Path=/; HttpOnly; SameSite=Lax')
                if language:self.send_header('Set-Cookie',settings.LANGUAGE_COOKIE_NAME+'='+language+'; Path=/; SameSite=Lax')
                self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps({'actor':role,'language':language}).encode());return
            if path=='/qa22/fixtures' and method=='GET':self.respond_json({'paths':paths,'initial':initial,'legacy':legacy,'runToken':control_token});return
            if path=='/qa22/expire-place-gate' and method=='POST':
                if parse_qs(parsed.query).get('token')!=[control_token]:self.send_error(403);return
                from catalog.models import PlaceReviewCooldown
                changed=PlaceReviewCooldown.objects.filter(user=users['author'],place=place).update(next_allowed_at=timezone.now()-timedelta(seconds=1))
                self.respond_json({'synthetic_gate_expired':changed});close_old_connections();return
            if path=='/qa22/invariants' and method=='GET':
                result={}
                for kind,head in heads.items():
                    head.refresh_from_db()
                    result[kind]=dict(approved_text=head.text,current=head.current_revision_id,candidate=head.candidate_revision_id,likes=head.likes_count,dislikes=head.dislikes_count,revision_count=head.revisions.count(),reaction_count=head.reactions.count(),original_reaction_retained=head.reactions.filter(pk=initial[kind]['reaction'],revision_id=initial[kind]['approved']).exists(),reply_count=head.revisions.filter(responses__kind='reply').count(),report_count=head.revisions.filter(responses__kind='report').count())
                self.respond_json(result);close_old_connections();return
            if path=='/qa22/finish' and method=='GET':
                if parse_qs(parsed.query).get('token')!=[control_token]:self.send_error(403);return
                dump('browser-bridge.json',{'status':'PASS','requests':requests,'synthetic_only':True,'outbound_guard':'UNCHANGED'})
                self.respond_json({'finished':True});threading.Thread(target=self.server.shutdown,daemon=True).start();return
            if path in('/qa-font.css','/qa-font.ttf') and method=='GET':
                resource=Path('/root/task33-browser-tools')/('material22.css'if path.endswith('.css')else'material.ttf')
                self.send_response(200);self.send_header('Access-Control-Allow-Origin','*');self.send_header('Content-Type','text/css'if path.endswith('.css')else'font/ttf');self.end_headers();self.wfile.write(resource.read_bytes());return
            if path.startswith('/static/') and method=='GET':
                name=path[len('/static/'):]
                if '..'in Path(name).parts or Path(name).suffix.lower()not in{'.css','.js','.svg','.png','.jpg','.jpeg','.webp','.woff','.woff2','.ttf','.ico'}:self.send_error(404);return
                found=finders.find(name)
                if not found:self.send_error(404);return
                self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(found)[0]or'application/octet-stream');self.end_headers();self.wfile.write(Path(found).read_bytes());return
            if path not in(allowed_get if method=='GET'else allowed_post):self.send_error(404);return
            if method=='POST':
                size=int(self.headers.get('Content-Length','0'))
                if size>20000:self.send_error(413);return
                data=self.rfile.read(size)
            with actor_locks[actor]:
                try:
                    client=clients[actor]
                    if method=='POST':response=client.generic(method,self.path,data=data,content_type=self.headers.get('Content-Type','application/x-www-form-urlencoded'),HTTP_HOST='127.0.0.1:8782',HTTP_ORIGIN=self.headers.get('Origin','http://127.0.0.1:8782'))
                    else:response=client.get(self.path,HTTP_HOST='127.0.0.1:8782')
                    requests.append({'actor':actor,'path':path,'method':method,'status':response.status_code})
                    self.send_response(response.status_code)
                    for name in('Content-Type','Location','Retry-After'):
                        if response.has_header(name):self.send_header(name,response[name])
                    for morsel in response.cookies.values():self.send_header('Set-Cookie',morsel.OutputString())
                    self.end_headers();self.wfile.write(response.content)
                finally:close_old_connections()
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',8782),Handler)
    timer=threading.Timer(2400,server.shutdown);timer.daemon=True;timer.start()
    dump('browser-ready.json',{'port':8782,'loopback_only':True,'synthetic_only':True,'paths':paths})
    try:server.serve_forever(poll_interval=.2)
    finally:timer.cancel();server.server_close()
    return 0 if(base.OUTPUT/'browser-bridge.json').exists()else 1
