"""Test runner that resets process-global state between tests.

`TestCase` rolls back the database after every test, but two other pieces of
state survive and make results depend on execution order:

* **The cache.** Under `DJANGO_TESTING=1` the backend is a locmem instance
  shared by the whole process, so whatever a test leaves behind — a tracking
  rate-limit counter, an IndexNow dedupe marker — is still there for the next
  one.
* **The active language.** `LocaleMiddleware` activates a language per request
  and never restores it, so one client call to a `/ru/` URL leaves every later
  test running in Russian. Code that formats text outside a request then
  produces the wrong language.

Both are reset as each test starts, so every test begins from the same state no
matter what ran before it.
"""

import unittest
import pkgutil

from django.conf import settings
from django.core.cache import cache
from django.test.runner import DiscoverRunner, ParallelTestSuite, RemoteTestResult, RemoteTestRunner
from django.utils import translation


def _reset_global_state() -> None:
    cache.clear()
    translation.activate(settings.LANGUAGE_CODE)


def _with_state_reset(result_class):
    class StateResetResult(result_class):
        def startTest(self, test):
            _reset_global_state()
            super().startTest(test)

    StateResetResult.__name__ = f"StateReset{result_class.__name__}"
    return StateResetResult


class StateResetRemoteTestResult(RemoteTestResult):
    """Reset worker-local state before every test in a parallel run."""

    def startTest(self, test):
        _reset_global_state()
        super().startTest(test)


class StateResetRemoteTestRunner(RemoteTestRunner):
    resultclass = StateResetRemoteTestResult


class KidsMapParallelTestSuite(ParallelTestSuite):
    runner_class = StateResetRemoteTestRunner


class KidsMapTestRunner(DiscoverRunner):
    parallel_test_suite = KidsMapParallelTestSuite

    def build_suite(self, test_labels=None, **kwargs):
        if not test_labels:
            # src/ is not traversed by repository-root unittest discovery.
            # Discover the domain package and legacy non-test-prefixed suites
            # automatically so new modules cannot silently miss the CI gate.
            from catalog import testcases

            test_labels = ["catalog.testcases"]
            if self.pattern in (None, "test*.py"):
                test_labels += [
                    f"catalog.testcases.{module.name}"
                    for module in sorted(pkgutil.iter_modules(testcases.__path__), key=lambda item: item.name)
                    if not module.ispkg and not module.name.startswith("test")
                ]
        return super().build_suite(test_labels, **kwargs)

    def get_resultclass(self):
        # Django returns None when it has no special result class of its own,
        # in which case unittest falls back to TextTestResult.
        return _with_state_reset(super().get_resultclass() or unittest.TextTestResult)
