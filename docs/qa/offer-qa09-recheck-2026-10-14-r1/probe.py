import copy,json
from pathlib import Path
from django import forms
from django.db import connection,transaction
from catalog.models import Place,PricingPlan,VolunteerPlaceRevision
from catalog.services.volunteer_places import review_form
from catalog.services.place_readiness import evaluate_form_readiness
from catalog.services.pricing_plans import serialize_nested_pricing
P=Path(__file__).resolve().parent;f=json.loads((P/'fixtures.json').read_text())
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 place=Place.objects.get(pk=f['place']);revision=VolunteerPlaceRevision.objects.get(place=place);form=review_form(revision);valid=form.is_valid();readiness=evaluate_form_readiness(form,form.instance) if valid else None
 live_tree=serialize_nested_pricing(place)
 diagnostic=copy.copy(form);diagnostic.data=form.data.copy();diagnostic.data['nested_pricing']=live_tree;diagnostic._errors=None;diagnostic._bound_fields_cache={}
 simulated_valid=diagnostic.is_valid();simulated=evaluate_form_readiness(diagnostic,diagnostic.instance) if simulated_valid else None
 d={'transaction':'READ ONLY','candidate_status':revision.status,'payload_fields':sorted(revision.payload),'live_name_en':place.name_en,'candidate_name_en':revision.payload.get('name_en'),'active_group_price':str(PricingPlan.objects.get(pk=f['plan']).price),'direct_place_tariffs':PricingPlan.objects.filter(place=place,is_active=True).count(),'form_valid':valid,'cleaned_nested_pricing':form.cleaned_data.get('nested_pricing'),'is_ready':readiness.is_ready if readiness else None,'issues':[{'code':i.code,'field':i.field} for i in readiness.issues] if readiness else [],'diagnostic_simulation':'In-memory form data receives current trusted serialized live tree; no source/DB write, not app PASS','simulated_form_valid':simulated_valid,'simulated_is_ready':simulated.is_ready if simulated else None,'simulated_issues':[{'code':i.code,'field':i.field} for i in simulated.issues] if simulated else []}
(P/'probe.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
