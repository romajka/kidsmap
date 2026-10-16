"""One synthetic specialist for invalid-POST presentation recheck, in NEW own DB only."""
import io,json
from PIL import Image,ImageDraw
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from catalog.models import Specialist,SpecialistSpecialization
assert cfg['database']=='mod07_plan_r1'and Specialist.objects.count()==0
password=json.loads((SCRATCH/'credentials.json').read_text())['login_password'];admin=get_user_model().objects.create_superuser('qa_mod07_admin','qa_mod07@example.invalid',password)
spec=SpecialistSpecialization.objects.create(code='qa_mod07',name='QA direction',name_ru='Вымышленная специализация',name_az='Uydurma ixtisas',name_en='Fictional specialization')
buf=io.BytesIO();Image.new('RGB',(640,400),'#18643e').save(buf,format='WEBP');profile=Specialist.objects.create(name='QA Error Summary Specialist',created_by=admin,status='published',is_active=True,consultation_format='online',bio_ru='Вымышленная биография',bio_az='Uydurma bioqrafiya',bio_en='Fictional biography');profile.photo.save('qa-mod07.webp',ContentFile(buf.getvalue()));profile.specializations.add(spec)
(HERE/'fixtures.json').write_text(json.dumps({'actors':{'admin':admin.username},'ids':{'specialist':[profile.pk]},'specialization_id':spec.pk,'fixture':'NEW ownDB; one fictional specialist, initially has specialization; only invalid submissions permitted during PLAN'},indent=2));print(json.dumps({'synthetic_specialists':1,'specializations':1,'new_database_only':True}))
