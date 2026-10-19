import json
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from catalog.models import Activity, Event, SiteSettings, Specialist
from catalog.services.review_versions import submit_review, moderate_candidate, review_types
from catalog.testcases.utils import create_ready_place

@transaction.atomic
def seed():
    users=get_user_model()
    author=users.objects.create_user('s03pc-author',first_name='Fictional')
    users.objects.create_user('s03pc-outsider',first_name='Fictional outsider')
    staff=users.objects.create_superuser('s03pc-reviewer','reviewer@example.invalid',None)
    site=SiteSettings.get_solo()
    site.specialists_section_enabled=site.events_section_enabled=True
    site.save()
    cases=[]
    for kind in ('place','activity','event','specialist'):
        for lang in ('ru','az','en'):
            for width in (360,390,768,1024,1280,1440):
                cell=len(cases)
                label=f'Fictional {kind} {cell}'
                if kind=='specialist':target=Specialist.objects.create(name=label,status='published',is_active=True)
                else:
                    place=create_ready_place(name=label,name_az=label,name_ru=label,name_en=label)
                    if kind=='place':target=place
                    elif kind=='activity':target=Activity.objects.create(place=place,status='published',name_az=label,name_ru=label,name_en=label)
                    else:target=Event.objects.create(name=label,name_az=label,category=place.category,status='published',event_format='online',
                        start_datetime=timezone.now()+timedelta(days=5),end_datetime=timezone.now()+timedelta(days=5,hours=1))
                head,revision=submit_review(target=target,user=author,rating=4,text='Public current four',author_name='Fictional')
                moderate_candidate(head=head,revision_id=revision.pk,actor=staff,approve=True)
                old=timezone.now()-timedelta(minutes=10)
                # Initial fixture only: no future native A/B/C timestamp is changed.
                review_types()[kind][1].objects.filter(pk=head.pk).update(created_at=old,submitted_at=old)
                type(revision).objects.filter(pk=revision.pk).update(created_at=old,submitted_at=old)
                cases.append({'cell':cell,'kind':kind,'lang':lang,'width':width,'pk':target.pk,
                              'url':('' if lang=='az' else '/'+lang)+f'/reviews/{kind}/target/{target.pk}/'})
    (settings.QA_ROOT/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
    print('Seeded72 fictional current4 cases and3 actors; initial fixture timestamps only aged10min')

def case(cell):
    return json.loads((settings.QA_ROOT/'cases.json').read_text())[cell]
