"""Read-only synthetic DB evidence; never perform audited transitions."""
import sys,json,datetime
output_name=sys.argv[1] if len(sys.argv)>1 else 'current-state.json'
sys.argv=['run.py','qa-state'];from run import *
from django.apps import apps
from django.db import connection,transaction
from django.db.models import Count
allowed=['Place','Organization','Program','Activity','OfferingGroup','PricingPlan','VolunteerPlaceRevision','PublicationRevision','OrganizationJoinRequest','OrganizationConnectionOperation','Specialist','SpecialistProposalDraft','SpecialistEmployment','SpecialistPracticeLocation','Event','EventPhoto','PlacePhoto','OwnerTeamMembership','OrganizationTeamMembership','PlaceReview','SpecialistReview','PlaceLike','FunnelEvent']
payload={}
with transaction.atomic():
 with connection.cursor() as cur:
  cur.execute('SET TRANSACTION READ ONLY');cur.execute("SET LOCAL statement_timeout='10s'");cur.execute("SET LOCAL lock_timeout='2s'")
 for name in allowed:
  try:model=apps.get_model('catalog',name)
  except LookupError:continue
  fields=[f.attname for f in model._meta.fields if f.name not in ['session_key','actor_hash','identity_hash','token','email','phone','phone2','phone3']]
  payload[name]=list(model.objects.values(*fields).order_by('pk'))
target=HERE/output_name
target.write_text(json.dumps(payload,default=str,indent=2),encoding='utf-8')
print({k:len(v) for k,v in payload.items()})
