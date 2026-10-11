"""One new initial synthetic fixture for a genuinely zero-data metrics page."""
import sys,json
sys.argv=['run.py','initial-empty'];from run import *
from catalog.testcases.utils import create_ready_place
from django.contrib.auth import get_user_model
from catalog.models import Place
assert not Place.objects.filter(name_az='Uydurma QA12 sıfır').exists()
p=create_ready_place(name='Fictional QA12 zero',name_az='Uydurma QA12 sıfır',name_ru='Вымышленное QA12 без данных',name_en='Fictional QA12 zero data',owner=get_user_model().objects.get(username='qa12_owner'),status='draft')
(HERE/'empty-fixture.json').write_text(json.dumps({'synthetic_initial_only':True,'place_id':p.pk}))
print('Initial empty fixture',p.pk)
