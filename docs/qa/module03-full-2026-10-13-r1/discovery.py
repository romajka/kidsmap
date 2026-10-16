"""Explicit module03 discovery, including non-prefixed domain suites."""
import json,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
names=['test_specialist_proposal_drafts','test_specialist_entry_locations','test_specialist_entry_admin','test_specialist_identity_date_label','test_task33_specialist_workspace','test_task33_specialist_screens_security','test_task33_specialist_privacy','test_task33_specialist_domain','test_task33_specialist_security_review','test_task33_specialist_screens','test_task33_specialist_transfer','test_task33_specialist_retention','test_task33_specialist_db_review','specialists','test_spec_qa01_document_validation','test_spec_qa02_photo_conflict']
labels=['catalog.testcases.'+x for x in names]
loader=unittest.TestLoader();suite=loader.loadTestsFromNames(labels)
def flatten(s):
 for test in s:
  if isinstance(test,unittest.TestSuite):yield from flatten(test)
  else:yield test.id()
ids=list(flatten(suite));assert not loader.errors,loader.errors;assert len(ids)==len(set(ids))
(P/'discovery.json').write_text(json.dumps({'labels':labels,'ids':ids,'unique_tests':len(ids),'no_label_wrapper_not_used':True},indent=2))
(P/'test-labels.json').write_text(json.dumps(labels,indent=2));print('Explicit unique module03 tests:',len(ids))
