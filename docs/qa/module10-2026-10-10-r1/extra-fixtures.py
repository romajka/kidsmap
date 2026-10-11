"""One additional initial fictional legacy temporary Place; no audited transition."""
import sys,json
sys.argv=['run.py','qa-seed'];from run import *
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from catalog.testcases.utils import create_ready_place
from django.utils.translation import override
assert not (HERE/'extra-fixtures.json').exists()
u=get_user_model().objects.get(username='qa10_owner')
p=create_ready_place(name='Fictional QA10 temporary',name_az='Uydurma QA10 temporary',name_ru='Вымышленное QA10 temporary',name_en='Fictional QA10 temporary',owner=u,created_by=u,is_temporary=True,temporary_start=timezone.now()+timedelta(days=2),temporary_end=timezone.now()+timedelta(days=3),photo='places/qa10.png',lat=40.42,lng=49.82)
urls={}
for lang in ['ru','az','en']:
 with override(lang):urls[lang]=p.get_absolute_url()
(HERE/'extra-fixtures.json').write_text(json.dumps({'temporary':p.pk,'urls':urls},indent=2))
print('Additional initial fictional temporary Place',p.pk)
