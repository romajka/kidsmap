"""Fictional initial accounts/targets. Review mutations are exclusively native UI."""
from django.contrib.auth import get_user_model
from catalog.models import Activity,Event,Specialist,SiteSettings,UserEmailVerification
from catalog.testcases.utils import create_ready_place
from django.utils import timezone
from datetime import timedelta
from PIL import Image
U=get_user_model();assert U.objects.count()==0
pw=json.loads((SCRATCH/'credentials.json').read_text())['login_password']
def actor(label,staff=False):
 u=U.objects.create_user(username='social01_'+label,email=label+'@example.invalid',password=pw,first_name='Fictional',last_name=label,is_staff=staff,is_superuser=staff)
 UserEmailVerification.objects.update_or_create(user=u,defaults={'email':u.email,'is_verified':True,'verified_at':timezone.now()})
 return {'id':u.pk,'username':u.username}
actors={'moderator':actor('moderator',True),'outsider':actor('outsider')};cases=[]
photo=settings.MEDIA_ROOT/'places/social01.png';photo.parent.mkdir(exist_ok=True);Image.new('RGB',(800,600),'#136F38').save(photo)
for i,(lang,width)in enumerate((l,w)for l in('ru','az','en')for w in(390,1440)):
 users={role:actor(str(i)+'_'+role)for role in('author','repeat','rejected')}
 p=create_ready_place(name='Fictional SOCIAL01 '+str(i),name_ru='Вымышленное SOCIAL01 '+str(i),name_az='Uydurma SOCIAL01 '+str(i),name_en='Fictional SOCIAL01 '+str(i),status='published',is_active=True,photo='places/social01.png',cover_photo='',description_az='Uydurma məkan. '*30,description_ru='Вымышленное место. '*30,description_en='Fictional place. '*30)
 a=Activity.objects.create(place=p,status='published',name_az='Uydurma SOCIAL01 fəaliyyət '+str(i),description_az='Fictional activity')
 spec=Specialist.objects.create(name='Fictional SOCIAL01 specialist '+str(i),name_alt='Uydurma SOCIAL01 mütəxəssis '+str(i),status='published',is_active=True,bio_az='Uydurma mütəxəssis. '*25)
 e=Event.objects.create(name='Fictional SOCIAL01 event '+str(i),name_az='Uydurma SOCIAL01 tədbir '+str(i),category=p.category,status='published',event_format='online',start_datetime=timezone.now()+timedelta(days=5),end_datetime=timezone.now()+timedelta(days=5,hours=1),description_az='Uydurma tədbir. '*25)
 cases.append({'id':i,'lang':lang,'width':width,'actors':users,'targets':{'place':p.pk,'activity':a.pk,'specialist':spec.pk,'event':e.pk}})
site=SiteSettings.get_solo();site.events_section_enabled=site.specialists_section_enabled=True;site.save()
fixture={'actors':actors,'cases':cases,'targets':cases[0]['targets'],'synthetic_only':True}
(HERE/'fixtures.json').write_text(json.dumps(fixture,indent=2));print('Fictional initial fixtures:20accounts,24typed targets,reviews0')
