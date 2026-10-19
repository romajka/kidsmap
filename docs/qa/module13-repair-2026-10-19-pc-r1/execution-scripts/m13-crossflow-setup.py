from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
(O/'crossflow_driver.py').write_text((O/'browser_driver.py').read_text().replace('-s=m13-full-r1','-s=m13-crossflow-r1'))
# An independent initial standalone fixture for native connection/publication.
(Q/'seed-crossflow.py').write_text('''import sys,json
sys.argv=['runtime.py','seed-crossflow'];from runtime import *
from catalog.models import Place
from catalog.testcases.utils import create_ready_place
from django.contrib.auth import get_user_model
assert not Place.objects.filter(name_az='M13 Intermodule Branch').exists()
u=get_user_model().objects.get(username='m13_owner');p=create_ready_place(owner=u,created_by=u,name_az='M13 Intermodule Branch',name_ru='M13 Межмодульный филиал',name_en='M13 Intermodule Branch',status='draft')
p.photo=Place.objects.get(pk=1).photo;p.save(update_fields=['photo'])
(QA/'crossflow-fixtures.json').write_text(json.dumps({'standalone':p.pk}))
print('Fresh standalone draft fixture for actual native publication/connection; initial setup only.')
''')
print('Prepared independent native flow helpers')
