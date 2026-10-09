import json
from pathlib import Path
from django.db import transaction
from django.db.models import F
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from catalog.models import Place,OrganizationPlaceRequest
from catalog.services.organization_ownership import create_organization,request_join,confirm_join
from catalog.services.organization_connections import preview_connections
from catalog.testcases.utils import create_quality_place
rows=[]
with transaction.atomic():
 owner=get_user_model().objects.get(username='demo_owner');other=get_user_model().objects.get(username='demo_outsider')
 org=create_organization(actor=owner,values={'name_az':'ORG12 Plan synthetic'})
 p=create_quality_place(owner=other,created_by=other,with_subcategory=True,name='ORG12 Plan branch',name_az='ORG12 Plan branch')
 r=request_join(actor=owner,place_id=p.pk,organization_id=org.pk)
 Place.objects.filter(pk=p.pk).update(content_version=F('content_version')+1)
 for name,fn in [('confirm_org',lambda:confirm_join(actor=owner,request_id=r.pk)),('confirm_place',lambda:confirm_join(actor=other,request_id=r.pk)),('request_again',lambda:request_join(actor=owner,place_id=p.pk,organization_id=org.pk))]:
  try:
   with transaction.atomic():fn()
   rows.append({'action':name,'result':'accepted'})
  except ValidationError as e:rows.append({'action':name,'result':'ValidationError','messages':e.messages})
 op=preview_connections(actor=owner,organization_id=org.pk,relationship_kind='business',place_ids=[p.pk]);r.refresh_from_db();p.refresh_from_db()
 result={'actions':rows,'pending_status':r.status,'linked':p.organization_id is not None,'preview_decisions':list(op.items.values_list('decision',flat=True)),'fixture_transaction_rolled_back':True}
 transaction.set_rollback(True)
Path(__file__).with_name('probe.json').write_text(json.dumps(result,indent=2));print(result)
