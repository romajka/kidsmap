import os
import runpy
from unittest import TestCase
from unittest.mock import patch

from sentry_sdk.integrations.django import DjangoIntegration


class SentrySettingsTests(TestCase):
    def settings(self, **env):
        with patch.dict(os.environ, {"DJANGO_TESTING": "1", **env}, clear=True):
            with patch("sentry_sdk.init") as initialize:
                runpy.run_module("config.settings", run_name="config._isolated_settings")
        return initialize

    def test_empty_dsn_does_not_initialize_or_read_sampling_rate(self):
        self.settings(SENTRY_DSN=" ", SENTRY_TRACES_SAMPLE_RATE="unused").assert_not_called()

    def test_dsn_enables_django_with_explicit_privacy_and_sampling(self):
        dsn = "https://test@example.invalid/1"
        for env, rate in (({}, 0.1), ({"SENTRY_TRACES_SAMPLE_RATE": "0"}, 0.0),
                          ({"SENTRY_TRACES_SAMPLE_RATE": "0.35"}, 0.35)):
            with self.subTest(rate=rate):
                initialize = self.settings(SENTRY_DSN=dsn, **env)
                initialize.assert_called_once()
                options = initialize.call_args.kwargs
                self.assertEqual(options["dsn"], dsn)
                self.assertIs(options["send_default_pii"], False)
                self.assertEqual(options["traces_sample_rate"], rate)
                self.assertTrue(any(isinstance(i, DjangoIntegration) for i in options["integrations"]))
