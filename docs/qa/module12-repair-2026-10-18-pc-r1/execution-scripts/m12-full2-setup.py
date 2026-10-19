import json,shutil,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m12-full-r1';O=R/'docs/qa/module12-repair-2026-10-18-pc-r1';old=json.loads((O/'evidence/final-backend.json').read_text());assert old['exit']==0 and len(old['test_ids'])==583
for name in ['final-backend.json','final-backend-source.json','final-current-labels.json']:shutil.copyfile(O/'evidence'/name,O/'evidence'/name.replace('final-','before-read-beacon-'))
for db in ['m12full_r2']:
 assert subprocess.check_output(['docker','exec','m12-full-r1-pg','psql','-p','55493','-U','m12_guard','-d','postgres','-Atc',"SELECT count(*) FROM pg_database WHERE datname='"+db+"'"],text=True).strip()=='0';subprocess.run(['docker','exec','m12-full-r1-pg','createdb','-p','55493','-U','m12_guard',db],check=True)
(Q/'qa_full2_settings.py').write_text("from qa_settings import *\nDATABASES['default']['NAME']='m12full_r2'\nDATABASES['default']['TEST']['NAME']='test_m12full_r2'\n")
t=(Q/'runtime.py').read_text().replace("else 'qa_settings'","else 'qa_full2_settings'").replace("settings.DATABASES['default']['NAME'] == 'm12full_r1'","settings.DATABASES['default']['NAME'] == 'm12full_r2'");assert 'qa_full2_settings' in t;(Q/'runtime_full2.py').write_text(t)
config=json.loads((Q/'config.json').read_text());config['database']='m12full_r2';(Q/'config.json').write_text(json.dumps(config))
t=(R/'.tmp/m12-full-tests.py').read_text();t=t.replace("name='test_m12full_r1'","name='test_m12full_r2'").replace("str(Q/'runtime.py')","str(Q/'runtime_full2.py')").replace("Q/'full-test-r1.log'","Q/'full-test-r2.log'");t=t.replace("['ingress','reporting','localization','payload','acceptance']","['ingress','reporting','localization','payload','acceptance','read_failure']");(R/'.tmp/m12-full-tests-r2.py').write_text(t);print('Fresh full2 guarded base/profile prepared; normal fixtureDB unchanged,583-method result retained.')
