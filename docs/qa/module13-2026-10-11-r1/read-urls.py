import sys,json
sys.argv=['run.py','qa-urls'];from run import *
from catalog.models import Place,Organization,Activity,Specialist,Event
from django.urls import reverse
from django.utils.translation import override
result={}
for lang in ['ru','az','en']:
 with override(lang):
  result[lang]={'places':{str(x.pk):x.get_absolute_url() for x in Place.objects.all()},'organizations':{str(x.pk):reverse('organization_detail',args=[x.public_id]) for x in Organization.objects.all()},'activities':{str(x.pk):reverse('activity_detail',args=[x.pk]) for x in Activity.objects.all()},'specialists':{str(x.pk):x.get_absolute_url() for x in Specialist.objects.all()},'events':{str(x.pk):x.get_absolute_url() for x in Event.objects.all()}}
(HERE/'card-urls.json').write_text(json.dumps(result,indent=2))
print({k:{s:len(v) for s,v in value.items()} for k,value in result.items()})
