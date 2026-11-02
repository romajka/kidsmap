"""Opt-in atomicity checks against a separately provisioned disposable Unix socket.

Set KIDSMAP_AUTH_TEST_REDIS_SOCKET to an isolated socket under repository .tmp.
No flush, network Redis, credentials or shared production cache are used.
"""
import os
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.cache.backends.redis import RedisCache
from django.test import SimpleTestCase

from catalog.services.auth_throttle import _increment


@unittest.skipUnless(os.environ.get('KIDSMAP_AUTH_TEST_REDIS_SOCKET'), 'isolated Redis socket not supplied')
class AuthThrottleRedisTests(SimpleTestCase):
    def setUp(self):
        socket = Path(os.environ['KIDSMAP_AUTH_TEST_REDIS_SOCKET']).resolve()
        if not socket.is_relative_to((settings.BASE_DIR / '.tmp').resolve()) or not socket.is_socket():
            raise ValueError('An isolated Redis Unix socket under repository .tmp is required')
        self.backend = RedisCache(f'unix://{socket}?db=0', {'KEY_PREFIX': 'auth-test-' + uuid4().hex})
        self.key = 'counter'
        self.raw = self.backend._cache.get_client(write=True)
        self.physical_key = self.backend.make_key(self.key)
        self.addCleanup(self.raw.delete, self.physical_key)

    def test_concurrent_increments_are_lossless_and_expire(self):
        with ThreadPoolExecutor(max_workers=24) as executor:
            values = list(executor.map(lambda _: _increment(self.backend, self.key, 60), range(240)))
        self.assertEqual(sorted(values), list(range(1, 241)))
        self.assertGreater(self.raw.ttl(self.physical_key), 0)
        self.assertLessEqual(self.raw.ttl(self.physical_key), 60)

    def test_rejected_traffic_does_not_extend_ttl_and_expired_counter_restarts(self):
        self.assertEqual(_increment(self.backend, self.key, 1), 1)
        before = self.raw.pttl(self.physical_key)
        time.sleep(0.05)
        self.assertEqual(_increment(self.backend, self.key, 60), 2)
        self.assertLess(self.raw.pttl(self.physical_key), before)
        time.sleep(1.05)
        self.assertEqual(_increment(self.backend, self.key, 60), 1)
        self.assertGreater(self.raw.ttl(self.physical_key), 0)

    def test_counter_without_expiry_is_repaired(self):
        self.raw.set(self.physical_key, 8)
        self.assertEqual(_increment(self.backend, self.key, 60), 9)
        self.assertGreater(self.raw.ttl(self.physical_key), 0)
