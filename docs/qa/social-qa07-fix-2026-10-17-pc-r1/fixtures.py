import json
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from catalog.models import Activity,Organization,Program
from catalog.services.public_presentation import present
from catalog.services.organization_ownership import request_join
from catalog.testcases.utils import create_ready_place
@transaction.atomic
def seed():
 U=get_user_model();assert not U.objects.filter(username='s07-fix-staff').exists()
 staff=U.objects.create_superuser('s07-fix-staff','staff@example.invalid',None)
 owner=U.objects.get(username='s07-author');place=Activity.objects.order_by('pk').first().place
 org=Organization.objects.create(owner=owner,created_by=owner,name_az='Fictional07 organization',status='published',approved_at=timezone.now())
 parent=create_ready_place(owner=owner,created_by=owner,name='Fictional07 program parent')
 request_join(actor=owner,place_id=parent.pk,organization_id=org.pk);parent.refresh_from_db()
 program=Program.objects.create(organization=org,name_az='Live AZ',name_ru='Live RU',name_en='Live EN',status='published',approved_at=timezone.now())
 rows=[]
 for variant,fields in [('escaping',dict(place=place,status='published',name_az='<script>fictional()</script> & class')),('empty',dict(place=place,status='published')),('hidden',dict(place=place,status='draft',name_az='PRIVATE DRAFT')),('liveprogram',dict(place=parent,status='published',program=program))]:
  a=Activity.objects.create(**fields);rows.append(dict(variant=variant,pk=a.pk,reviews=f'/reviews/activity/target/{a.pk}/',names={lang:present(a,lang)['name'] for lang in ['az','ru','en']}))
 (settings.QA_ROOT/'edge-targets.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
 print('Own fictional edge fixtures created; no reviews or candidate records')
