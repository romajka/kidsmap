import unittest

from django.test.runner import DiscoverRunner


class CompactTextTestResult(unittest.TextTestResult):
    """Keep failed HTML assertions useful without dumping whole responses."""

    max_failure_chars = 8_000

    def _exc_info_to_string(self, err, test):
        rendered = super()._exc_info_to_string(err, test)
        if len(rendered) <= self.max_failure_chars:
            return rendered
        omitted = len(rendered) - self.max_failure_chars
        return (
            rendered[: self.max_failure_chars]
            + f"\n... [failure output truncated; {omitted} characters omitted]\n"
        )


class CompactTextTestRunner(unittest.TextTestRunner):
    resultclass = CompactTextTestResult


class KidsMapTestRunner(DiscoverRunner):
    test_runner = CompactTextTestRunner
