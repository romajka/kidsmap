import json
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from catalog.models import Activity,Event,SiteSettings,Specialist
from catalog.services.public_presentation import present
from catalog.testcases.utils import create_ready_place

@transaction.atomic
def seed():
    U=get_user_model();assert not U.objects.exists()
    U.objects.create_user('s07-author',email='author@example.invalid',first_name='Fictional')
    site=SiteSettings.get_solo();site.specialists_section_enabled=site.events_section_enabled=True;site.save()
    place=create_ready_place(name='Fictional place',name_az='Fictional place AZ',name_ru='Fictional place RU',name_en='Fictional place EN')
    activities=[]
    for variant,fields in [
        ('localized',{'name_az':'Uydurma məşğələ AZ','name_ru':'Вымышленное занятие RU','name_en':'Fictional class EN'}),
        ('azfallback',{'name_az':'Uydurma yalnız AZ'}),
        ('snapshot',{'program_snapshot':{'name_az':'Approved snapshot AZ','name_ru':'Approved snapshot RU','name_en':'Approved snapshot EN'}})]:
        a=Activity.objects.create(place=place,status='published',**fields)
        names={lang:present(a,lang)['name'] for lang in ['az','ru','en']}
        activities.append({'variant':variant,'kind':'activity','pk':a.pk,'detail':f'/activities/{a.pk}/',
            'reviews':f'/reviews/activity/target/{a.pk}/','names':names})
    spec=Specialist.objects.create(name='Fictional specialist',status='published',is_active=True)
    event=Event.objects.create(name='Fictional event',name_az='Fictional event AZ',name_ru='Fictional event RU',name_en='Fictional event EN',
        category=place.category,status='published',event_format='online',start_datetime=timezone.now()+timedelta(days=5),
        end_datetime=timezone.now()+timedelta(days=5,hours=1))
    shared=[]
    for kind,t in [('place',place),('specialist',spec),('event',event)]:
        names={lang:('Fictional specialist' if kind=='specialist' else ('Fictional place ' if kind=='place' else 'Fictional event ')+lang.upper()) for lang in ['az','ru','en']}
        shared.append({'kind':kind,'pk':t.pk,'reviews':f'/reviews/{kind}/target/{t.pk}/','names':names})
    (settings.QA_ROOT/'targets.json').write_text(json.dumps({'activities':activities,'shared':shared},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Own fictional author,3Activity name scenarios,3other target kinds; no review/candidate records or external delivery')
