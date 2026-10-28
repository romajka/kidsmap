"""Synthetic cases exercised by the gate's subprocess integration test."""
from django.test import SimpleTestCase


class WorkerPass(SimpleTestCase):
    def test_01_worker_state_starts_clean(self):
        import os
        from pathlib import Path
        from django.conf import settings
        from django.core.cache import cache
        from django.utils import translation
        self.assertEqual(Path(settings.MEDIA_ROOT), settings.QA_ROOT/'workers'/str(os.getpid())/'media')
        self.assertIsNone(cache.get('quality-worker-sentinel'))
        self.assertEqual(translation.get_language(), 'az')
        cache.set('quality-worker-sentinel', True)
        translation.activate('ru')

    def test_02_next_test_resets_worker_state(self):
        from django.core.cache import cache
        from django.utils import translation
        self.assertIsNone(cache.get('quality-worker-sentinel'))
        self.assertEqual(translation.get_language(), 'az')


class OtherWorkerPass(SimpleTestCase):
    def test_success(self):
        pass


class WorkerFailure(SimpleTestCase):
    def test_failure(self):
        self.fail('synthetic worker assertion')


class ClassSetupFailure(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        raise RuntimeError('synthetic class setup error')

    def test_unreachable(self):
        raise AssertionError('must never run')


class SerialPass(SimpleTestCase):
    quality_serial = True

    def test_success(self):
        pass


class SerialFailure(SimpleTestCase):
    quality_serial = True

    def test_failure(self):
        self.fail('synthetic serial assertion')
