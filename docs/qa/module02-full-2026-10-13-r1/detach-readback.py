import hashlib,json
from pathlib import Path
from django.db import transaction,connection
from catalog.models import Place,Activity,OfferingGroup,PricingPlan
P=Path(__file__).resolve().parent
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 p=Place.objects.get(pk=11);a=Activity.objects.get(place=p)
 protected={'groups':list(OfferingGroup.objects.filter(activity=a).order_by('pk').values()),'pricing':list(PricingPlan.objects.filter(offering_group__activity=a).order_by('pk').values()),'photos':[hashlib.sha256(Path(p.photo.path).read_bytes()).hexdigest()]+[hashlib.sha256(Path(x.image.path).read_bytes()).hexdigest() for x in p.gallery.all()]}
 out={'read_only':True,'owner_id':p.owner_id,'status':p.status,'organization_id':p.organization_id,'program_id':a.program_id,'snapshot':a.program_snapshot,'protected_hash':hashlib.sha256(json.dumps(protected,sort_keys=True,default=str).encode()).hexdigest()}
name='detach-after.json' if (P/'detach-before.json').exists() else 'detach-before.json';(P/name).write_text(json.dumps(out,indent=2));print(name)
