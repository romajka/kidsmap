import json
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from catalog.models import Activity,Event,SiteSettings,Specialist
from catalog.testcases.utils import create_ready_place

@transaction.atomic
def seed():
    assert not Specialist.objects.exists() and not Event.objects.exists()
    site=SiteSettings.get_solo()
    site.specialists_section_enabled=site.events_section_enabled=True
    site.save()
    targets=[]
    for kind in ['place','activity','specialist','event']:
        label='Fictional shared '+kind
        if kind=='specialist':
            target=Specialist.objects.create(name=label,status='published',is_active=True)
        else:
            place=create_ready_place(name=label,name_az=label,name_ru=label,name_en=label)
            if kind=='place':target=place
            elif kind=='activity':target=Activity.objects.create(place=place,status='published',name_az=label,name_ru=label,name_en=label)
            else:target=Event.objects.create(name=label,name_az=label,category=place.category,status='published',event_format='online',
                start_datetime=timezone.now()+timedelta(days=5),end_datetime=timezone.now()+timedelta(days=5,hours=1))
        targets.append({'kind':kind,'pk':target.pk,'url':f'/reviews/{kind}/target/{target.pk}/'})
    (settings.QA_ROOT/'shared-targets.json').write_text(json.dumps(targets,indent=2)+'\n')
    print('Seeded four own fictional shared review targets; SiteReview records unchanged')
