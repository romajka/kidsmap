"""Synthetic stage 12 owner surfaces on a disposable QA04 PostgreSQL database."""
import importlib.util
import json
import mimetypes
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from http.cookies import SimpleCookie

spec = importlib.util.spec_from_file_location(
    "qa04_commands", Path(__file__).resolve().parents[3] / "qa04" / "commands.py"
)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
dump = base.dump


def main(mode, labels):
    assert mode == "probe" and not labels
    code = base.main(mode, labels)
    if code:
        return code

    from django.contrib.auth import get_user_model
    from django.db.models import F
    from django.contrib.staticfiles import finders
    from django.test import Client
    from django.urls import reverse
    from django.utils.translation import override
    from catalog.models import Organization, Place
    from catalog.services.organization_ownership import request_join, confirm_join
    from catalog.services import business_team
    from catalog.testcases.utils import create_quality_place

    User = get_user_model()
    owner = User.objects.create_user(username="stage12_browser_owner", email="owner@example.invalid")
    zero = User.objects.create_user(username="stage12_browser_zero", email="zero@example.invalid")
    standalone = User.objects.create_user(username="stage12_browser_standalone", email="standalone@example.invalid")
    manager = User.objects.create_user(username="stage12_browser_manager", email="manager@example.invalid")
    org_empty = Organization.objects.create(owner=owner, created_by=owner, name_az="Boş təşkilat", name_ru="Организация без филиалов", name_en="Organization without branches")
    org_network = Organization.objects.create(owner=owner, created_by=owner, name_az="Şəbəkə", name_ru="Сеть центров", name_en="Center network")
    branch_a = create_quality_place(owner=owner, created_by=owner)
    branch_b = create_quality_place(owner=owner, created_by=owner)
    own_place = create_quality_place(owner=standalone, created_by=standalone)
    request_join(actor=owner, place_id=branch_a.pk, organization_id=org_network.pk)
    request_join(actor=owner, place_id=branch_b.pk, organization_id=org_network.pk)
    invitation = business_team.invite(actor=owner, target_type="organization", target_id=org_network.pk,
        email=manager.email, role="MANAGER", actions=["organization.view", "place.view", "place.edit"],
        scope="selected_places", place_ids=[branch_a.pk])
    business_team.accept(actor=manager, target_type="organization", invitation_id=invitation.pk)
    org_network.status = "published"
    org_network.save(update_fields=["status"])
    place_owner = User.objects.create_user(username="stage12_browser_place_owner", email="place-owner@example.invalid")
    linked_place = create_quality_place(owner=place_owner, created_by=place_owner, name="Linked QA place", name_az="Linked QA place")
    pending_place = create_quality_place(owner=place_owner, created_by=place_owner, name="Pending QA place", name_az="Pending QA place")
    stale_place = create_quality_place(owner=place_owner, created_by=place_owner, name="Stale QA place", name_az="Stale QA place")
    linked_request = request_join(actor=owner, place_id=linked_place.pk, organization_id=org_network.pk)
    confirm_join(actor=place_owner, request_id=linked_request.pk)
    stale_request = request_join(actor=owner, place_id=stale_place.pk, organization_id=org_network.pk)
    clients = {}
    for label, user in (("owner", owner), ("zero", zero), ("standalone", standalone), ("manager", manager), ("place-owner", place_owner)):
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)
        clients[label] = client

    scenarios = [
        {"id": "zero", "path": "/zero", "status": 200},
        {"id": "org-empty", "path": "/org-empty", "status": 200},
        {"id": "org-network", "path": "/org-network", "status": 200},
        {"id": "standalone", "path": "/standalone", "status": 200},
        {"id": "manager-selected", "path": "/manager-selected", "status": 200},
        {"id": "manager-forbidden", "path": "/manager-forbidden", "status": 404},
    ]
    route_table = {
        "/zero": ("zero", "organization_workspace_index", {}),
        "/org-empty": ("owner", "organization_workspace_detail", {"org_id": org_empty.pk}),
        "/org-network": ("owner", "organization_workspace_detail", {"org_id": org_network.pk}),
        "/standalone": ("standalone", "organization_workspace_index", {}),
        "/manager-selected": ("manager", "organization_workspace_detail", {"org_id": org_network.pk}),
        "/manager-forbidden": ("manager", "organization_workspace_detail", {"org_id": org_empty.pk}),
        "/place-owner": ("place-owner", "owner_places_dashboard", {}),
    }
    requests = []
    started = time.monotonic()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlsplit(self.path)
            pathname = parsed.path
            lang = parse_qs(parsed.query).get("lang", ["az"])[0]
            if lang not in ("az", "ru", "en"):
                self.send_error(404)
                return
            if pathname == "/make-stale":
                Place.objects.filter(pk=stale_place.pk).update(content_version=F("content_version")+1)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"stale")
                return
            if pathname == "/finish":
                base.dump("browser-bridge.json", {"status": "PASS", "requests": requests,
                    "synthetic_only": True, "loopback_only": True,
                    "elapsed_seconds": round(time.monotonic() - started, 3)})
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"finished")
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            if pathname == "/scenarios":
                body = json.dumps(scenarios).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)
                return
            if pathname.startswith("/static/"):
                name = pathname[len("/static/"):]
                if ".." in Path(name).parts or Path(name).suffix.lower() not in {".css", ".js", ".svg", ".png", ".jpg", ".jpeg", ".webp", ".woff", ".woff2", ".ttf", ".ico"}:
                    self.send_error(404)
                    return
                found = finders.find(name)
                if not found:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", mimetypes.guess_type(found)[0] or "application/octet-stream")
                self.end_headers()
                self.wfile.write(Path(found).read_bytes())
                return
            if pathname not in route_table:
                self.send_error(404)
                return
            identity, route_name, kwargs = route_table[pathname]
            with override(lang):
                route = reverse(route_name, kwargs=kwargs)
                response = clients[identity].get(route, HTTP_HOST="127.0.0.1:8772", HTTP_ACCEPT_LANGUAGE=lang)
            requests.append({"scenario": pathname, "lang": lang, "status": response.status_code})
            self.send_response(response.status_code)
            self.send_header("Content-Type", response.get("Content-Type", "text/html"))
            self.send_header("Set-Cookie", f"qa_identity={identity}; Path=/; SameSite=Lax")
            self.send_header("Set-Cookie", f"qa_lang={lang}; Path=/; SameSite=Lax")
            self.end_headers()
            self.wfile.write(response.content)

        def do_POST(self):
            cookies = SimpleCookie()
            cookies.load(self.headers.get("Cookie", ""))
            identity = cookies.get("qa_identity")
            lang_cookie = cookies.get("qa_lang")
            identity = identity.value if identity else ""
            lang = lang_cookie.value if lang_cookie else "az"
            if identity not in clients or lang not in ("az", "ru", "en"):
                self.send_error(403)
                return
            pathname = urlsplit(self.path).path
            with override(lang):
                allowed = {
                    reverse("organization_workspace_join", args=[org_network.pk]),
                    reverse("organization_workspace_confirm", args=[org_network.pk, stale_request.pk]),
                    reverse("organization_workspace_detach", args=[org_network.pk, linked_place.pk]),
                }
                if pathname not in allowed:
                    self.send_error(404)
                    return
                length = int(self.headers.get("Content-Length", "0"))
                if length > 4096:
                    self.send_error(413)
                    return
                data = {key: values[-1] for key, values in parse_qs(self.rfile.read(length).decode(), keep_blank_values=True).items()}
                response = clients[identity].post(pathname, data, HTTP_HOST="127.0.0.1:8772", HTTP_ACCEPT_LANGUAGE=lang)
            requests.append({"scenario": "POST " + pathname, "lang": lang, "status": response.status_code})
            self.send_response(response.status_code)
            self.send_header("Content-Type", response.get("Content-Type", "text/html"))
            if response.status_code in (301, 302):
                self.send_header("Location", "/place-owner?lang=" + lang)
            self.end_headers()
            self.wfile.write(response.content)

        def log_message(self, *_):
            pass

    server = HTTPServer(("127.0.0.1", 8772), Handler)
    timer = threading.Timer(900, server.shutdown)
    timer.daemon = True
    timer.start()
    base.dump("browser-ready.json", {"port": 8772, "loopback_only": True, "synthetic_only": True,
        "scenarios": [x["id"] for x in scenarios]})
    try:
        server.serve_forever(poll_interval=.2)
    finally:
        timer.cancel()
        server.server_close()
    return 0 if (base.OUTPUT / "browser-bridge.json").exists() else 1
