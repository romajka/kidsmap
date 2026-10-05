"""Bounded read-only public routes, synthetic data and loopback static server."""
import importlib.util
import json
import mimetypes
import threading
from pathlib import Path
spec = importlib.util.spec_from_file_location('qa04_commands', Path(__file__).resolve().parents[2] / 'qa04/commands.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
BaselineRunner = base.BaselineRunner
dump = base.dump

def main(mode, labels):
    assert mode == 'probe'
    code = base.main(mode, labels)
    if code:
        return code
    from django.contrib.auth import get_user_model
    from django.conf import settings
    from django.contrib.staticfiles import finders
    from django.test import Client
    from django.utils import timezone
    from django.utils.translation import override
    from catalog.models import Place, Organization, Program, Activity, OfferingGroup, PricingPlan, PlaceReview
    from catalog.services import organization_ownership
    from catalog.testcases.utils import create_quality_place
    from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
    from urllib.parse import urlsplit
    settings.LOCALIZED_PLACE_URLS_ENABLED = True
    settings.PUBLIC_BASE_URL = 'https://kidsmap.az'
    owner = get_user_model().objects.create_user('browser21_synthetic', email='browser21@example.invalid')
    common = dict(owner=owner, created_by=owner, photo='', cover_photo='', phone1='', website='', lat=None, lng=None)
    fallback = create_quality_place(**common, name_az='Yerli məkan', name_ru='', name_en='', description_ru='', description_en='')
    complete = create_quality_place(**common, name_az='Tam məkan', name_ru='Полный перевод', name_en='Complete translation', description_ru='Музыкальные занятия для детей', description_en='Music lessons for children')
    from PIL import Image
    Image.new('RGB', (640, 400), '#eaf5ec').save(Path(settings.MEDIA_ROOT) / 'browser21-fixture.png')
    Place.objects.filter(pk=complete.pk).update(photo='browser21-fixture.png')
    complete.refresh_from_db()
    PlaceReview.objects.create(place=complete, user=owner, author_name='Synthetic reviewer', rating=5, text='QA21 stable review text', is_approved=True, status='approved')
    closed = create_quality_place(**common, name_az='Bağlı məkan', name_ru='', name_en='', description_ru='', description_en='')
    Place.objects.filter(pk=closed.pk).update(operating_state='closed', operating_state_approved_at=timezone.now())
    org = Organization.objects.create(owner=owner, created_by=owner, name_az='Açıq təşkilat', description_az='Musiqi </script><script>window.__qa21Injected=true</script> & dərslər', status='published', approved_at=timezone.now())
    organization_ownership.request_join(actor=owner, place_id=fallback.pk, organization_id=org.pk)
    fallback.refresh_from_db()
    program = Program.objects.create(organization=org, name_az='Musiqi proqramı', description_az='Uşaqlar üçün musiqi məşğələləri', status='published', approved_at=timezone.now())
    activity = Activity.objects.create(place=fallback, program=program, status='published', supplement_az='Yerli əlavə')
    group = OfferingGroup.objects.create(activity=activity, name_az='Kiçik qrup', language='en', age_from=5, age_to=8, schedule_text='Şənbə 10:00')
    PricingPlan.objects.create(offering_group=group, product_type='lesson', price='25')
    paths = {}
    for lang in ('az', 'ru', 'en'):
        with override(lang):
            prefix = '' if lang == 'az' else '/' + lang
            paths[lang] = {key: obj.get_absolute_url() for key, obj in [('fallback', fallback), ('complete', complete), ('closed', closed)]}
            paths[lang].update(organization=f'{prefix}/organizations/{org.public_id}/', activity=f'{prefix}/activities/{activity.pk}/')
            paths[lang]['legacy'] = f'{prefix}/place/{fallback.pk}/'
    allowed = {p for values in paths.values() for p in values.values()}
    client = Client()
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path = urlsplit(self.path).path
            if path == '/finish':
                base.dump('browser-bridge.json', dict(status='PASS', requests=requests, synthetic_only=True, outbound_guard='UNCHANGED'))
                self.send_response(200); self.end_headers(); self.wfile.write(b'finished')
                threading.Thread(target=self.server.shutdown, daemon=True).start(); return
            if path == '/fixtures':
                self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(json.dumps(paths).encode()); return
            if path in ('/qa-font.css', '/qa-font.ttf'):
                resource = Path('/root/task33-browser-tools') / ('material.css' if path.endswith('.css') else 'material.ttf')
                self.send_response(200); self.send_header('Access-Control-Allow-Origin', '*'); self.send_header('Content-Type', 'text/css' if path.endswith('.css') else 'font/ttf'); self.end_headers(); self.wfile.write(resource.read_bytes()); return
            if path == '/media/browser21-fixture.png':
                self.send_response(200); self.send_header('Content-Type', 'image/png'); self.end_headers(); self.wfile.write((Path(settings.MEDIA_ROOT) / 'browser21-fixture.png').read_bytes()); return
            if path.startswith('/static/'):
                name = path[len('/static/'):]
                if '..' in Path(name).parts or Path(name).suffix.lower() not in {'.css', '.js', '.svg', '.png', '.jpg', '.jpeg', '.webp', '.woff', '.woff2', '.ttf', '.ico'}:
                    self.send_error(404); return
                found = finders.find(name)
                if not found:
                    self.send_error(404); return
                self.send_response(200); self.send_header('Content-Type', mimetypes.guess_type(found)[0] or 'application/octet-stream'); self.end_headers(); self.wfile.write(Path(found).read_bytes()); return
            if path not in allowed:
                self.send_error(404); return
            response = client.get(self.path, HTTP_HOST='127.0.0.1:8781')
            requests.append(dict(path=path, status=response.status_code))
            self.send_response(response.status_code)
            for name in ('Content-Type', 'Location'):
                if response.has_header(name): self.send_header(name, response[name])
            self.end_headers(); self.wfile.write(response.content)
        def log_message(self, *args): pass
    server = ThreadingHTTPServer(('127.0.0.1', 8781), Handler)
    timer = threading.Timer(1800, server.shutdown); timer.daemon = True; timer.start()
    base.dump('browser-ready.json', dict(port=8781, loopback_only=True, synthetic_only=True, paths=paths))
    try:
        server.serve_forever(poll_interval=.2)
    finally:
        timer.cancel(); server.server_close()
    return 0 if (base.OUTPUT / 'browser-bridge.json').exists() else 1
