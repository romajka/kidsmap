"""New own database only: distinct fictional queues for filter rendering."""
import io,json
from datetime import timedelta
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils import timezone
from catalog.models import Place,Event,Specialist,SpecialistSpecialization,Category,SiteSettings
from catalog.testcases.utils import create_ready_place
assert cfg['database']=='mod08_plan_r1'and Event.objects.count()==Specialist.objects.count()==0
password=json.loads((SCRATCH/'credentials.json').read_text())['login_password'];admin=get_user_model().objects.create_superuser('qa_mod08_admin','qa_mod08@example.invalid',password);owner=get_user_model().objects.create_user('qa_mod08_owner','qa_owner08@example.invalid',password)
buf=io.BytesIO();Image.new('RGB',(640,400),'#18643e').save(buf,format='WEBP');name=Place._meta.get_field('photo').storage.save('places/qa-mod08.webp',ContentFile(buf.getvalue()))
cats=[Category.objects.create(code=f'QA08{i}',name=f'QA category {i}',name_ru=f'QA категория {i}',name_az=f'QA kateqoriya {i}',name_en=f'QA category {i}')for i in(1,2)]
directions=[SpecialistSpecialization.objects.create(code=f'qa08-{i}',name=f'QA direction {i}',name_ru=f'QA направление {i}',name_az=f'QA ixtisas {i}',name_en=f'QA direction {i}')for i in(1,2)]
ids={'event':[],'specialist':[],'place':[]};now=timezone.now()
for i in range(3):
 title=f'QA Filter {i+1}';status=['published','pending','draft'][i];event=Event.objects.create(name=title+' Event',name_ru=title+' Мероприятие',name_az=title+' Tədbir',name_en=title+' Event',category=cats[i%2],start_datetime=now+timedelta(days=[0,3,35][i]),end_datetime=now+timedelta(days=[0,3,35][i],hours=2),owner=[admin,owner,admin][i],status=status,photo=name);ids['event'].append(event.pk)
 specialist=Specialist.objects.create(name=title+' Specialist',status=status,is_active=i!=1,consultation_format=['online','offline','both'][i],created_by=admin,photo=name,bio_ru='QA Bio',bio_az='QA Bio',bio_en='QA Bio');specialist.specializations.add(directions[i%2]);ids['specialist'].append(specialist.pk)
for i in range(2):
 p=create_ready_place(name=f'QA Filter Place {i+1}',name_ru=f'QA Filter Place {i+1}',name_az=f'QA Filter Place {i+1}',name_en=f'QA Filter Place {i+1}',created_by=admin,photo=name);ids['place'].append(p.pk)
site=SiteSettings.get_solo();site.specialists_section_enabled=True;site.save()
(HERE/'fixtures.json').write_text(json.dumps({'actors':{'admin':admin.username,'owner':owner.username},'ids':ids,'category_ids':[c.pk for c in cats],'direction_ids':[d.pk for d in directions],'database':'mod08_plan_r1','setup':'new fictional varied dates/status/category/format/direction; browser GET filters only'},indent=2));print(json.dumps({'own_users':2,'queue_counts':{k:len(v)for k,v in ids.items()},'own_db':cfg['database']}))
