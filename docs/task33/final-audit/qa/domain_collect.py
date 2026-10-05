"""Retain disposable audit evidence; repository contains aggregate JSON only."""
import json,shutil,hashlib
from pathlib import Path
ROOT=Path('/mnt/c/kidsmap');OUT=ROOT/'docs/task33/final-audit'
retained=Path('/root/task33-evidence/final-audit-domain-cross-stage-20261004')
retained.mkdir(exist_ok=False)
attempts=[]
for suffix in ('','-r2','-r3','-r4'):
    src=Path('/tmp/task33-qa-domain-cross-stage'+suffix+'-20261004')
    dst=retained/('first' if not suffix else suffix[1:]);shutil.copytree(src,dst)
    run=json.loads((src/'run.json').read_text());suite=json.loads((src/'suite-results.json').read_text())
    attempts.append({'attempt':suffix or 'first','raw':str(dst),
        'run_status':run['status'],'cleanup':run['cleanup'],'child_exit':run['child_exit'],
        'tests_run':suite['tests_run'],'failures':suite['failures'],'errors':suite['errors'],
        'adapter_issue':'missing legacy Client' if not suffix else ('missing setUpTestData' if suffix=='-r2' else None)})
src=Path('/tmp/task33-qa-domain-cross-stage-r4-20261004')
safe={k:json.loads((src/k).read_text()) for k in ('suite-results.json','isolation.json','migrations.json','checks.json','domain-observations.json')}
run=json.loads((src/'run.json').read_text());safe['run.json']={k:run[k] for k in ('status','child_exit','cleanup','network','ports_published','postgres_data','mounted_checkout','run_root_removed','socket_root_removed')}
safe.update({'executor':'/root/stage28_database sequential django-reviewer','scope':'5 new external QA-only probes; existing APP assertions unchanged',
    'attempts':attempts,'production':'NOT_CONTACTED','mirror':'/root/km-final-domain',
    'command':'wsl -d Ubuntu-24.04 -u root --exec /root/kidsmap-task33/.venv/bin/python /mnt/c/kidsmap/docs/task33/final-audit/qa/domain_run.py --mode probe --output /tmp/task33-qa-domain-cross-stage-r4-20261004',
    'helper_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (OUT/'qa').rglob('domain*.py')},
    'source_mirror_matches_current':{p:((ROOT/p).read_bytes()==(Path('/root/km-final-domain')/p).read_bytes()) for p in ('src/catalog/services/catalog_search.py','src/catalog/services/pricing_plans.py','src/catalog/services/organization_ownership.py','src/catalog/domain_admin/place.py','src/catalog/forms.py')},
    'canonical_full':'1817/109F11E and Task33 579/580 attributed /root; these5 not added to APP suite'})
(OUT/'domain-results.json').write_text(json.dumps(safe,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'own_cases':safe['suite-results.json']['tests_run'],'status':run['status'],'cleanup':run['cleanup'],'mirror_match':all(safe['source_mirror_matches_current'].values()),'raw':str(retained)}))
