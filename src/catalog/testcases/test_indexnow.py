import json
from io import StringIO
from unittest.mock import MagicMock, patch
from urllib.error import URLError

from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings

from catalog.models import CatalogContentSettings, Place
from catalog.services.content_quality import public_place_queryset
from catalog.services.indexnow import (
    IndexNowSubmissionResult,
    canonical_indexnow_url,
    submit_indexnow_urls,
)
from catalog.testcases.utils import create_quality_place


INDEXNOW_TEST_SETTINGS = {
    "INDEXNOW_KEY": "abcd1234-indexnow",
    "INDEXNOW_ENDPOINT": "https://api.indexnow.org/indexnow",
    "INDEXNOW_TIMEOUT_SECONDS": 2.5,
    "INDEXNOW_MIN_INTERVAL_SECONDS": 3600,
}


def submitted_urls_from_mock(mocked_enqueue):
    return [
        url
        for call in mocked_enqueue.call_args_list
        for url in call.args[0]
    ]


@override_settings(**INDEXNOW_TEST_SETTINGS)
class IndexNowClientTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_key_file_is_public_only_for_configured_key(self):
        response = self.client.get("/abcd1234-indexnow.txt")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"abcd1234-indexnow")
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        self.assertEqual(self.client.get("/wrong-key-1234.txt").status_code, 404)

    @override_settings(INDEXNOW_KEY="")
    def test_key_file_is_disabled_without_environment_key(self):
        self.assertEqual(self.client.get("/abcd1234-indexnow.txt").status_code, 404)

    def test_client_posts_only_canonical_public_urls_with_timeout(self):
        response = MagicMock(status=200)
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        urls = [
            "https://kidsmap.az/place/7-example/",
            "https://kidsmap.az/place/7-example/?preview=1",
            "http://kidsmap.az/place/7-example/",
            "https://www.kidsmap.az/place/7-example/",
            "https://kidsmap.az/admin/",
            "https://kidsmap.az/privacy/",
            "https://example.com/place/7/example/",
        ]

        with patch(
            "catalog.services.indexnow.urlopen", return_value=response
        ) as mocked_urlopen:
            result = submit_indexnow_urls(urls)

        self.assertTrue(result.accepted)
        self.assertEqual(result.submitted_count, 1)
        request = mocked_urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(mocked_urlopen.call_args.kwargs["timeout"], 2.5)
        self.assertEqual(payload["host"], "kidsmap.az")
        self.assertEqual(payload["key"], "abcd1234-indexnow")
        self.assertEqual(
            payload["keyLocation"],
            "https://kidsmap.az/abcd1234-indexnow.txt",
        )
        self.assertEqual(
            payload["urlList"], ["https://kidsmap.az/place/7-example/"]
        )

    def test_network_error_is_contained_and_does_not_raise(self):
        with patch(
            "catalog.services.indexnow.urlopen",
            side_effect=URLError("offline"),
        ):
            result = submit_indexnow_urls(
                ["https://kidsmap.az/place/7-example/"], force=True
            )

        self.assertFalse(result.accepted)
        self.assertEqual(result.submitted_count, 1)

    def test_cooldown_suppresses_repeated_submission(self):
        response = MagicMock(status=202)
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        url = "https://kidsmap.az/place/7-example/"

        with patch(
            "catalog.services.indexnow.urlopen", return_value=response
        ) as mocked_urlopen:
            first = submit_indexnow_urls([url])
            second = submit_indexnow_urls([url])

        self.assertTrue(first.accepted)
        self.assertEqual(second.submitted_count, 0)
        self.assertEqual(mocked_urlopen.call_count, 1)

    def test_url_validator_rejects_queries_private_and_noindex_routes(self):
        self.assertEqual(
            canonical_indexnow_url("https://kidsmap.az/ru/place/7-example/"),
            "https://kidsmap.az/ru/place/7-example/",
        )
        for url in (
            "https://kidsmap.az/catalog/?category=EDU",
            "https://kidsmap.az/ru/auth/login/",
            "https://kidsmap.az/admin/",
            "https://kidsmap.az/privacy/",
        ):
            with self.subTest(url=url):
                self.assertEqual(canonical_indexnow_url(url), "")


class IndexNowSignalTests(TestCase):
    def test_new_quality_publication_enqueues_all_language_canonicals(self):
        with override_settings(**INDEXNOW_TEST_SETTINGS), patch(
            "catalog.indexnow_signals.enqueue_indexnow_urls"
        ) as mocked_enqueue, self.captureOnCommitCallbacks(execute=True):
            place = create_quality_place(name="IndexNow new place")

        self.assertTrue(public_place_queryset(Place.objects.filter(pk=place.pk)).exists())
        submitted = submitted_urls_from_mock(mocked_enqueue)
        self.assertIn(
            f"https://kidsmap.az/place/{place.pk}-{place.slug}/", submitted
        )
        self.assertIn(
            f"https://kidsmap.az/ru/place/{place.pk}-{place.slug}/", submitted
        )
        self.assertIn(
            f"https://kidsmap.az/en/place/{place.pk}-{place.slug}/", submitted
        )
        self.assertTrue(all("?" not in url for url in submitted))

    def test_substantial_update_and_unpublish_enqueue_but_like_only_does_not(self):
        with override_settings(INDEXNOW_KEY=""):
            place = create_quality_place(name="IndexNow existing place")

        with override_settings(**INDEXNOW_TEST_SETTINGS), patch(
            "catalog.indexnow_signals.enqueue_indexnow_urls"
        ) as mocked_enqueue:
            with self.captureOnCommitCallbacks(execute=True):
                place.address = "Bakı şəhəri, yeni ünvan 25"
                place.save(update_fields=["address", "updated_at"])
            self.assertTrue(mocked_enqueue.called)

            mocked_enqueue.reset_mock()
            with self.captureOnCommitCallbacks(execute=True):
                place.likes_count += 1
                place.save(update_fields=["likes_count", "updated_at"])
            mocked_enqueue.assert_not_called()

            with self.captureOnCommitCallbacks(execute=True):
                place.status = Place.STATUS_DRAFT
                place.save(update_fields=["status", "updated_at"])
            submitted = submitted_urls_from_mock(mocked_enqueue)
            self.assertIn(
                f"https://kidsmap.az/place/{place.pk}-{place.slug}/", submitted
            )

    def test_catalog_content_save_enqueues_only_indexable_seo_landing(self):
        with override_settings(INDEXNOW_KEY=""):
            for index in range(5):
                create_quality_place(
                    name=f"SEO eligible place {index}", category="EDU"
                )
        content_settings = CatalogContentSettings.get_solo()
        page = {
            "title": "Eligible",
            "meta_description": "Eligible SEO landing",
            "intro": "Eligible SEO landing",
            "benefits": [],
            "catalog_query": "?category=EDU",
            "faq": [],
        }
        content_settings.seo_pages_json = {
            language: {"eligible-seo": page} for language in ("az", "ru", "en")
        }

        with override_settings(**INDEXNOW_TEST_SETTINGS), patch(
            "catalog.indexnow_signals.enqueue_indexnow_urls"
        ) as mocked_enqueue, self.captureOnCommitCallbacks(execute=True):
            content_settings.save(update_fields=["seo_pages_json", "updated_at"])

        submitted = submitted_urls_from_mock(mocked_enqueue)
        self.assertEqual(
            set(submitted),
            {
                "https://kidsmap.az/catalog/eligible-seo/",
                "https://kidsmap.az/ru/catalog/eligible-seo/",
                "https://kidsmap.az/en/catalog/eligible-seo/",
            },
        )


@override_settings(**INDEXNOW_TEST_SETTINGS)
class SubmitIndexNowCommandTests(TestCase):
    def setUp(self):
        cache.clear()
        with override_settings(INDEXNOW_KEY=""):
            self.place = create_quality_place(name="Manual IndexNow place")

    def test_dry_run_never_calls_external_client(self):
        output = StringIO()
        with patch(
            "catalog.management.commands.submit_indexnow.submit_indexnow_urls"
        ) as mocked_submit:
            call_command("submit_indexnow", "--dry-run", stdout=output)

        mocked_submit.assert_not_called()
        self.assertIn("Dry run complete", output.getvalue())

    def test_limited_manual_batch_uses_mocked_client(self):
        output = StringIO()
        result = IndexNowSubmissionResult(
            submitted_count=1,
            status_code=200,
            accepted=True,
        )
        with patch(
            "catalog.management.commands.submit_indexnow.submit_indexnow_urls",
            return_value=result,
        ) as mocked_submit:
            call_command("submit_indexnow", "--limit", "1", "--force", stdout=output)

        submitted_urls = mocked_submit.call_args.args[0]
        self.assertEqual(len(submitted_urls), 1)
        self.assertTrue(submitted_urls[0].startswith("https://kidsmap.az/"))
        self.assertNotIn("?", submitted_urls[0])
