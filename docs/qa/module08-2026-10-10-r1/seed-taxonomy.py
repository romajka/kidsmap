"""New synthetic lookup only. No update to a previously audited object."""
import sys,json
sys.argv=['run.py','qa-extra-taxonomy'];from run import *
from catalog.models import SpecialistSpecialization
assert not (HERE/'extra-taxonomy.json').exists()
assert SpecialistSpecialization.objects.count()==0
x=SpecialistSpecialization.objects.create(code='qa08-fictional-direction',name='Synthetic QA08 direction',name_ru='Synthetic QA08 direction RU',name_az='Uydurma QA08 istiqamet',name_en='Fictional QA08 direction EN')
(HERE/'extra-taxonomy.json').write_text(json.dumps({'new_initial_only':True,'specialization':x.pk,'reason':'Initial QA seed had no specialization options. Adds new fictional lookup; does not set specialist relation or change profile.'}),encoding='utf-8');print('New fictional lookup created; specialist unchanged')
