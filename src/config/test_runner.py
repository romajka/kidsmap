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
import os
import time
import json
import ast
import inspect
from collections import Counter
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings
from django.test.runner import (
    DiscoverRunner, ParallelTestSuite, RemoteTestResult, RemoteTestRunner,
    iter_test_cases, partition_suite_by_case,
)
from django.utils import translation


def _reset_global_state() -> None:
    cache.clear()
    translation.activate(settings.LANGUAGE_CODE)


class _QualityTimingMixin:
    """Record real worker time, including each test's setup and teardown."""

    quality_remote_replay = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quality_records = []
        self._quality_active = None

    def startTest(self, test):
        _reset_global_state()
        if not self.quality_remote_replay:
            self._quality_active = (test, time.perf_counter(), 'success')
        super().startTest(test)

    def _quality_outcome(self, test, outcome):
        if self._quality_active is not None and self._quality_active[0] is test:
            case, started, previous = self._quality_active
            # An error must not be hidden by a later failed subtest/teardown.
            self._quality_active = (case, started, previous if previous == 'error' else outcome)

    def addFailure(self, test, err):
        self._quality_outcome(test, 'failure')
        super().addFailure(test, err)

    def addError(self, test, err):
        self._quality_outcome(test, 'error')
        super().addError(test, err)

    def addSubTest(self, test, subtest, err):
        if err is not None:
            self._quality_outcome(test, 'failure' if issubclass(err[0], test.failureException) else 'error')
        super().addSubTest(test, subtest, err)

    def addSkip(self, test, reason):
        self._quality_outcome(test, 'skip')
        super().addSkip(test, reason)

    def addExpectedFailure(self, test, err):
        self._quality_outcome(test, 'expected_failure')
        super().addExpectedFailure(test, err)

    def addUnexpectedSuccess(self, test):
        self._quality_outcome(test, 'unexpected_success')
        super().addUnexpectedSuccess(test)

    def stopTest(self, test):
        if self._quality_active is not None:
            case, started, outcome = self._quality_active
            self._quality_active = None
            self._store_quality_timing(test, {
                'test_id': case.id(), 'elapsed_seconds': time.perf_counter() - started,
                'outcome': outcome, 'worker_id': os.getpid(),
            })
        super().stopTest(test)

    def _store_quality_timing(self, test, record):
        self.quality_records.append(record)

    def recordQualityTiming(self, test, record):
        if record['test_id'] != test.id() or record['elapsed_seconds'] < 0:
            raise ValueError('Invalid worker timing record')
        self.quality_records.append(record)


def _with_state_reset(result_class, remote_replay=False):
    class StateResetResult(_QualityTimingMixin, result_class):
        quality_remote_replay = remote_replay

    StateResetResult.__name__ = f"StateReset{result_class.__name__}"
    return StateResetResult


class StateResetRemoteTestResult(_QualityTimingMixin, RemoteTestResult):
    """Reset worker-local state before every test in a parallel run."""

    def _store_quality_timing(self, test, record):
        self.events.append(('recordQualityTiming', self.test_index, record))


class StateResetRemoteTestRunner(RemoteTestRunner):
    resultclass = StateResetRemoteTestResult

    def run(self, test):
        _prepare_worker_storage()
        return super().run(test)


_worker_storage = None


def _prepare_worker_storage():
    """Separate shared upload paths before a worker's first setUpClass."""
    global _worker_storage
    root = getattr(settings, 'QA_ROOT', None)
    if root is not None and _worker_storage is None:
        directory = Path(root)/'workers'/str(os.getpid())
        _worker_storage = override_settings(
            MEDIA_ROOT=directory/'media', PRIVATE_MEDIA_ROOT=directory/'private-media',
            PRIVATE_DRAFT_MEDIA_ROOT=directory/'private-drafts',
        )
        _worker_storage.enable()


class KidsMapParallelTestSuite(ParallelTestSuite):
    runner_class = StateResetRemoteTestRunner


SERIAL_QUALITY_MODULES = frozenset({
    'test_phone_migration', 'test_place_release_schema_compatibility',
    'test_project_fixes_release', 'test_task33_catalog_schema',
    'test_task33_completion_taxonomy_migration', 'test_task33_conversion',
    'test_task33_event_schema', 'test_task33_notification_crashes',
    'test_task33_r1_acceptance', 'test_task33_review_migration',
    'test_task33_specialist_db_review', 'test_task33_specialist_transfer',
})


@lru_cache(maxsize=None)
def _source_requires_serial(filename):
    """Recognize future direct QA guards too; unavailable source fails closed."""
    try:
        tree = ast.parse(Path(filename).read_text(encoding='utf-8'))
    except (OSError, SyntaxError, TypeError, UnicodeError):
        return True
    names = {'MigrationExecutor', '_require_isolated_database', 'require_disposable_postgres'}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)) and any(alias.name in names for alias in node.names):
            return True
        if isinstance(node, ast.Import) and any(
                alias.name.removeprefix('src.') in {'guard', 'catalog.services.catalog_conversion'}
                for alias in node.names):
            return True
        if isinstance(node, ast.Name) and node.id in names:
            return True
        if isinstance(node, ast.Attribute) and node.attr in names:
            return True
        if isinstance(node, ast.ImportFrom):
            if node.module in {'guard', 'catalog.services.catalog_conversion'}:
                return True
            if node.module == 'catalog.services' and any(n.name == 'catalog_conversion' for n in node.names):
                return True
    return False


def _requires_serial(test):
    if getattr(test, 'quality_serial', False) or 'quality_serial' in getattr(test, 'tags', ()):
        return True
    if isinstance(test, TransactionTestCase) and not isinstance(test, TestCase):
        return True
    if not isinstance(test, SimpleTestCase):
        return True
    module = type(test).__module__.removeprefix('src.')
    if module.startswith('catalog.testcases.') and module.rsplit('.', 1)[-1] in SERIAL_QUALITY_MODULES:
        return True
    try:
        filename = inspect.getsourcefile(type(test))
    except TypeError:
        return True
    return not filename or _source_requires_serial(filename)


def split_quality_suite(suite):
    """Partition one canonical collection; never rediscover or discard a case."""
    cases = list(iter_test_cases(suite))
    counts = Counter(test.id() for test in cases)
    if any(count != 1 for count in counts.values()):
        raise ValueError('Duplicate test IDs in canonical quality collection')
    parallel, serial = [], []
    for test in cases:
        (serial if _requires_serial(test) else parallel).append(test)
    if Counter(t.id() for t in parallel + serial) != counts:
        raise ValueError('Quality partition lost or duplicated tests')
    return unittest.TestSuite(parallel), unittest.TestSuite(serial)


class KidsMapTestRunner(DiscoverRunner):
    parallel_test_suite = KidsMapParallelTestSuite

    def __init__(self, *args, timing_json=None, quality_lane=None, quality_cases=None, **kwargs):
        super().__init__(*args, **kwargs)
        if quality_lane not in (None, 'serial', 'parallel'):
            raise ValueError('Unknown quality lane')
        self.quality_lane = quality_lane
        self.quality_cases = quality_cases
        self.timing_json = Path(timing_json) if timing_json else None
        self.quality_phases = {}
        self.quality_result = None
        self.quality_ids = []

    @classmethod
    def add_arguments(cls, parser):
        super().add_arguments(parser)
        parser.add_argument('--timing-json', help='Write per-test worker timings and coverage to JSON')
        parser.add_argument('--quality-lane', choices=['serial', 'parallel'],
                            help='Internal lossless quality partition; use run_isolated_quality.py for the complete gate')

    def run_tests(self, test_labels, **kwargs):
        started = time.perf_counter()
        failures = None
        try:
            failures = super().run_tests(test_labels, **kwargs)
            return failures
        finally:
            self.quality_phases['total_seconds'] = time.perf_counter() - started
            if self.timing_json:
                records = getattr(self.quality_result, 'quality_records', [])
                expected = Counter(self.quality_ids)
                actual = Counter(r['test_id'] for r in records)
                complete = bool(self.quality_result is not None and expected == actual
                                and all(count == 1 for count in expected.values()))
                result = self.quality_result
                report = {
                    'schema_version': 1, 'phases': self.quality_phases,
                    'planned_ids': self.quality_ids, 'records': records,
                    'complete': complete, 'successful': failures == 0 and complete,
                    'tests_run': result.testsRun if result else 0,
                    'failures': len(result.failures) if result else 0,
                    'errors': len(result.errors) if result else 0,
                    'skipped': len(result.skipped) if result else 0,
                    'missing_ids': sorted((expected - actual).elements()),
                    'extra_ids': sorted((actual - expected).elements()),
                }
                self.timing_json.parent.mkdir(parents=True, exist_ok=True)
                temporary = self.timing_json.with_suffix('.tmp')
                temporary.write_text(json.dumps(report, indent=2) + '\n')
                temporary.replace(self.timing_json)
                if failures == 0 and not complete:
                    raise RuntimeError('Quality timing coverage is incomplete or duplicated')

    def setup_databases(self, **kwargs):
        started = time.perf_counter()
        try:
            return super().setup_databases(**kwargs)
        finally:
            self.quality_phases['database_setup_seconds'] = time.perf_counter() - started

    def teardown_databases(self, old_config, **kwargs):
        started = time.perf_counter()
        try:
            return super().teardown_databases(old_config, **kwargs)
        finally:
            self.quality_phases['database_teardown_seconds'] = time.perf_counter() - started

    def run_suite(self, suite, **kwargs):
        started = time.perf_counter()
        try:
            self.quality_result = super().run_suite(suite, **kwargs)
            return self.quality_result
        finally:
            self.quality_phases['execution_seconds'] = time.perf_counter() - started

    def run_checks(self, databases):
        started = time.perf_counter()
        try:
            return super().run_checks(databases)
        finally:
            self.quality_phases['checks_seconds'] = time.perf_counter() - started

    def build_suite(self, test_labels=None, **kwargs):
        started = time.perf_counter()
        if self.quality_cases is not None:
            suite = self.test_suite(self.quality_cases)
        elif not test_labels:
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
        if self.quality_cases is None:
            processes = self.parallel
            self.parallel = 1
            try:
                suite = super().build_suite(test_labels, **kwargs)
            finally:
                self.parallel = processes
        if self.quality_lane:
            parallel, serial = split_quality_suite(suite)
            suite = parallel if self.quality_lane == 'parallel' else serial
        elif self.parallel > 1:
            _, serial = split_quality_suite(suite)
            if serial.countTestCases():
                raise ValueError('Guarded tests require the split isolated quality gate, not --parallel alone')
        self.quality_ids = [test.id() for test in iter_test_cases(suite)]
        if self.parallel > 1:
            subsuites = partition_suite_by_case(suite)
            self.parallel = min(self.parallel, len(subsuites))
            if self.parallel > 1:
                suite = self.parallel_test_suite(subsuites, self.parallel, self.failfast,
                                                 self.debug_mode, self.buffer)
        self.quality_phases['collection_seconds'] = time.perf_counter() - started
        return suite

    def get_resultclass(self):
        # Django returns None when it has no special result class of its own,
        # in which case unittest falls back to TextTestResult.
        return _with_state_reset(super().get_resultclass() or unittest.TextTestResult,
                                 remote_replay=self.parallel > 1)
