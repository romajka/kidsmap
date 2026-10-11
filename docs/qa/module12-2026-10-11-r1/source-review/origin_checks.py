"""Verify actual port-validation source without Django setup, HTTP or DB access."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import django
from django.utils.http import url_has_allowed_host_and_scheme
import django.utils.http as django_http

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
app_path = ROOT / "src/catalog/views.py"
source = app_path.read_bytes()
head_source = subprocess.check_output(["git", "show", "HEAD:src/catalog/views.py"], cwd=ROOT)
tree = ast.parse(source.decode("utf-8-sig"))
names = {"_allowed_tracking_hosts", "_has_allowed_tracking_origin"}
nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
module = ast.Module(body=nodes, type_ignores=[])
namespace = {"settings": SimpleNamespace(CSRF_TRUSTED_ORIGINS=[]), "url_has_allowed_host_and_scheme": url_has_allowed_host_and_scheme}
exec(compile(module, str(app_path), "exec"), namespace)

class Request:
    def __init__(self, headers, host="localhost:8829", secure=False):
        self.headers = headers
        self._host = host
        self._secure = secure
    def get_host(self):
        return self._host
    def is_secure(self):
        return self._secure

cases = [
    ("same-origin explicit local port", {"Origin": "http://localhost:8829"}, False, True),
    ("portless same-host origin", {"Origin": "http://localhost"}, True, True),
    ("foreign origin", {"Origin": "https://evil.example"}, False, False),
    ("same-origin explicit local Referer port", {"Referer": "http://localhost:8829/ru/"}, False, True),
    ("no Origin or Referer with same-origin fetch marker", {"Sec-Fetch-Site": "same-origin"}, True, True),
    ("explicit default port", {"Origin": "http://localhost:80"}, False, None),
]
rows = []
for name, headers, expected_implementation, same_origin_expectation in cases:
    request = Request(headers)
    actual = namespace["_has_allowed_tracking_origin"](request)
    assert actual == expected_implementation, (name, actual)
    rows.append({"case": name, "actual": actual, "source_expectation": expected_implementation, "same_origin_contract_expectation": same_origin_expectation})
namespace["settings"].CSRF_TRUSTED_ORIGINS = ["http://fixture.example:8829"]
trusted_actual = namespace["_has_allowed_tracking_origin"](Request({"Origin": "http://fixture.example:8829"}))
assert trusted_actual is False
rows.append({"case": "configured trusted origin explicit port", "actual": trusted_actual, "source_expectation": False, "trusted_origin_contract_expectation": True})
evidence = {
    "mode": "AUDIT ONLY / source function execution, no Django setup / HTTP / DB",
    "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "django_version": django.get_version(),
    "app_source_sha256": hashlib.sha256(source).hexdigest(),
    "app_matches_head_after_line_ending_normalization": source.replace(b"\r\n", b"\n") == head_source.replace(b"\r\n", b"\n"),
    "app_functions": [{"name": node.name, "line": node.lineno, "end_line": node.end_lineno} for node in nodes],
    "django_helper_path": str(Path(django_http.__file__).resolve()),
    "django_helper_sha256": hashlib.sha256(Path(django_http.__file__).read_bytes()).hexdigest(),
    "results": rows,
}
assert evidence["app_matches_head_after_line_ending_normalization"]
(OUT / "origin-checks.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"source_checks": len(rows), "implementation_checks": "PASS", "same_origin_portless": True, "same_origin_explicit_port": False, "app_matches_head": True, "external": "NOT RUN"}))
