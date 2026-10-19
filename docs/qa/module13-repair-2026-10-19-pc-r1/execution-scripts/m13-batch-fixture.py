import sys,json
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/m13-full-r1');sys.argv=['runtime.py','batch-fixture'];from runtime import *
from catalog.testcases.utils import create_ready_place
from catalog.models import Place
from django.contrib.auth import get_user_model
editor=get_user_model().objects.get(username='m13_editor');assert not Place.objects.filter(name_az='M13 Batch Independent Branch').exists()
p=create_ready_place(owner=editor,created_by=editor,name_az='M13 Batch Independent Branch',name_ru='M13 Независимый филиал для пакета',name_en='M13 Batch Independent Branch');p.photo=Place.objects.get(pk=1).photo;p.save(update_fields=['photo']);assert p.pk==3
(QA/'batch-fixture.json').write_text(json.dumps({'place':p.pk,'initial_standalone':p.organization_id is None,'owner':'fictional editor actor','initial_fixture_only':True}));print('Initial standalone branch3 for real native partial batch and second-owner consent; prior audited entities unchanged.')
