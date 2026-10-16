"""Inject only own fixture credentials into an ignored script; redact outputs."""
import json, os, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];SCRATCH=ROOT/'.tmp'/HERE.name
config=json.loads((SCRATCH/'config.json').read_text());secret=json.loads((SCRATCH/'credentials.json').read_text())
fixtures=json.loads((SCRATCH/'fixtures.json').read_text())
body=(HERE/'browser.js').read_text()
for key,value in {'__BASE__':'http://127.0.0.1:'+str(config['http_port']),'__FIXTURES__':fixtures,'__FOLDER__':str(HERE),'__PASSWORD__':secret['admin_password']}.items():
    body=body.replace(key,json.dumps(value))
script=SCRATCH/'browser-private.js';script.write_text(body);os.chmod(script,0o600)
output=subprocess.run(['playwright-cli','-s=ownership-preview-20261014','run-code','--filename',str(script)],capture_output=True,text=True)
text=output.stdout+output.stderr
for value in secret.values():text=text.replace(value,'[REDACTED]')
(HERE/'browser.txt').write_text(text)
if not text.startswith('### Result\n'):raise RuntimeError('Browser harness error; see sanitized browser.txt')
result=json.JSONDecoder().raw_decode(text.split('\n',1)[1])[0]
(HERE/'browser-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'phase':result['phase'],'checks':len(result['rows']),'failures':[r['id'] for r in result['rows'] if r['status']=='FAIL'],'error':result.get('error'),'pageerrors':result['errors'],'network':result['network']}))
if result.get('error') or result['errors'] or result['network']:raise SystemExit(1)
