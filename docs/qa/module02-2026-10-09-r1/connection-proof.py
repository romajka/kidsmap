import sys,json
sys.argv=['run.py','observe']
from run import *
from catalog.models import OrganizationConnectionOperation,OrganizationConnectionItem
bulk=OrganizationConnectionOperation.objects.get(pk='33aa85e9-0f3b-4a7d-afe6-cf15353bb452')
mixed=OrganizationConnectionOperation.objects.get(pk='5a42d182-c6bf-4eab-8e05-7fd77dd0947d')
rows={str(o.pk):dict(o.items.values_list('place_id','result')) for o in [bulk,mixed]}
expected={1:'already_connected',12:'other_network',13:'changed',16:'connected',23:'requested'}
out={'bulk_status':bulk.status,'bulk_ten_correct':rows[str(bulk.pk)]=={i:'connected' for i in range(1,11)},'mixed_status':mixed.status,'mixed_correct':rows[str(mixed.pk)]==expected,'results':rows}
(HERE/'connection-proof.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
assert out['bulk_ten_correct'] and out['mixed_correct']
before=json.loads((HERE/'observation-before.json').read_text(encoding='utf-8'))['preservation']
after=json.loads((HERE/'observation-after-bulk.json').read_text(encoding='utf-8'))['preservation']
assert before==after
print('Ten rich-place identities/media/schedule/activity/group/pricing records unchanged; mixed5 exact canonical results PASS')
