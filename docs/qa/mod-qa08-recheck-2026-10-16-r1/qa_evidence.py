import hashlib,json
from django.conf import settings
from django.http import JsonResponse,Http404
from django.db import connection,transaction
from catalog.models import Place,Event,Specialist,SpecialistPracticeLocation,SpecialistDocument

def state(request):
 if not settings.TESTING or request.META.get('REMOTE_ADDR')!='127.0.0.1':raise Http404
 with transaction.atomic():
  with connection.cursor()as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
  data={name:list(model.objects.order_by('pk').values())for name,model in(('places',Place),('events',Event),('specialists',Specialist))}
  data['specializations']={str(pk):list(Specialist.objects.get(pk=pk).specializations.order_by('pk').values_list('pk',flat=True))for pk in Specialist.objects.values_list('pk',flat=True)}
  data['locations']=list(SpecialistPracticeLocation.objects.order_by('pk').values());data['documents']=list(SpecialistDocument.objects.order_by('pk').values())
 return JsonResponse({'read_only':True,'synthetic_only':True,'counts':{k:len(v)for k,v in data.items()},'domain_sha256':hashlib.sha256(json.dumps(data,sort_keys=True,default=str).encode()).hexdigest()})
