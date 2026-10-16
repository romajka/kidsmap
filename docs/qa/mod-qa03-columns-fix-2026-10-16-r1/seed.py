"""Initial fictional queue data only; no application mutation during PLAN browser checks."""
import io,json
from datetime import timedelta
from PIL import Image,ImageDraw
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils import timezone
from catalog.models import Place,Event,Specialist,SiteSettings
from catalog.testcases.utils import create_ready_place
password=json.loads((SCRATCH/'credentials.json').read_text())['login_password'];admin=get_user_model().objects.create_superuser('qa_mod03_admin','qa_mod03_admin@example.invalid',password)
buf=io.BytesIO();im=Image.new('RGB',(640,400),'#18643e');ImageDraw.Draw(im).text((30,50),'FICTIONAL QUEUE QA',fill='white');im.save(buf,format='WEBP');name=Place._meta.get_field('photo').storage.save('places/qa-mod03.webp',ContentFile(buf.getvalue()))
ids={'place':[],'event':[],'specialist':[]}
for i in range(1,4):
 title=f'QA Queue {i}';p=create_ready_place(name=title,name_az=title+' uşaqlar üçün uzun sınaq adı',name_ru=title+' длинное вымышленное название детского центра',name_en=title+' fictional long children activity center name',created_by=admin,photo=name,address='Fictional QA address 101, synthetic district, no real location')
 ids['place'].append(p.pk)
 event=Event.objects.create(name=title+' Event',name_az=title+' Tədbir',name_ru=title+' Мероприятие',name_en=title+' Event',category_id=p.category_id,start_datetime=timezone.now()+timedelta(days=i),end_datetime=timezone.now()+timedelta(days=i,hours=2),status='published',photo=name)
 ids['event'].append(event.pk)
 specialist=Specialist.objects.create(name=title+' Specialist',created_by=admin,status='published',is_active=True,photo=name,bio_az='Fictional local specialist bio',bio_ru='Вымышленная биография только для QA',bio_en='Fictional local specialist bio',consultation_format='online')
 ids['specialist'].append(specialist.pk)
site=SiteSettings.get_solo();site.specialists_section_enabled=True;site.save()
(HERE/'fixtures.json').write_text(json.dumps({'actors':{'admin':admin.username},'ids':ids,'rows_per_queue':3,'fixture_media':name,'setup':'initial synthetic visible queue records; no native save/approval claimed'},indent=2));print(json.dumps({'own_users':1,'initial_rows':ids}))


Place.objects.create(name='QA Deleted Place',name_ru='QA Deleted Place',name_az='QA Deleted Place',name_en='QA Deleted Place',category_id='EDU',status='draft',is_active=False,deleted_at=timezone.now(),deleted_by=admin)
from django.contrib.auth.models import Permission
reader=get_user_model().objects.create_user('qa_columns_reader','qa_columns_reader@example.invalid',password,is_staff=True)
reader.user_permissions.add(Permission.objects.get(codename='view_specialist',content_type__app_label='catalog'))
fixture=json.loads((HERE/'fixtures.json').read_text());fixture['actors']['reader']=reader.username;(HERE/'fixtures.json').write_text(json.dumps(fixture,indent=2))
