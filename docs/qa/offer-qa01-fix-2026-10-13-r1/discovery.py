import json
from pathlib import Path
from django.test.runner import DiscoverRunner
labels=['catalog.testcases.test_offer_qa01_group_removal','catalog.testcases.test_task33_pricing.GroupPricingTests','catalog.testcases.test_task33_completion_taxonomy','catalog.testcases.test_task33_program_workspace']
def flatten(suite):
 for test in suite:
  if hasattr(test,'id'):yield test.id()
  else:yield from flatten(test)
ids=list(flatten(DiscoverRunner(verbosity=0).build_suite(labels)))
p=Path(__file__).resolve().parent
(p/'test-discovery.json').write_text(json.dumps({'labels':labels,'ids':ids,'count':len(ids),'unique':len(set(ids))},indent=2))
print(json.dumps({'count':len(ids),'unique':len(set(ids))}))
