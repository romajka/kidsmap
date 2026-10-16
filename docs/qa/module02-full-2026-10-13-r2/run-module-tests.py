import json,re,subprocess,time
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];S=R/'.tmp'/P.name
labels=json.loads((P/'test-labels.json').read_text());secret=json.loads((S/'credentials.json').read_text())
args=[str(R/'.venv/bin/python'),str(P/'runtime.py'),'test']+labels
start=time.monotonic();q=subprocess.run(args,capture_output=True,text=True);out=q.stdout+q.stderr
for v in secret.values():out=out.replace(v,'[REDACTED]')
out=re.sub(r'(name=[\"\']csrfmiddlewaretoken[\"\'] value=[\"\'])[^\"\']+',r'\1[REDACTED]',out)
(P/'module-tests.txt').write_text(out)
counts=re.search(r'Ran (\d+) tests?',out);data={'argv':args,'exit':q.returncode,'seconds':round(time.monotonic()-start,2),'count':int(counts[1]) if counts else None,'result':'module-tests.txt'}
(P/'module-tests.json').write_text(json.dumps(data,indent=2))
with (P/'commands.jsonl').open('a') as f:f.write(json.dumps(data)+'\n')
print(json.dumps(data));raise SystemExit(q.returncode)
