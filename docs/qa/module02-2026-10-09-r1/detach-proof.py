import json,sys,hashlib
sys.argv=['run.py','observe']
from run import *
from catalog.models import Place,Activity,OfferingGroup,PricingPlan
from catalog.services.organization_ownership import affiliation_current
p=Place.objects.get(pk=11)
a=Activity.objects.get(pk=11)
before=json.loads((HERE/'observation-before-detach.json').read_text(encoding='utf-8'))
after=json.loads((HERE/'observation-after-detach.json').read_text(encoding='utf-8'))
# Rich ten places already verified byte-for-byte before/after connect. Detach11's dependency snapshot is explicit.
proof={'detached':p.organization_id is None,'owner_unchanged':p.owner_id==1,'status_unchanged':p.status=='published','program_became_local':a.program_id is None,'approved_snapshot_preserved':bool(a.program_snapshot),'groups_retained':OfferingGroup.objects.filter(activity=a).count()==1,'pricing_retained':PricingPlan.objects.filter(offering_group__activity=a).count()==1,'media_retained':bool(p.photo and p.gallery.count()==2),'transfer14_B':Place.objects.get(pk=14).organization_id==2,'new_branch_separate_id':Place.objects.filter(pk=33,organization_id=1).exists(),'informational27_owner_unchanged':Place.objects.get(pk=27).owner_id==2,'informational27_kind':Place.objects.get(pk=27).organization_relationship_kind}
(HERE/'detach-proof.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
print(json.dumps(proof))
