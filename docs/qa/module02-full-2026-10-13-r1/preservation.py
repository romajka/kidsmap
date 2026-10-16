import hashlib,json
from pathlib import Path
from django.db import connection,transaction
from catalog.models import Place,PlacePhoto,Activity,OfferingGroup,PricingPlan
P=Path(__file__).resolve().parent
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 rows=[]
 for p in Place.objects.filter(pk__in=range(1,11)).order_by('pk'):
  values={f.name:f.value_from_object(p) for f in p._meta.concrete_fields if not (f.name.startswith('organization') or f.name in ['updated_at','content_version'])}
  values['days']=list(p.schedule_days.order_by('pk').values());values['place_pricing']=list(PricingPlan.objects.filter(place=p).order_by('pk').values());values['photos']=list(PlacePhoto.objects.filter(place=p).order_by('pk').values());values['activities']=list(Activity.objects.filter(place=p).order_by('pk').values());values['groups']=list(OfferingGroup.objects.filter(activity__place=p).order_by('pk').values());values['pricing']=list(PricingPlan.objects.filter(offering_group__activity__place=p).order_by('pk').values())
  media=[p.photo.path]+[x.image.path for x in p.gallery.all()]
  rows.append({'place_id':p.pk,'owner_id':p.owner_id,'rich_hash':hashlib.sha256(json.dumps(values,sort_keys=True,default=str).encode()).hexdigest(),'media_sha256':[hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in media],'organization_id':p.organization_id})
result={'read_only':True,'rows':rows};name='preservation-after.json' if (P/'preservation-before.json').exists() else 'preservation-before.json';(P/name).write_text(json.dumps(result,indent=2));print(name)
