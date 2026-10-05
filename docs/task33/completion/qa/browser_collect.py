"""Strict aggregate; retain raw DOM/screenshots only in external evidence."""
import json
import hashlib
import sys
from pathlib import Path

root=Path(sys.argv[1]);family=sys.argv[2]
raw=(root/'result-cli.txt').read_text(encoding='utf-8')
start=raw.find('### Result')
if start<0:raise SystemExit('Result absent; preserve failed harness run')
result=json.loads(raw[start+len('### Result'):].split('###',1)[0].strip())
(root/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
run=json.loads((root/'launcher/run.json').read_text(encoding='utf-8'))
checks=result['checks'];rows=result['rows']
source=json.loads((root/'source.json').read_text(encoding='utf-8'))
runtime_assets={}
assets=dict(result.get('runtimeAssets',{}))
if 'runtimeCss' in result:assets['static/admin/css/pages/kidsmap_admin_form_shell.css']={'status':200,'text':result['runtimeCss']}
for name,value in assets.items():
    actual=hashlib.sha256(value['text'].encode()).hexdigest()
    runtime_assets[name]={'sha256':actual,'matches_frozen':value['status']==200 and actual==source['application'].get(name)}
    checks.append({'check':'runtime_asset_frozen_match','asset':name,'pass':runtime_assets[name]['matches_frozen']})
identities=[(family,row.get('screen',row.get('role')),row.get('actor',row.get('role')),row['lang'],row['width'],row.get('mode','')) for row in rows]
summary={'stage':'completion','family':family,'executor':'/root','role':'browser-qa (sequential)',
 'scope':'fresh Chromium rendered execution; not independent source review of previous authored backend',
 'evidence':str(root),'contexts':len(rows),'unique_contexts':len(set(identities)),
 'passed_contexts':sum(not row['issues'] for row in rows),'checks':len(checks),'passed_checks':sum(bool(c['pass']) for c in checks),
 'failed_rows':[{key:row.get(key) for key in ('screen','role','actor','lang','width','mode','issues')}for row in rows if row['issues']],
 'failed_checks':[c for c in checks if not c['pass']],
 'event_counts':{key:len(values) for key,values in result['events'].items()},
 'launcher_status':run['status'],'cleanup':run['cleanup'],
 'isolation':json.loads((root/'launcher/isolation.json').read_text(encoding='utf-8')),
 'screenshots':sorted(p.name for p in root.glob('*.png')),
 'source_current':json.loads((root/'source-current.json').read_text(encoding='utf-8')),'runtime_assets':runtime_assets}
current=summary['source_current']
failed=summary['failed_rows'] or summary['failed_checks'] or any(result['events'].get(key) for key in ('errors','failed','staticFailures')) or run['status']!='PASS' or run['cleanup']!='PASS' or len(rows)!=len(set(identities)) or current['mismatches'] or current['new_application_files'] or not current['executed_harness_unchanged']
summary['status']='FAIL' if failed else 'PASS'
(root/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=True))
raise SystemExit(bool(failed))
