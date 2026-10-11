"""Initial lawful fixture for OFF flag admin draft-save; not an audited transition."""
import sys,json
sys.argv=['run.py','qa-seed'];from run import *
from django.contrib.auth import get_user_model
from django.utils import timezone
from catalog.models import Organization
actor=get_user_model().objects.get(username='qa10_admin')
obj=Organization.objects.create(owner=actor,name_az='Uydurma QA10 admin təşkilatı',name_ru='Вымышленная QA10 организация админа',name_en='Fictional QA10 admin organization',status='published',approved_at=timezone.now(),phone='+994000000020')
(HERE/'owned-organization.json').write_text(json.dumps({'id':obj.pk,'owner':'qa10_admin','initial_status':obj.status,'initial_names':{k:getattr(obj,k) for k in ('name_az','name_ru','name_en')}}),encoding='utf-8')
print('Created initial lawful organization',obj.pk)
