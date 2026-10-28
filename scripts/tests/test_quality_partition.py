"""The optimization must never drop cases or send guarded work to clones."""
import unittest
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import quality_test_support  # noqa: F401
from django.test import SimpleTestCase, TestCase, TransactionTestCase
from config import test_runner as quality


class QualityPartitionTests(unittest.TestCase):
    def cases(self):
        class Ordinary(TestCase):
            def runTest(self):
                pass

        class Pure(SimpleTestCase):
            def runTest(self):
                pass

        class Committed(TransactionTestCase):
            def runTest(self):
                pass

        class Guarded(TestCase):
            __module__ = 'catalog.testcases.test_task33_conversion'

            def runTest(self):
                pass

        class Explicit(TestCase):
            quality_serial = True

            def runTest(self):
                pass

        return [Ordinary(), Pure(), Committed(), Guarded(), Explicit()]

    def test_only_ordinary_and_pure_cases_use_workers(self):
        partition = getattr(quality, 'split_quality_suite', None)
        self.assertTrue(callable(partition), 'Quality runner needs a lossless serial/parallel partition')
        cases = self.cases()
        parallel, serial = partition(unittest.TestSuite(cases))
        self.assertEqual(list(parallel), cases[:2])
        self.assertEqual(list(serial), cases[2:])

    def test_duplicate_ids_are_rejected_before_execution(self):
        partition = getattr(quality, 'split_quality_suite', None)
        self.assertTrue(callable(partition), 'Missing partition validation')
        case = self.cases()[0]
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            partition(unittest.TestSuite([case, case]))

    def test_nested_suites_preserve_order_and_all_ids(self):
        partition = getattr(quality, 'split_quality_suite', None)
        self.assertTrue(callable(partition), 'Missing partition validation')
        cases = self.cases()
        parallel, serial = partition(unittest.TestSuite([
            unittest.TestSuite(cases[:1]), unittest.TestSuite(cases[1:]),
        ]))
        self.assertEqual([t.id() for t in parallel], [cases[0].id(), cases[1].id()])
        self.assertEqual([t.id() for t in serial], [t.id() for t in cases[2:]])

    def test_unknown_test_types_are_serial(self):
        partition = getattr(quality, 'split_quality_suite', None)
        self.assertTrue(callable(partition), 'Unknown test types must fail closed')
        case = unittest.FunctionTestCase(lambda: None)
        parallel, serial = partition(unittest.TestSuite([case]))
        self.assertEqual(list(parallel), [])
        self.assertEqual(list(serial), [case])

    def test_new_aliased_guard_and_migration_imports_fail_closed(self):
        samples = [
            'import guard as qa_guard',
            'import catalog.services.catalog_conversion as conversion',
            'from django.db.migrations.executor import MigrationExecutor as executor',
            'from guard import socket_path as isolated_socket',
        ]
        for source in samples:
            with self.subTest(source=source), tempfile.TemporaryDirectory() as temporary:
                filename = Path(temporary)/'future_guarded_case.py'
                filename.write_text(source+'\n')
                self.assertTrue(quality._source_requires_serial(str(filename)))


class QualityGateIntegrationTests(unittest.TestCase):
    def test_actual_workers_and_serial_lane_preserve_ids_and_failure_exit(self):
        helper = Path(__file__).with_name('quality_fixture_gate.py')
        for failure, expected_exit in [('none', 0), ('parallel', 1), ('serial', 1), ('class_setup', 1)]:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temporary:
                completed = subprocess.run(
                    [sys.executable, str(helper), temporary, failure],
                    capture_output=True, text=True, timeout=45,
                )
                self.assertEqual(completed.returncode, expected_exit, completed.stdout + completed.stderr)
                self.assertTrue((Path(temporary)/'timing.json').is_file(), 'Gate must report failed and incomplete lanes')
                report = json.loads((Path(temporary)/'timing.json').read_text())
                self.assertEqual(report['successful'], failure == 'none')
                if failure == 'none':
                    self.assertEqual(report['tests_run'], 4)
                    self.assertEqual(len(report['records']), 4)
                    self.assertTrue(report['complete'])
                    workers = {r['worker_id'] for r in report['lanes'][0]['records']}
                    self.assertTrue(workers)
                    self.assertEqual(report['lanes'][0]['workers'], 2)
                    self.assertNotIn(report['lanes'][1]['records'][0]['worker_id'], workers)
                elif failure in ('parallel', 'class_setup'):
                    self.assertEqual(len(report['lanes']), 1)
                    self.assertFalse(report['complete'])
                    self.assertIn('synthetic worker assertion' if failure == 'parallel'
                                  else 'synthetic class setup error', completed.stderr)
                else:
                    self.assertEqual(len(report['lanes']), 2)
                    self.assertIn('synthetic serial assertion', completed.stderr)

    def test_empty_selection_cannot_be_reported_as_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            completed = subprocess.run(
                [sys.executable, str(Path(__file__).with_name('quality_fixture_gate.py')), temporary, 'empty'],
                capture_output=True, text=True, timeout=15,
            )
            self.assertNotEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == '__main__':
    unittest.main()
