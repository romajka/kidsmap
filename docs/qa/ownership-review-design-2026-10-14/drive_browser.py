"""Use the preceding task's own isolated stand; never print fixture secrets."""
import json,os,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
SCRATCH=ROOT/'.tmp/ownership-preview-fix-2026-10-14'
config=json.loads((SCRATCH/'config.json').read_text());secrets=json.loads((SCRATCH/'credentials.json').read_text())
fixtures=json.loads((SCRATCH/'fixtures.json').read_text())
body=(HERE/'browser.js').read_text()
for name,value in {'__BASE__':'http://127.0.0.1:'+str(config['http_port']),'__FIXTURES__':fixtures,'__FOLDER__':str(HERE),'__PASSWORD__':secrets['admin_password']}.items():body=body.replace(name,json.dumps(value))
private=SCRATCH/'review-design-private.js';private.write_text(body);os.chmod(private,0o600)
process=subprocess.run(['playwright-cli','-s=review-design-20261014','run-code','--filename',str(private)],capture_output=True,text=True,timeout=180)
output=process.stdout+process.stderr
for value in secrets.values():output=output.replace(value,'[REDACTED]')
(HERE/'browser.txt').write_text(output)
if not output.startswith('### Result\n'):raise RuntimeError('Browser execution error; see sanitized browser.txt')
result=json.JSONDecoder().raw_decode(output.split('\n',1)[1])[0]
(HERE/'browser-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'phase':result['phase'],'checks':len(result['rows']),'error':result.get('error'),'errors':result['errors'],'network':result['network'],'writes':result['writes']}))
if result.get('error') or result['errors'] or result['network'] or result['writes'] or any(r['status']=='FAIL' for r in result['rows']):raise SystemExit(1)
