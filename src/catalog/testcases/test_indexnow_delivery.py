import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, nullcontext
from datetime import datetime, timedelta, timezone
from io import StringIO
from threading import Event
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from django.core.cache import caches
from django.core.cache.backends.redis import RedisCache
from django.core.management import call_command
from django.db import connections, transaction
from django.test import TestCase, TransactionTestCase, override_settings

from catalog.services.indexnow import enqueue_indexnow_urls, submit_indexnow_urls
from catalog.services.indexnow_cache import url_key
from catalog.testcases.test_indexnow import INDEXNOW_TEST_SETTINGS
from catalog.testcases.utils import create_quality_place


URL = "https://kidsmap.az/place/indexnow-test/"
START = datetime(2026, 11, 25, tzinfo=timezone.utc)
TRANSPORT = "catalog.services.indexnow.urlopen"


def response(status):
    return nullcontext(SimpleNamespace(status=status))


@contextmanager
def at(seconds):
    with patch("django.utils.timezone.now", return_value=START + timedelta(seconds=seconds)) as clock:
        # LocMem uses the process clock for expiry. Redis uses its own server clock.
        with patch("time.time", side_effect=lambda: clock.return_value.timestamp()):
            yield clock


def expire_redis_key(test, suffix, expected_ttl):
    backend = caches["default"]
    if isinstance(backend, RedisCache):
        key = url_key(URL) + suffix
        redis = backend._cache.get_client(write=True)
        ttl = redis.ttl(backend.make_key(key))
        test.assertGreater(ttl, expected_ttl - 5)
        test.assertLessEqual(ttl, expected_ttl)
        # Advance this key to its expiry without waiting an hour in the suite.
        backend.touch(key, timeout=0)


def run_cron():
    call_command("indexnow_retry", stdout=StringIO())


@override_settings(**INDEXNOW_TEST_SETTINGS)
class IndexNowDeliveryTests(TestCase):
    def test_accepted_cooldown_starts_at_response_and_expires_after_an_hour(self):
        with at(0) as clock:
            def slow_response(*args, **kwargs):
                self.assertIsNone(caches["default"].get(url_key(URL) + ":sent"))
                clock.return_value += timedelta(seconds=10)
                return response(200)

            with patch(TRANSPORT, side_effect=slow_response) as transport:
                self.assertTrue(submit_indexnow_urls([URL]).accepted)
                clock.return_value = START + timedelta(seconds=3609)
                self.assertEqual(submit_indexnow_urls([URL]).submitted_count, 0)
                expire_redis_key(self, ":sent", 3600)
                clock.return_value = START + timedelta(seconds=3610)
                self.assertTrue(submit_indexnow_urls([URL]).accepted)
                self.assertEqual(transport.call_count, 2)

    @patch("catalog.services.indexnow.MAX_URLS_PER_REQUEST", 1)
    def test_cooled_urls_do_not_use_up_the_http_batch_limit(self):
        other = "https://kidsmap.az/place/other/"
        with patch(TRANSPORT, side_effect=lambda *args, **kwargs: response(200)) as transport:
            submit_indexnow_urls([URL])
            self.assertTrue(submit_indexnow_urls([URL, other]).accepted)
            self.assertEqual(json.loads(transport.call_args.args[0].data)["urlList"], [other])

    def test_transient_errors_are_retried_by_cron_without_another_publication(self):
        for index, error in enumerate((
            HTTPError(URL, 503, "unavailable", {}, None),
            HTTPError(URL, 429, "limited", {}, None),
            TimeoutError(),
            URLError("offline"),
        )):
            url = f"{URL.rstrip('/')}-{index}/"
            with self.subTest(error=error), patch(TRANSPORT, side_effect=[error, response(202)]) as transport:
                with at(0):
                    self.assertFalse(submit_indexnow_urls([url]).accepted)
                with at(59):
                    run_cron()
                    self.assertEqual(transport.call_count, 1)
                with at(60):
                    run_cron()
                    self.assertEqual(transport.call_count, 2)
                    run_cron()
                    self.assertEqual(submit_indexnow_urls([url]).submitted_count, 0)
                    self.assertEqual(transport.call_count, 2)

    def test_next_edit_of_same_place_resubmits_immediately_without_cron(self):
        with override_settings(INDEXNOW_KEY=""):
            place = create_quality_place(
                name="IndexNow no cron", uses_slug_only_urls=False, with_subcategory=True,
            )

        with patch(TRANSPORT, side_effect=[response(503), response(200)]) as transport:
            for address in ("Baku address 41", "Baku address 42"):
                with ThreadPoolExecutor(1) as pool, patch("catalog.services.indexnow._executor", pool):
                    with self.captureOnCommitCallbacks(execute=True):
                        place.address = address
                        place.save(update_fields=["address", "updated_at"])
            self.assertEqual(transport.call_count, 2)
            first, second = [json.loads(call.args[0].data)["urlList"] for call in transport.call_args_list]
            self.assertEqual(set(first), set(second))
            self.assertIn(f"https://kidsmap.az/place/{place.pk}-{place.slug}/", first)

    def test_new_publication_can_deliver_a_due_retry(self):
        with patch(TRANSPORT, side_effect=[response(503), response(200)]) as transport:
            with at(0):
                self.assertFalse(submit_indexnow_urls([URL]).accepted)
            with at(60):
                self.assertTrue(submit_indexnow_urls([URL]).accepted)
                run_cron()
                self.assertEqual(transport.call_count, 2)

    def test_backoff_intervals_and_three_retry_limit(self):
        with patch(TRANSPORT, side_effect=lambda *args, **kwargs: response(503)) as transport:
            with at(0):
                submit_indexnow_urls([URL])
            for count, due in enumerate((60, 360, 2160), start=1):
                with at(due - 1):
                    run_cron()
                    self.assertEqual(transport.call_count, count)
                with at(due):
                    run_cron()
                    self.assertEqual(transport.call_count, count + 1)
            with at(10000):
                run_cron()
                self.assertEqual(transport.call_count, 4)

    def test_late_response_does_not_clear_the_new_owners_retry(self):
        def late_response(*args, **kwargs):
            with at(61), patch(TRANSPORT, return_value=response(429)) as replacement:
                expire_redis_key(self, ":lease", 60)
                run_cron()
                self.assertEqual(replacement.call_count, 1)
            return response(200)

        with at(0), patch(TRANSPORT, side_effect=late_response):
            submit_indexnow_urls([URL])
        # The replacement spent attempt two, so its retry is due five minutes later.
        with patch(TRANSPORT, return_value=response(202)) as transport:
            with at(360):
                run_cron()
                transport.assert_not_called()
            with at(361):
                run_cron()
                self.assertEqual(transport.call_count, 1)

    def test_permanent_errors_are_logged_and_stop_pending_retries(self):
        for code in (400, 403, 422):
            with self.subTest(code=code), patch(TRANSPORT, side_effect=[
                response(503), HTTPError(URL, code, "rejected", {}, None),
            ]) as transport:
                with at(0):
                    submit_indexnow_urls([URL])
                with at(60), self.assertLogs("catalog.services.indexnow", level="ERROR") as logs:
                    run_cron()
                self.assertIn(str(code), " ".join(logs.output))
                with at(10000):
                    run_cron()
                    self.assertEqual(transport.call_count, 2)


@override_settings(**INDEXNOW_TEST_SETTINGS)
class IndexNowConcurrentDeliveryTests(TransactionTestCase):
    def test_after_commit_worker_hands_transient_failure_to_cron(self):
        with patch(TRANSPORT, side_effect=[response(503), response(202)]) as transport:
            with at(0), ThreadPoolExecutor(1) as pool, patch("catalog.services.indexnow._executor", pool):
                with transaction.atomic():
                    enqueue_indexnow_urls([URL])
                    transport.assert_not_called()
            self.assertEqual(transport.call_count, 1)
            with at(60):
                run_cron()
                self.assertEqual(transport.call_count, 2)
                self.assertEqual(submit_indexnow_urls([URL]).submitted_count, 0)

    def test_overlapping_submissions_share_one_request_even_when_forced(self):
        entered, release = Event(), Event()

        def held_response(*args, **kwargs):
            entered.set()
            if not release.wait(10):
                raise AssertionError("Test did not release the transport")
            return response(200)

        def send():
            try:
                return submit_indexnow_urls([URL])
            finally:
                connections.close_all()

        with patch(TRANSPORT, side_effect=held_response) as transport, ThreadPoolExecutor(1) as pool:
            first = pool.submit(send)
            try:
                self.assertTrue(entered.wait(10))
                self.assertEqual(submit_indexnow_urls([URL]).submitted_count, 0)
                self.assertEqual(submit_indexnow_urls([URL], force=True).submitted_count, 0)
            finally:
                release.set()
            self.assertTrue(first.result(timeout=10).accepted)
            self.assertEqual(transport.call_count, 1)
