"""Exact targeted test IDs; no claim of full project discovery."""
import json, unittest
from pathlib import Path
LABELS=[
    'catalog.testcases.test_org_qa01_autosave_base',
    'catalog.testcases.test_task33_organization_workspace',
    'catalog.testcases.test_task33_drafts',
    'catalog.testcases.test_organization_editor_errors',
    'catalog.testcases.test_task33_publication.PublicationTests.test_schema_and_source_conflicts_do_not_write',
    'catalog.testcases.test_task33_publication.PublicationTests.test_approval_changes_only_patch_and_uses_new_version',
]
def flatten(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from flatten(test)
        else:
            yield test.id()
ids=list(flatten(unittest.defaultTestLoader.loadTestsFromNames(LABELS)))
assert len(ids)==44 and len(set(ids))==44 and not any('_FailedTest' in value for value in ids)
Path(__file__).with_name('targeted-discovery.json').write_text(json.dumps({'count':len(ids),'labels':LABELS,'ids':ids},indent=2))
print('44 unique targeted test IDs discovered; full project discovery NOT RUN')
