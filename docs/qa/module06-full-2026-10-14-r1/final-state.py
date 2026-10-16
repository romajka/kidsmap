import json
from pathlib import Path
from django.db import connection,transaction
from catalog.models import Place,Event,SiteSettings,VolunteerPlaceRevision,Activity,PricingPlan,EventOccurrenceChange
P=Path(__file__).resolve().parent;F=json.loads((P/'fixtures.json').read_text());rows=[]
def check(id,ok):
 rows.append({'id':id,'status':'PASS' if ok else 'FAIL'});assert ok,id
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 x=Place.objects.get(pk=F['places']['Page16']);rev=VolunteerPlaceRevision.objects.get(place=x);check('approved-edit-then-unpublish-preserved-name',x.name_az=='Uydurma QA06 UPDATED native' and x.status=='draft' and not x.is_active and rev.status=='approved')
 x=Place.objects.get(pk=F['places']['HIDDEN06_pending']);check('native-former-pending-published',x.status=='published' and x.is_active and VolunteerPlaceRevision.objects.get(place=x).status=='approved')
 check('other-private-fixtures-still-nonpublic',all((x.status!='published' or not x.is_active or x.deleted_at) for x in Place.objects.filter(pk__in=[i for i in F['private_places'] if i!=F['places']['HIDDEN06_pending']])))
 site=SiteSettings.get_solo();check('sections-restored',site.events_section_enabled and site.specialists_section_enabled and site.organizations_section_enabled)
 for k,g in F['groups'].items():
  a=Activity.objects.get(pk=g['activity']);check('group-source-preserved-'+k,a.status=='published' and a.offering_groups.get(pk=g['group']).archived_at is None)
 e=Event.objects.get(pk=F['events']['Scheduled']);check('native-event-reschedule-cancel-readback',e.occurrence_state=='cancelled' and EventOccurrenceChange.objects.filter(event=e,kind='cancel',reason='Fictional module06 cancellation').exists() and e.start_datetime.year==2030)
 out={'transaction':'READ ONLY','timeouts':['10s','2s'],'rows':rows,'fictional_only':True}
(P/'final-state.json').write_text(json.dumps(out,indent=2));print(json.dumps({'checks':len(rows),'readonly':True}))
