"""Timing must retain failures, setup/teardown costs and worker measurements."""
import io
import os
import time
import unittest

import quality_test_support  # noqa: F401
from config import test_runner as quality


class QualityTimingTests(unittest.TestCase):
    def run_cases(self, cases):
        result = quality._with_state_reset(unittest.TextTestResult)(io.StringIO(), True, 0)
        unittest.TestSuite(cases).run(result)
        return result

    def test_records_setup_body_teardown_and_all_failure_outcomes(self):
        class Cases(unittest.TestCase):
            def setUp(self):
                time.sleep(.005)
                if self._testMethodName == 'setup_error':
                    raise ValueError('synthetic setup error')

            def tearDown(self):
                time.sleep(.005)

            def success(self):
                pass

            def failure(self):
                self.fail('synthetic assertion')

            def error(self):
                raise ValueError('synthetic error')

            def setup_error(self):
                pass

            def subtest_failure(self):
                with self.subTest(value=1):
                    self.assertEqual(1, 2)

            @unittest.skip('synthetic skip')
            def skipped(self):
                pass

            @unittest.expectedFailure
            def expected_failure(self):
                self.fail('expected')

            @unittest.expectedFailure
            def unexpected_success(self):
                pass

        names = ['success', 'failure', 'error', 'setup_error', 'subtest_failure',
                 'skipped', 'expected_failure', 'unexpected_success']
        result = self.run_cases([Cases(name) for name in names])
        records = getattr(result, 'quality_records', [])
        self.assertEqual(len(records), 8)
        self.assertEqual([r['outcome'] for r in records],
                         ['success', 'failure', 'error', 'error', 'failure',
                          'skip', 'expected_failure', 'unexpected_success'])
        self.assertGreaterEqual(records[0]['elapsed_seconds'], .009)
        self.assertTrue(all(r['worker_id'] == os.getpid() for r in records))
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(len(result.failures), 2)
        self.assertEqual(len(result.errors), 2)

    def test_worker_timing_is_replayed_once_with_original_pid_and_duration(self):
        case = unittest.FunctionTestCase(lambda: None)
        remote = quality.StateResetRemoteTestResult()
        case.run(remote)
        events = [event for event in remote.events if event[0] == 'recordQualityTiming']
        self.assertEqual(len(events), 1)
        result_class = quality._with_state_reset(unittest.TextTestResult, remote_replay=True)
        result = result_class(io.StringIO(), True, 0)
        for event in remote.events:
            handler = getattr(result, event[0], None)
            if handler:
                handler(case, *event[2:])
        self.assertEqual(result.quality_records, [events[0][2]])
        self.assertTrue(result.wasSuccessful())


if __name__ == '__main__':
    unittest.main()
