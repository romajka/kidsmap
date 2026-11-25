import logging
import re
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace

from django.conf import settings
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.utils.module_loading import import_string


LOGGER = "kidsmap.timing"
HEADER = re.compile(r"app;dur=(\d+\.\d+), db;dur=(\d+\.\d+)")
ROW = re.compile(
    r"url_name=(\w+) method=(\w+) status=(\d+) app_ms=(\d+\.\d+) "
    r"sql_count=(\d+) db_ms=(\d+\.\d+)"
)


@override_settings(DEBUG=False)
class ServerTimingTests(SimpleTestCase):
    databases = {"default"}

    def request(self, path, url_name=None):
        request = RequestFactory().get(path, REMOTE_ADDR="192.0.2.77", HTTP_COOKIE="secret=cookie-marker")
        request.resolver_match = SimpleNamespace(url_name=url_name)
        return request

    def middleware(self, view):
        return import_string(settings.MIDDLEWARE[0])(view)

    def test_response_header_and_single_private_data_free_log_line(self):
        def api_view(request):
            with connection.cursor() as cursor:
                cursor.execute("SELECT %s", ["sql-marker"])
                cursor.execute("SELECT 2")
            return JsonResponse({"ok": True})

        request = self.request("/api/custom/path-marker?query-marker=value", "api_example")
        with self.assertLogs(LOGGER, "INFO") as logs:
            response = self.middleware(api_view)(request)
        self.assertEqual(len(logs.records), 1)
        row = ROW.fullmatch(logs.records[0].getMessage())
        self.assertIsNotNone(row)
        name, method, status, app_ms, count, db_ms = row.groups()
        self.assertEqual((name, method, status, count), ("api_example", "GET", "200", "2"))
        self.assertGreaterEqual(float(app_ms), float(db_ms))
        self.assertEqual(HEADER.fullmatch(response["Server-Timing"]).groups(), (app_ms, db_ms))

    def test_unresolved_redirect_and_errors_keep_status_and_zero_queries(self):
        for status in (301, 404, 500):
            with self.subTest(status=status), self.assertLogs(LOGGER, "INFO") as logs:
                response = self.middleware(lambda request: HttpResponse(status=status))(self.request("/private-marker"))
                self.assertEqual(response.status_code, status)
                self.assertRegex(response["Server-Timing"], HEADER)
            row = ROW.fullmatch(logs.records[0].getMessage())
            self.assertEqual((row[1], row[3], row[5], float(row[6])), ("unresolved", str(status), "0", 0))

    def test_technical_requests_are_timed_without_logging(self):
        for path in ("/static/site.css", "/media/image.jpg", "/favicon.ico", "/healthz", "/healthz/"):
            with self.subTest(path=path), self.assertNoLogs(LOGGER, "INFO"):
                response = self.middleware(lambda request: HttpResponse())(self.request(path))
                self.assertRegex(response.get("Server-Timing", ""), HEADER)
        with self.assertNoLogs(LOGGER, "INFO"):
            self.middleware(lambda request: HttpResponse(content_type="text/plain"))(self.request("/robots.txt"))

    def test_wrapper_is_removed_on_exception(self):
        def broken_view(request):
            raise ValueError("test error")

        before = tuple(connection.execute_wrappers)
        with self.assertLogs(LOGGER, "INFO") as logs, self.assertRaises(ValueError):
            self.middleware(broken_view)(self.request("/broken/"))
        self.assertEqual(tuple(connection.execute_wrappers), before)
        self.assertEqual(ROW.fullmatch(logs.records[0].getMessage())[3], "500")

    def test_four_simultaneous_requests_keep_their_own_sql_counters(self):
        barrier = Barrier(4, timeout=10)

        def view(request):
            with connection.cursor() as cursor:
                barrier.wait()
                for _ in range(request.query_count):
                    cursor.execute("SELECT 1")
                barrier.wait()
            return HttpResponse()

        middleware = self.middleware(view)

        def send(count):
            try:
                request = self.request("/parallel/", f"worker_{count}")
                request.query_count = count
                middleware(request)
            finally:
                connection.close()

        with self.assertLogs(LOGGER, "INFO") as logs, ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(send, (1, 2, 3, 4)))
        counts = sorted((m[1], int(m[5])) for r in logs.records if (m := ROW.fullmatch(r.getMessage())))
        self.assertEqual(counts, [(f"worker_{n}", n) for n in range(1, 5)])

    def test_application_logging_uses_stdout_once(self):
        from config.settings import LOGGING

        entry = LOGGING["loggers"][LOGGER]
        self.assertFalse(entry["propagate"])
        handler_name, = entry["handlers"]
        handler = LOGGING["handlers"][handler_name]
        self.assertEqual(handler["stream"], "ext://sys.stdout")
        self.assertEqual(logging.getLevelName(entry["level"]), logging.INFO)
