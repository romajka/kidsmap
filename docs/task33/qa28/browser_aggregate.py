"""Strict final composite with explicit, bounded late EventAdmin reconstruction."""
import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
paths=[Path(value) for value in sys.argv[1:]]
assert len(paths)==3
summaries=[json.loads((path/'summary.json').read_text(encoding='utf-8')) for path in paths]
assert all(item['status']=='PASS' for item in summaries)
assert {item['family'] for item in summaries}=={'r1','specialist','event'}
expected_contexts={'r1':357,'specialist':168,'event':273}
for item in summaries:
    assert item['contexts']==item['unique_contexts']==item['passed_contexts']==expected_contexts[item['family']],item['family']
sources={item['family']:json.loads((path/'source.json').read_text(encoding='utf-8'))
         for item,path in zip(summaries,paths)}
final=sources['event']['application']
assert sources['specialist']['application']==final
current={}
for domain in ('src','templates','static','locale','config','scripts'):
    for p in (ROOT/domain).rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts or p.suffix in ('.pyc','.mo'):continue
        current[p.relative_to(ROOT).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
current['manage.py']=hashlib.sha256((ROOT/'manage.py').read_bytes()).hexdigest()
assert current==final,'Final current APP differs from actually executed Event artifact'
old=sources['r1']['application']
changed=sorted(name for name,value in old.items() if final.get(name)!=value)
added=sorted(set(final)-set(old))
allowed_changes={'src/catalog/domain_admin/place.py':('EventAdminForm','admin-module-before.py'),
                 'src/catalog/forms.py':('OwnerEventForm','owner-forms-before.py')}
assert set(changed)<=set(allowed_changes),changed
assert added in ([],['src/catalog/testcases/test_task33_event_admin_precision.py']),added
reconstruction={'changed_application_files':changed,'new_test_files':added,
 'r1_scope':'EventAdminForm and OwnerEventForm precision methods not called by R1 surfaces; dedicated admin published and owner previously-approved draft precision POSTs checked in final Event family',
 'outside_declared_Event_forms_AST_unchanged':True}
for name in changed:
    class_name,retained_name=allowed_changes[name]
    retained_module=paths[0]/retained_name
    assert hashlib.sha256(retained_module.read_bytes()).hexdigest()==old[name],'Retained old module differs from executed R1 source'
    old_module=ast.parse(retained_module.read_text(encoding='utf-8'))
    new_module=ast.parse((ROOT/name).read_text(encoding='utf-8'))
    def outside_form(module):
        module.body=[node for node in module.body if not isinstance(node,ast.ClassDef) or node.name!=class_name]
        return ast.dump(module,include_attributes=False)
    assert outside_form(old_module)==outside_form(new_module),f'Unreviewed delta outside {class_name}'
contexts=sum(item['contexts'] for item in summaries)
unique=sum(item['unique_contexts'] for item in summaries)
assert contexts==unique==798
result={'stage':28,'status':'PASS','executor':'/root/stage26_public','role':'browser-qa',
 'aggregate_collector_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'execution':'fresh composite R1 plus Specialist/Event at final artifact; independent rendered execution, not independent review of authored27backend',
 'artifact':sources['event']['artifact'],'contexts':contexts,'unique_contexts':unique,
 'checks':sum(item['checks'] for item in summaries),'passed_checks':sum(item['passed_checks'] for item in summaries),
 'languages':['az','ru','en'],'widths':[320,360,390,768,1024,1280,1440],
 'families':summaries,'current_application_files':len(final),'current_application_matches_final_Event':True,
 'source_reconstruction':reconstruction,
 'not_run':['Production','Production image build','Physical devices','Full screenreader','Real GoogleMaps/OAuth/SMTP/CDNs']}
out=ROOT/'docs/task33/reports/28-browser-verification.json'
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','contexts':contexts,'checks':result['checks'],'application_files':len(final),'reconstruction':reconstruction}))
