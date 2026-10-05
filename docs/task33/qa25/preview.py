"""Loopback-only, allowlisted static Specialist prototype preview; no Django/DB."""
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote, urlsplit
import mimetypes
import argparse

ROOT = Path(__file__).resolve().parents[3]
DESIGN = ROOT / "docs/task33/design"
ASSETS = {
    "/static/img/logo-mark.svg",
    "/static/fonts/MaterialSymbolsRounded.woff2",
    "/static/fonts/chiron/ChironGoRoundTC-PublicSubset.woff2",
}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        name = unquote(urlsplit(self.path).path)
        candidate = (ROOT / name.lstrip("/")).resolve()
        allowed = name in ASSETS or (
            candidate.is_relative_to(DESIGN)
            and candidate.suffix in {".html", ".css", ".js", ".png", ".svg", ".json"}
        )
        if not allowed or not candidate.is_file():
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(candidate.name)[0] or "application/octet-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(candidate.read_bytes())

    def log_message(self, *args):
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8795)
    args = parser.parse_args()
    HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
