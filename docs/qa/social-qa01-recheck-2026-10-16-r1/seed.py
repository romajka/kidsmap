"""Initial fictional targets/accounts only. Reviews are created by native browser UI."""
from django.contrib.auth import get_user_model
from catalog.models import Place,Activity,Event,Specialist,SiteSettings,UserEmailVerification
from catalog.testcases.utils import create_ready_place
from django.utils import timezone
from datetime import timedelta
from PIL import Image
U=get_user_model();assert U.objects.count()==0
pw=json.loads((SCRATCH/'credentials.json').read_text())['login_password'];actors={}
for role in ('author','moderator','outsider'):
 u=U.objects.create_user(username='social01_'+role,email=role+'@example.invalid',password=pw,first_name='Fictional',last_name=role,is_staff=role=='moderator',is_superuser=role=='moderator')
 UserEmailVerification.objects.update_or_create(user=u,defaults={'email':u.email,'is_verified':True,'verified_at':timezone.now()})
 actors[role]={'id':u.pk,'username':u.username}
photo=settings.MEDIA_ROOT/'places/social01.png';photo.parent.mkdir(exist_ok=True);Image.new('RGB',(800,600),'#136F38').save(photo)
p=create_ready_place(name='Fictional SOCIAL01 place',name_ru='Вымышленное место SOCIAL01',name_az='Uydurma SOCIAL01 məkan',name_en='Fictional SOCIAL01 place',status='published',is_active=True,photo='places/social01.png',cover_photo='',description_az='Uydurma məkan. '*30,description_ru='Вымышленное место. '*30,description_en='Fictional place. '*30)
a=Activity.objects.create(place=p,status='published',name_az='Uydurma SOCIAL01 fəaliyyət',description_az='Fictional activity')
spec=Specialist.objects.create(name='Fictional SOCIAL01 specialist',name_alt='Uydurma SOCIAL01 mütəxəssis',status='published',is_active=True,bio_az='Uydurma mütəxəssis. '*25)
e=Event.objects.create(name='Fictional SOCIAL01 event',name_az='Uydurma SOCIAL01 tədbir',category=p.category,status='published',event_format='online',start_datetime=timezone.now()+timedelta(days=5),end_datetime=timezone.now()+timedelta(days=5,hours=1),description_az='Uydurma tədbir. '*25)
site=SiteSettings.get_solo();site.events_section_enabled=site.specialists_section_enabled=True;site.save()
fixture={'actors':actors,'targets':{'place':p.pk,'activity':a.pk,'specialist':spec.pk,'event':e.pk},'synthetic_only':True}
(HERE/'fixtures.json').write_text(json.dumps(fixture,indent=2));print('Created fictional accounts and four targets; reviews=0')
