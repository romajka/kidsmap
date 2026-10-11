"""Initial fictional nonpublic records; these are not transition evidence."""
import sys,json
sys.argv=['run.py','private-fixture-bootstrap'];from run import *
from catalog.models import *
from django.utils import timezone
from django.utils.translation import override
from django.urls import reverse
from datetime import timedelta
F=json.loads((HERE/'fixtures.json').read_text());out={};place=Place.objects.get(pk=F['places']['live'])
for state in ['draft','pending','rejected','archived','inactive']:
 out[state]={}
 if state!='inactive':
  org,_=Organization.objects.get_or_create(name_az='PRIVATE_QA11_ORG_'+state,defaults={'description_az':'Fictional private organization.','status':'published' if state=='archived' else state,'approved_at':timezone.now() if state=='archived' else None,'archived_at':timezone.now() if state=='archived' else None})
  activity,_=Activity.objects.get_or_create(place=place,name_az='PRIVATE_QA11_ACTIVITY_'+state,defaults={'description_az':'Fictional private activity.','status':'published' if state=='archived' else state,'archived_at':timezone.now() if state=='archived' else None})
  out[state]['organization']=org.pk;out[state]['organization_public_id']=str(org.public_id);out[state]['activity']=activity.pk
 if state!='archived':
  s,_=Specialist.objects.get_or_create(name='PRIVATE_QA11_SPECIALIST_'+state,defaults={'status':'published' if state=='inactive' else state,'is_active':state!='inactive','bio_az':'Fictional private specialist.'})
  out[state]['specialist']=s.pk;out[state]['specialist_slug']=s.slug
  if state!='inactive':
   e,_=Event.objects.get_or_create(name='PRIVATE_QA11_EVENT_'+state,defaults={'name_az':'PRIVATE_QA11_EVENT_'+state,'description_az':'Fictional private event.','category':place.category,'status':state,'start_datetime':timezone.now()+timedelta(days=4),'end_datetime':timezone.now()+timedelta(days=4,hours=1),'event_format':'online'})
   out[state]['event']=e.pk;out[state]['event_slug']=e.slug
e,_=Event.objects.get_or_create(name='PRIVATE_QA11_EVENT_deleted',defaults={'name_az':'PRIVATE_QA11_EVENT_deleted','description_az':'Fictional private event.','category':place.category,'status':'published','deleted_at':timezone.now(),'start_datetime':timezone.now()+timedelta(days=4),'end_datetime':timezone.now()+timedelta(days=4,hours=1),'event_format':'online'})
out['deleted']={'event':e.pk,'event_slug':e.slug}
out['urls']={}
for lang in ['az','ru','en']:
 with override(lang):
  out['urls'][lang]={state:{kind:(reverse('organization_detail',args=[values['organization_public_id']]) if kind=='organization' else reverse('activity_detail',args=[pk]) if kind=='activity' else Specialist.objects.get(pk=pk).get_absolute_url() if kind=='specialist' else Event.objects.get(pk=pk).get_absolute_url()) for kind,pk in values.items() if kind in ['organization','activity','specialist','event']} for state,values in out.items() if state!='urls'}
(HERE/'private-fixtures.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print('Fresh initial private entity fixtures created')
