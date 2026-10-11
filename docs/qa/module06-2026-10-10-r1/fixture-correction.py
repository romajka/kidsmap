"""Finish initial public fixture setup; no audited publication transitions."""
import sys,json
sys.argv=['run.py','fixture-initial'];from run import *
from catalog.models import Place
from catalog.services import organization_ownership
from django.contrib.auth import get_user_model
f=json.loads((HERE/'fixtures.json').read_text())
assert not (HERE/'fixture-correction.json').exists()
organization_ownership.request_join(actor=get_user_model().objects.get(username='qa_owner'),place_id=f['places']['Aurora'],organization_id=f['organization'])
for key,pk in f['places'].items():
 if key.startswith('Page') or key=='LongFallback':
  district='baku_yasamal' if key=='LongFallback' or int(key[4:])%2==0 else 'baku_narimanov'
  Place.objects.filter(pk=pk).update(district=district)
(HERE/'fixture-correction.json').write_text(json.dumps({'scope':'INITIAL FIXTURE SETUP ONLY; signal had inferred all districts from nearby coordinates; explicit synthetic district diversification; initial org branch relationship','published_transitions':0,'audited_data_mutations_by_orm':0},indent=2))
print('Initial fixture districts/network set; audited transitions remain UI only.')
