"""Initial synthetic entities only, no audited rename/flag/detach transitions."""
import sys,json
sys.argv=['run.py','fixture-bootstrap'];from run import *
from catalog.models import *
from catalog.testcases.utils import create_ready_place
from django.utils import timezone
from django.utils.translation import override
from django.urls import reverse
from catalog.services.public_presentation import public_url
F=json.loads((HERE/'fixtures.json').read_text());owner=__import__('django.contrib.auth',fromlist=['get_user_model']).get_user_model().objects.get(pk=F['actors']['owner']['id'])
org=Organization.objects.get(pk=F['organization'])
org.description_az='Uydurma QA11 təşkilat haqqında təsvir. '*12;org.description_ru='Вымышленная QA11 сеть и занятия. '*15;org.description_en='Fictional QA11 network and activities. '*15;org.save()
place=Place.objects.get(pk=F['places']['live'])
program=Program.objects.create(organization=org,name_az='Uydurma QA11 proqram',name_ru='Вымышленная QA11 программа',name_en='Fictional QA11 programme',description_az='Uydurma proqram. '*20,description_ru='Вымышленная программа. '*20,description_en='Fictional programme. '*20,status='published',approved_at=timezone.now(),category=place.category,subcategory=place.subcategory)
activity=Activity.objects.create(place=place,program=program,name_az='Uydurma QA11 fəaliyyət',name_ru='Вымышленное QA11 занятие',name_en='Fictional QA11 activity',description_az='Uydurma fəaliyyət. '*20,description_ru='Вымышленное занятие. '*20,description_en='Fictional activity. '*20,status='published',category=place.category,subcategory=place.subcategory)
F['program']=program.pk;F['activity']=activity.pk
F['extra_places']={}
for label,status,active,deleted,short_en in [('pending','pending',True,False,False),('rejected','rejected',True,False,False),('fallback','published',True,False,True),('long','published',True,False,False),('escaping','published',True,False,False)]:
 name={'az':'Uydurma QA11 '+label,'ru':'Вымышленное QA11 '+label,'en':'Fictional QA11 '+label}
 if label=='long':name={k:v+' '+('LongText ' if k=='en' else 'UzunMətn ' if k=='az' else 'ДлинныйТекст ')*15 for k,v in name.items()}
 if label=='escaping':name={k:v+' </script><script>window.__QA11_XSS__=1</script> "&<>' for k,v in name.items()}
 p=create_ready_place(owner=owner,created_by=owner,name=name['az'],name_az=name['az'],name_ru=name['ru'],name_en='' if short_en else name['en'],description_az='Uydurma məkan. '*30,description_ru='Вымышленное место. '*30,description_en='' if short_en else 'Fictional place. '*30,status=status,is_active=active,photo='places/qa11.png',lat=40.4,lng=49.8)
 F['extra_places'][label]=p.pk
for n in range(12):
 create_ready_place(owner=owner,name=f'Fictional QA11 collection {n}',name_az=f'Uydurma QA11 seçim {n}',name_ru=f'Вымышленная QA11 подборка {n}',name_en=f'Fictional QA11 collection {n}',description_az='Uydurma məkan. '*30,description_ru='Вымышленное место. '*30,description_en='Fictional place. '*30,photo='places/qa11.png',lat=40.4,lng=49.8)
content=CatalogContentSettings.get_solo();content.seo_pages_json={lang:{'qa11-strong':{'title':{'az':'Uydurma QA11 seçim','ru':'Вымышленная QA11 подборка','en':'Fictional QA11 collection'}[lang],'meta_description':'Fictional QA11 collection description','intro':'Fictional QA11 introduction','benefits':['Fictional listings'],'catalog_query':'?category=EDU','faq':[['Fictional question?','Fictional answer.']]},'qa11-empty':{'title':'Fictional QA11 empty','meta_description':'Fictional QA11 empty description','intro':'Fictional QA11 empty introduction','benefits':[],'catalog_query':'?q=QA11-NO-SUCH-ENTITY','faq':[]}} for lang in ['az','ru','en']};content.save(update_fields=['seo_pages_json','updated_at'])
site=SiteSettings.get_solo();site.organizations_section_enabled=site.specialists_section_enabled=site.events_section_enabled=True;site.save()
for lang in ['az','ru','en']:
 with override(lang):
  F['urls'][lang]['activity']=public_url(activity,lang);F['urls'][lang]['program']=reverse('organization_program_detail',args=[org.pk,program.pk]);F['urls'][lang]['landing']='/'+('' if lang=='az' else lang+'/')+'catalog/qa11-strong/'
  F['urls'][lang]['extras']={k:Place.objects.get(pk=v).get_absolute_url() for k,v in F['extra_places'].items()}
(HERE/'fixtures.json').write_text(json.dumps(F,indent=2,ensure_ascii=False),encoding='utf-8')
print('Fresh synthetic related and visibility fixtures. Program is private workspace; Activity public.')
