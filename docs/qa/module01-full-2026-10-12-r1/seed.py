from pathlib import Path
import json
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from catalog.models import Category,UserEmailVerification
from catalog.testcases.utils import ensure_quality_subcategory
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;SCRATCH=settings.QA_ROOT
secrets=json.loads((SCRATCH/'credentials.json').read_text());U=get_user_model();actors={}
for role,username in [('owner','start_owner'),('admin','start_admin'),('outsider','accept_outsider'),('staff','accept_staff')]:
 u,created=U.objects.get_or_create(username=username,defaults={'email':role+'accept01@example.invalid','is_staff':role in ('admin','staff'),'is_superuser':role=='admin'})
 if created:u.set_password(secrets['owner_password']);u.save()
 UserEmailVerification.objects.update_or_create(user=u,defaults={'email':u.email,'is_verified':True,'verified_at':timezone.now()})
 actors[role]={'id':u.pk,'username':u.username,'email':u.email}
cat=Category.objects.create(code='QA01_LONG',name='QA01 '+'Long fictional category '*7,name_ru='QA01 '+'Длинная вымышленная категория '*7,name_az='QA01 '+'Uzun uydurma kateqoriya '*7,name_en='QA01 '+'Long fictional category '*7);ensure_quality_subcategory(cat)
assets=SCRATCH/'assets';assets.mkdir()
for name,color in [('fixture','#136F38'),('replacement','#eddfbe'),('gallery','#cde7c5')]:
 im=Image.new('RGB',(800,600),color);ImageDraw.Draw(im).text((20,20),'FICTIONAL ACCEPT01 '+name,fill='#111');im.save(assets/(name+'.png'))
(assets/'bad.png').write_text('not an image; synthetic invalid file')
(HERE/'fixtures.json').write_text(json.dumps({'actors':actors,'synthetic_only':True}))
print('Own initial actors/taxonomy/assets ready; audited transitions not seeded.')
