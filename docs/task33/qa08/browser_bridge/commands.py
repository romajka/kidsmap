"""Synthetic authenticated forms only; static assets and fixed target routes.

The server never reads application env, working DB/media or arbitrary paths.
Client traffic stays on loopback; application outbound guards remain installed.
"""
import importlib.util,os,json,threading,mimetypes,time
from pathlib import Path
spec=importlib.util.spec_from_file_location('qa04_commands',Path(__file__).resolve().parents[2]/'qa04/commands.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
dump=base.dump

def main(mode,labels):
    assert mode=='probe'
    code=base.main(mode,labels)
    if code:return code
    from django.contrib.auth import get_user_model
    from django.test import Client
    from django.urls import reverse
    from django.utils.translation import override
    from django.contrib.staticfiles import finders
    from django.conf import settings
    from catalog.testcases.utils import create_ready_place
    from catalog.models import Place,VolunteerPlaceRevision
    from http.server import HTTPServer,BaseHTTPRequestHandler
    from urllib.parse import urlsplit,parse_qs
    U=get_user_model();owner=U.objects.create_user(username='browser_stage08_owner');staff=U.objects.create_superuser(username='browser_stage08_staff',email='staff@example.invalid',password='synthetic')
    place=create_ready_place(owner=owner,created_by=owner,photo='',cover_photo='',phone1='',website='https://example.invalid',lat=None,lng=None)
    original_description=place.description_az
    clients={area:Client(enforce_csrf_checks=True) for area in ('owner','admin')}
    for area,client in clients.items():client.force_login(owner if area=='owner' else staff)
    requests=[];started=time.monotonic()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):self.handle_surface('GET')
        def do_POST(self):self.handle_surface('POST')
        def handle_surface(self,method):
            parsed=urlsplit(self.path);path=parsed.path;lang=parse_qs(parsed.query).get('lang',['az'])[0]
            if lang not in ('az','ru','en'):self.send_error(404);return
            if path=='/finish' and method=='GET':
                dump('browser-bridge.json',{'status':'PASS','requests':requests,'outbound_guard':'UNCHANGED','synthetic_only':True,'elapsed_seconds':round(time.monotonic()-started,3)})
                self.send_response(200);self.end_headers();self.wfile.write(b'finished');threading.Thread(target=self.server.shutdown,daemon=True).start();return
            if path=='/invariants' and method=='GET':
                current=Place.objects.get(pk=place.pk);revision=VolunteerPlaceRevision.objects.filter(place=current).first()
                result={'approved_description_preserved':current.description_az==original_description,'published_preserved':current.is_public,'candidate_present':revision is not None,'candidate_description_changed':bool(revision and revision.payload.get('description_az') and revision.payload['description_az']!=original_description)}
                self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps(result).encode());return
            if path.startswith('/static/') and method=='GET':
                name=path[len('/static/'):]
                if '..' in Path(name).parts or Path(name).suffix.lower() not in {'.css','.js','.svg','.png','.jpg','.jpeg','.webp','.woff','.woff2','.ttf','.ico'}:self.send_error(404);return
                found=finders.find(name)
                if not found:self.send_error(404);return
                self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(found)[0] or 'application/octet-stream');self.end_headers();self.wfile.write(Path(found).read_bytes());return
            area=path.strip('/')
            if area not in clients:self.send_error(404);return
            with override(lang):
                route=reverse('owner_place_edit',args=[place.pk]) if area=='owner' else reverse('admin:catalog_place_change',args=[place.pk])
                client=clients[area]
                if method=='POST':
                    size=int(self.headers.get('Content-Length','0'))
                    if size>500000:self.send_error(413);return
                    response=client.generic('POST',route,data=self.rfile.read(size),content_type=self.headers.get('Content-Type','application/x-www-form-urlencoded'),HTTP_HOST='127.0.0.1:8768',HTTP_ACCEPT_LANGUAGE=lang)
                else:response=client.get(route,HTTP_HOST='127.0.0.1:8768',HTTP_ACCEPT_LANGUAGE=lang)
                status=response.status_code;requests.append({'area':area,'lang':lang,'method':method,'django_status':status})
                if status in (301,302,303):response=client.get(route,HTTP_HOST='127.0.0.1:8768',HTTP_ACCEPT_LANGUAGE=lang)
                self.send_response(response.status_code);self.send_header('X-QA-Django-Status',str(status));self.send_header('Content-Type',response.get('Content-Type','text/html'));self.end_headers();self.wfile.write(response.content)
        def log_message(self,*args):pass
    server=HTTPServer(('127.0.0.1',8768),Handler)
    timer=threading.Timer(600,server.shutdown);timer.daemon=True;timer.start()
    dump('browser-ready.json',{'port':8768,'loopback_only':True,'synthetic_only':True,'surfaces':['owner','admin']})
    try:server.serve_forever(poll_interval=.2)
    finally:timer.cancel();server.server_close()
    return 0 if (base.OUTPUT/'browser-bridge.json').exists() else 1
