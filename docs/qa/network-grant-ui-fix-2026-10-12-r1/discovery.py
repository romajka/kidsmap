import json,unittest
from pathlib import Path
LABELS=['catalog.testcases.test_network_grant_ui', 'catalog.testcases.test_organization_invitation_transport', 'catalog.testcases.test_organization_invitation_result', 'catalog.testcases.test_org_qa01_autosave_base', 'catalog.testcases.test_task33_permissions.GrantTests.test_revocation_and_leave_immediately_remove_cached_account_access', 'catalog.testcases.test_task33_permissions.GrantTests.test_endpoint_denies_foreign_nested_ids_and_manager_team_post', 'catalog.testcases.test_task33_permissions.GrantTests.test_invitation_grant_version_and_replay_are_checked', 'catalog.testcases.test_task33_permissions.GrantTests.test_endpoint_transport_csrf_config_and_conflict']
def ids(suite):
 for t in suite:
  if isinstance(t,unittest.TestSuite):yield from ids(t)
  else:yield t.id()
result=list(ids(unittest.defaultTestLoader.loadTestsFromNames(LABELS)))
assert len(result)==28 and len(set(result))==28 and not any('_FailedTest' in x for x in result)
Path(__file__).with_name('discovery.json').write_text(json.dumps({'count':28,'ids':result,'labels':LABELS},indent=2))
print('28 unique targeted test IDs; full project discovery NOT RUN')
