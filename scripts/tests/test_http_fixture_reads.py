"""Memoized fixture reads must preserve real routes, errors and cookie changes."""
from collections import Counter
import unittest

import quality_test_support  # noqa: F401
from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings
from django.urls import path
from catalog.testcases.http_fixtures import ReadOnlyFixtureClient

reads = Counter()


def rendered(request, key):
    cookie = request.COOKIES.get('fixture', '')
    reads[(key, cookie)] += 1
    return HttpResponse(f'{key}:{cookie}:{reads[(key, cookie)]}', status=404 if key == 'missing' else 200)


urlpatterns = [path('read/<slug:key>/', rendered)]


@override_settings(ROOT_URLCONF=__name__, MIDDLEWARE=[])
class FixtureReadTests(SimpleTestCase):
    def setUp(self):
        reads.clear()

    def test_repeated_reads_render_each_distinct_path_once_including_404(self):
        client = ReadOnlyFixtureClient()
        for name, status in [('one', 200), ('missing', 404), ('two', 200)]:
            for _ in range(3):
                response = client.get('/read/'+name+'/')
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.content.decode(), f'{name}::1')
        self.assertEqual(dict(reads), {('one', ''): 1, ('missing', ''): 1, ('two', ''): 1})

    def test_cookie_changes_and_separate_clients_never_reuse_wrong_response(self):
        client = ReadOnlyFixtureClient()
        client.cookies['fixture'] = 'first'
        self.assertEqual(client.get('/read/one/').content, b'one:first:1')
        client.cookies['fixture'] = 'second'
        self.assertEqual(client.get('/read/one/').content, b'one:second:1')
        other = ReadOnlyFixtureClient()
        other.cookies['fixture'] = 'second'
        self.assertEqual(other.get('/read/one/').content, b'one:second:2')

    def test_writes_are_rejected_instead_of_leaving_stale_cached_reads(self):
        with self.assertRaises(ValueError):
            ReadOnlyFixtureClient().post('/read/one/', {'new': 'data'})


if __name__ == '__main__':
    unittest.main()
