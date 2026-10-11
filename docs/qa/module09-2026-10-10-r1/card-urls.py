import sys,json
sys.argv=['run.py','qa-readonly'];from run import *
from django.db import transaction,connection
from django.urls import reverse
from catalog.models import Place,Specialist,Event
f=json.loads((HERE/'fixtures.json').read_text())
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'")
 urls={'place':Place.objects.get(pk=f['places']['empty']).get_absolute_url(),'specialist':Specialist.objects.get(pk=f['specialist']).get_absolute_url(),'activity':reverse('activity_detail',args=[f['activity']]),'event':Event.objects.get(pk=f['event']).get_absolute_url()}
(HERE/'card-urls.json').write_text(json.dumps(urls,indent=2));print('Read-only public card routes')
