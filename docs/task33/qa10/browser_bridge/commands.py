"""Stage 10 synthetic public/admin browser fixture on disposable QA04 PostgreSQL."""
import importlib.util
import json
import mimetypes
import threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

spec = importlib.util.spec_from_file_location('qa04_commands', Path(__file__).resolve().parents[2] / 'qa04/commands.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
dump = base.dump


def main(mode, labels):
    assert mode == 'probe'
    code = base.main(mode, labels)
    if code:
        return code
    from django.contrib.auth import get_user_model
    from django.contrib.staticfiles import finders
    from django.test import Client
    from django.urls import reverse
    from django.utils.translation import override
    from catalog.models import Activity, OfferingGroup
    from catalog.services.pricing_plans import replace_group_pricing_plans, replace_place_pricing_plans
    from catalog.testcases.utils import create_ready_place

    place = create_ready_place(photo='', cover_photo='')
    replace_place_pricing_plans(place, [])
    activity = Activity.objects.create(place=place, name_az='Robotika', name_ru='Робототехника', name_en='Robotics')
    Activity.objects.filter(pk=activity.pk).update(status='published')
    activity.refresh_from_db()
    group = OfferingGroup.objects.create(activity=activity, name_az='5–8 yaş', name_ru='5–8 лет', name_en='Ages 5–8', age_from=5, age_to=8)
    replace_group_pricing_plans(group, [
        {'product_type': 'membership', 'price': '90', 'billing_mode': 'recurring', 'billing_interval': 'month', 'billing_interval_count': 1, 'title_az': 'Aylıq', 'title_ru': 'Абонемент', 'title_en': 'Membership'},
        {'product_type': 'lesson', 'price_kind': 'free', 'price': '0', 'is_trial': True, 'title_az': 'Sınaq dərsi', 'title_ru': 'Пробное занятие', 'title_en': 'Trial lesson'},
        {'product_type': 'registration_fee', 'charge_role': 'registration_fee', 'price': '15', 'is_required': True, 'title_az': 'Qeydiyyat', 'title_ru': 'Вступительный взнос', 'title_en': 'Registration fee'},
    ])
    staff = get_user_model().objects.create_superuser(username='stage10_browser_staff', email='staff@example.invalid', password='synthetic')
    clients = {'public': Client(), 'admin': Client(enforce_csrf_checks=True)}
    clients['admin'].force_login(staff)
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.handle_surface('GET')

        def do_POST(self):
            self.handle_surface('POST')

        def handle_surface(self, method):
            parsed = urlsplit(self.path)
            path = parsed.path
            lang = parse_qs(parsed.query).get('lang', ['az'])[0]
            if lang not in ('az', 'ru', 'en'):
                self.send_error(404)
                return
            if path == '/fixture':
                current = type(place).objects.get(pk=place.pk)
                body = json.dumps({'place_id': place.pk, 'base_content_version': current.content_version, 'activity_id': activity.pk, 'group_id': group.pk}).encode()
                self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(body); return
            if path == '/finish':
                base.dump('browser-bridge.json', {'status': 'PASS', 'requests': requests, 'synthetic_only': True, 'loopback_only': True})
                self.send_response(200); self.end_headers(); self.wfile.write(b'finished')
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            if path.startswith('/static/'):
                name = path[len('/static/'):]
                if '..' in Path(name).parts or Path(name).suffix.lower() not in {'.css', '.js', '.svg', '.png', '.jpg', '.jpeg', '.webp', '.woff', '.woff2', '.ttf', '.ico'}:
                    self.send_error(404); return
                found = finders.find(name)
                if not found:
                    self.send_error(404); return
                self.send_response(200); self.send_header('Content-Type', mimetypes.guess_type(found)[0] or 'application/octet-stream'); self.end_headers(); self.wfile.write(Path(found).read_bytes()); return
            area = 'admin' if path == '/admin' or path.endswith('/pricing/import/validate/') else 'public' if path == '/detail' else None
            if area is None:
                self.send_error(404); return
            with override(lang):
                route = reverse('admin:catalog_place_change', args=[place.pk]) if path == '/admin' else reverse('admin:catalog_place_pricing_import_validate') if area == 'admin' else place.get_absolute_url()
                client = clients[area]
                kwargs = {'HTTP_HOST': '127.0.0.1:8769', 'HTTP_ACCEPT_LANGUAGE': lang}
                if method == 'POST':
                    size = int(self.headers.get('Content-Length', '0'))
                    if size > 500000:
                        self.send_error(413); return
                    response = client.generic('POST', route, data=self.rfile.read(size), content_type=self.headers.get('Content-Type', 'application/json'), HTTP_X_CSRFTOKEN=self.headers.get('X-CSRFToken', ''), **kwargs)
                else:
                    response = client.get(route, **kwargs)
                requests.append({'area': area, 'lang': lang, 'method': method, 'status': response.status_code})
                self.send_response(response.status_code)
                self.send_header('Content-Type', response.get('Content-Type', 'text/html'))
                self.end_headers(); self.wfile.write(response.content)

        def log_message(self, *args):
            pass

    server = HTTPServer(('127.0.0.1', 8769), Handler)
    timer = threading.Timer(600, server.shutdown); timer.daemon = True; timer.start()
    base.dump('browser-ready.json', {'port': 8769, 'loopback_only': True, 'synthetic_only': True, 'surfaces': ['public', 'admin']})
    try:
        server.serve_forever(poll_interval=.2)
    finally:
        timer.cancel(); server.server_close()
    return 0 if (base.OUTPUT / 'browser-bridge.json').exists() else 1
