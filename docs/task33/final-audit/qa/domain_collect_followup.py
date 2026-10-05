import json,shutil,hashlib
from pathlib import Path
ROOT=Path('/mnt/c/kidsmap');OUT=ROOT/'docs/task33/final-audit'
src=Path('/tmp/task33-qa-domain-cross-stage-r5-20261004')
dst=Path('/root/task33-evidence/final-audit-domain-cross-stage-20261004/r5')
shutil.copytree(src,dst)
data=json.loads((OUT/'domain-results.json').read_text());run=json.loads((src/'run.json').read_text());suite=json.loads((src/'suite-results.json').read_text())
data['prior_final_r4']={'suite':data['suite-results.json'],'observations':data['domain-observations.json']}
data['attempts'].append({'attempt':'r5','raw':str(dst),'run_status':run['status'],'cleanup':run['cleanup'],'child_exit':run['child_exit'],'tests_run':suite['tests_run'],'failures':suite['failures'],'errors':suite['errors'],'adapter_issue':None,'purpose':'additional causal audience facts probe'})
data['suite-results.json']=suite;data['domain-observations.json']=json.loads((src/'domain-observations.json').read_text())
data['run.json']={k:run[k] for k in ('status','child_exit','cleanup','network','ports_published','postgres_data','mounted_checkout','run_root_removed','socket_root_removed')}
data['command']=data['command'].replace('-r4-','-r5-');data['scope']='6 new external QA-only probes; APP1817 unchanged'
data['helper_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (OUT/'qa').rglob('domain*.py')}
(OUT/'domain-results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
failure=json.loads((OUT/'domain-failure-classification.json').read_text())
for e in failure['entries']:
    if '.adult_classes.PlaceAdultClassesPublicTests.' in e['id']:
        e['status']='CONFIRMED_PRESENTATION_EXPECTATION_DEBT_FACTS_RETAINED'
        e['reason']='Новый causalprobe воспроизвёл оба oldassertion failures. Currentcatalog содержиткороткийВзрослые, detail200содержит6–17 иВзрослыегруппы. Меняетсяexactstring/unitsplacement, age/adultfactsнеутрачены. ЭтоnativeHTTPtext,неполныйrenderedvisualproof.'
        e['evidence']='domain-results.json:domain-observations.json.legacy_audience'
        e['confidence']='HIGH_SOURCE_PLUS_CAUSAL_LOCAL_HTTP'
        e['observation']=data['domain-observations.json']['legacy_audience']
(OUT/'domain-failure-classification.json').write_text(json.dumps(failure,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'tests':suite['tests_run'],'failures':suite['failures'],'errors':suite['errors'],'cleanup':run['cleanup'],'audience':data['domain-observations.json']['legacy_audience']},ensure_ascii=False))
