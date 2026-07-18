"""Intentional failure used only to exercise Django's parallel error path."""

from django.test import TestCase


class ParallelFailureProbe(TestCase):
    def test_failure_can_cross_process_boundary(self):
        self.fail("intentional parallel-runner probe")


class ParallelWorkerProbe(TestCase):
    def test_second_worker_partition(self):
        self.assertTrue(True)
