"""Canonical test-suite manifest for the catalog application.

The testcase files intentionally do not follow unittest's ``test*.py`` naming
pattern. Keeping the manifest here makes ``manage.py test`` complete without
re-exporting imported TestCase classes (which used to run some tests twice).
"""

TEST_MODULES = (
    "catalog.testcases.adult_classes",
    "catalog.testcases.admin",
    "catalog.testcases.auth_access",
    "catalog.testcases.auth_flow",
    "catalog.testcases.catalog",
    "catalog.testcases.events_feature",
    "catalog.testcases.images",
    "catalog.testcases.owner",
    "catalog.testcases.place_filepond_admin",
    "catalog.testcases.place_taxonomy_admin",
    "catalog.testcases.pricing_plans",
    "catalog.testcases.public",
    "catalog.testcases.specialists",
    "catalog.testcases.tracking",
)


def load_tests(loader, standard_tests, pattern):
    suite = loader.suiteClass()
    for module_name in TEST_MODULES:
        suite.addTests(loader.loadTestsFromName(module_name))
    return suite
