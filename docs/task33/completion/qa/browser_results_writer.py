"""Strict fresh all-family result; no retained R1 equivalence permitted."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'docs/task33/completion'
paths=[Path(v) for v in sys.argv[1:]]
assert len(paths)==4
summaries=[json.loads((p/'summary.json').read_text(encoding='utf-8')) for p in paths]
sources=[json.loads((p/'source.json').read_text(encoding='utf-8')) for p in paths]
expected={'r1':357,'specialist':168,'event':273,'targeted':63}
assert {s['family'] for s in summaries}==set(expected)
for s in summaries:
    assert s['status'] in ('PASS','FAIL') and s['contexts']==s['unique_contexts']==s['passed_contexts']==expected[s['family']],s['family']
assert all(s['application']==sources[0]['application'] for s in sources),'All fresh families must execute exactly same APP'
assert all(s['artifact']==sources[0]['artifact'] for s in sources)
current={}
for domain in ('src','templates','static','locale','config','scripts'):
    for p in (ROOT/domain).rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts or p.suffix in ('.pyc','.mo'):continue
        current[p.relative_to(ROOT).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
current['manage.py']=hashlib.sha256((ROOT/'manage.py').read_bytes()).hexdigest()
assert current==sources[0]['application'],'Current APP differs from actual executed common snapshot'
result={'status':'FAIL' if any(s['status']=='FAIL' for s in summaries) else 'PASS','role':'browser-qa (sequential)','executor':'/root',
 'business_and_DOM_checks_all_passed':all(s['checks']==s['passed_checks'] and not s['failed_rows'] for s in summaries),
 'strict_browser_gate':'FAIL' if any(s['status']=='FAIL' for s in summaries) else 'PASS',
 'unexpected_console_or_page_errors':sum(s['event_counts'].get('errors',0) for s in summaries),
 'runtime_error_details':[{'family':s['family'],'errors':json.loads((p/'results.json').read_text(encoding='utf-8'))['events'].get('errors',[])} for s,p in zip(summaries,paths) if s['event_counts'].get('errors')],
 'causal_diagnostic':'Fresh real Program submissions 400/302/409 and standalone taxonomy owner/reviewer lifecycle are included in targeted checks. Failed harness attempts are retained separately.',
 'gallery':'screenshots/index.json','screenshots':30,
 'independence':'Sequential root execution of browser-qa role; not an independent reviewer.',
 'artifact':sources[0]['artifact'],'application_files':len(current),'same_source_all_families':True,'current_application_match':True,
 'base_contexts':798,'additional_targeted_contexts':63,'contexts':sum(s['contexts'] for s in summaries),
 'unique_clean_contexts':sum(s['passed_contexts'] for s in summaries),
 'checks':sum(s['checks'] for s in summaries),'passed_checks':sum(s['passed_checks'] for s in summaries),
 'families':summaries,'retained_browser_evidence_used':False,'R1_bounded_equivalence_used':False,
 'collector_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'not_run':['Production','Production image build/deploy','Physical devices','Full screenreader/contrast audit','Real GoogleMaps/OAuth/CDN/SMTP','Exhaustive all legacy/application paths']}
(OUT/'browser-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ('status','contexts','checks','application_files','same_source_all_families')}))
