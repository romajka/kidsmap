"""Sanitized actual-application QA summary; raw DOM/screenshots remain outside Git."""
import hashlib
import json
import sys
from pathlib import Path

root=Path(sys.argv[1]); raw=(root/'result-cli.txt').read_text()
start=raw.find('### Result')
if start<0:raise SystemExit('Browser result absent; inspect isolated external evidence')
payload=raw[start+len('### Result'):].split('###',1)[0].strip()
result=json.loads(payload)
(root/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
run=json.loads((root/'launcher/run.json').read_text())
summary={'stage':25,'scope':'ACTUAL_APPLICATION','execution_identity':'/root/stage25_browser','role':'browser-qa',
 'head':'015d031d8eb17114bd860159dde805b38df3c13c','snapshot':'dirty WORKTREE frozen in own allowlisted mirror',
 'evidence':str(root),'browser':'Chromium via cached Playwright CLI','languages':['az','ru','en'],'widths':[320,360,390,768,1024,1280,1440],
 'rows':result['total'],'passed_rows':result['passed'],'checks':len(result['checks']),'passed_checks':result['checksPassed'],
 'failed_rows':[{k:r[k] for k in ('screen','actor','lang','width','issues')}for r in result['rows']if r['issues']],
 'failed_checks':[c for c in result['checks']if not c['pass']],
 'event_counts':{k:len(v)for k,v in result['events'].items()},
 'screenshots':sorted(p.name for p in root.glob('*.png')),
 'executed_matrix_sha256':hashlib.sha256((root/'matrix.js').read_bytes()).hexdigest(),
 'source_manifest_sha256':hashlib.sha256((root/'source-sha256.json').read_bytes()).hexdigest(),
 'source_file_count':len(json.loads((root/'source-sha256.json').read_text())),
 'launcher_status':run['status'],'launcher_cleanup':run['cleanup'],'isolation':json.loads((root/'launcher/isolation.json').read_text()),
 'external_transport':result['externalTransport'],
 'not_run':['Production','Real external integrations/CDNs','Real records/private file inventory','Full screen reader audit','Stage26+','Deployment']}
if len(sys.argv)>2:Path(sys.argv[2]).write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False))
if result['total']!=result['passed']or len(result['checks'])!=result['checksPassed']or any(result['events'][k]for k in ['errors','failed','staticFailures'])or run['status']!='PASS'or run['cleanup']!='PASS':raise SystemExit(1)
