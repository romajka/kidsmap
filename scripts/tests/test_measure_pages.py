import io
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from unittest import TestCase
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "measure_pages.py"


class MeasurePagesTests(TestCase):
    def test_five_gets_medians_and_visible_errors(self):
        paths = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                paths.append(self.path)
                if self.path == "/redirect":
                    self.send_response(302)
                    self.send_header("Location", "/ok")
                else:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    if self.path == "/ok":
                        n = paths.count("/ok")
                        self.send_header("Server-Timing", f"app;dur={n}, db;dur={n/2}")
                self.end_headers()
                self.wfile.write(b"<p>hello</p>")

            def log_message(self, *args):
                pass

        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = Thread(target=server.serve_forever)
            thread.start()
            try:
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), "--base", f"http://127.0.0.1:{server.server_port}",
                     "/ok", "/missing-header", "/redirect"],
                    capture_output=True, text=True, timeout=15,
                )
            finally:
                server.shutdown()
                thread.join()
        self.assertEqual(paths, ["/ok"] * 5 + ["/missing-header"] * 5 + ["/redirect"] * 5)
        self.assertNotEqual(result.returncode, 0)
        ok, = (line for line in result.stdout.splitlines() if line.startswith("/ok\t"))
        _, hits, ttfb, size, timing = ok.split("\t")
        self.assertEqual((hits, size, timing), ("5/5", "12", "app;dur=3.000, db;dur=1.500"))
        self.assertGreater(float(ttfb), 0)
        self.assertIn("unavailable", result.stdout)
        self.assertIn("302", result.stderr)

    def test_permanent_redirect_is_measured_without_following_it(self):
        seen = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                seen.append(self.path)
                self.send_response(301)
                self.send_header("Location", "/ru/afisha/")
                self.send_header("Server-Timing", "app;dur=1, db;dur=0")
                self.end_headers()

            def log_message(self, *args):
                pass

        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = Thread(target=server.serve_forever)
            thread.start()
            try:
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), "--base", f"http://127.0.0.1:{server.server_port}",
                     "--redirect", "/ru/events/", "/ru/afisha/"], capture_output=True, text=True, timeout=15,
                )
            finally:
                server.shutdown()
                thread.join()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(seen, ["/ru/events/"] * 5)
        self.assertIn("5/5", result.stdout)
        self.assertIn("db;dur=0.000", result.stdout)

    def test_first_byte_precedes_slow_headers_and_body(self):
        from scripts import measure_pages

        now = [1.0]

        class Stream(io.BufferedReader):
            def readline(self, *args):
                now[0] += 5
                return super().readline(*args)

            def read(self, *args):
                now[0] += 15
                return super().read(*args)

        stream = Stream(io.BytesIO(b"HTTP/1.1 200 OK\r\nContent-Length: 1\r\n\r\nx"))

        class Socket:
            def makefile(self, mode):
                return stream

        with patch.object(measure_pages, "perf_counter", side_effect=lambda: now[0]):
            response = measure_pages.TimedResponse(Socket())
            response.begin()
            self.assertEqual(response.read(), b"x")
            self.assertEqual(response.first_byte_at, 1.0)
            self.assertGreater(now[0], response.first_byte_at)
