import json
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from catalog.models import Activity,Event,SiteSettings,Specialist,SiteReview
from catalog.testcases.utils import create_ready_place

@transaction.atomic
def seed():
    U=get_user_model()
    assert SiteReview.objects.count()==2 and not SiteReview.objects.filter(status='pending').exists()
    assert not U.objects.filter(username__startswith='s06-fix-').exists()
    for lang in ['ru','az','en']:U.objects.create_user('s06-fix-'+lang,email=lang+'@example.invalid',first_name='Fictional')
    site=SiteSettings.get_solo();site.specialists_section_enabled=site.events_section_enabled=True;site.save()
    place=create_ready_place(name='Fictional shared place',name_az='Fictional shared place',name_ru='Fictional shared place',name_en='Fictional shared place')
    activity=Activity.objects.create(place=place,status='published',name_az='Fictional shared activity',name_ru='Fictional shared activity',name_en='Fictional shared activity')
    spec=Specialist.objects.create(name='Fictional shared specialist',status='published',is_active=True)
    event=Event.objects.create(name='Fictional shared event',name_az='Fictional shared event',category=place.category,status='published',event_format='online',
        start_datetime=timezone.now()+timedelta(days=5),end_datetime=timezone.now()+timedelta(days=5,hours=1))
    targets=[{'kind':'home','url':'/'},{'kind':'place_detail','url':place.get_absolute_url()}]
    for kind,target in [('activity',activity),('specialist',spec),('event',event)]:
        targets.append({'kind':kind,'url':f'/reviews/{kind}/target/{target.pk}/'})
    (settings.QA_ROOT/'shared-targets.json').write_text(json.dumps(targets,indent=2)+'\n')
    print('Created3fresh fictional submit authors and5shared page targets; initial SiteReview state preserved')
