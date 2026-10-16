"""Durable isolated command recorder; transient raw output stays in ignored own scratch."""
import json,re,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name;name=sys.argv[1];argv=[str(R/'.venv/bin/python'),str(H/'runtime.py'),*sys.argv[2:]]
t=time.monotonic()
with(S/(name+'.raw.log')).open('w')as out:
 p=subprocess.Popen(argv,cwd=R,stdout=out,stderr=subprocess.STDOUT)
 (H/(name+'.running.json')).write_text(json.dumps({'pid':p.pid,'argv':argv}))
 try:code=p.wait(timeout=600)
 except subprocess.TimeoutExpired:p.terminate();code=p.wait(timeout=30)
raw=(S/(name+'.raw.log')).read_text();raw=re.sub(r'(name=[\"\']csrfmiddlewaretoken[\"\']\s+value=[\"\'])[^\"\']+',r'\1[REDACTED]',raw)
(H/(name+'.txt')).write_text(raw);receipt={'name':name,'argv':argv,'exit':code,'seconds':round(time.monotonic()-t,3)}
with(H/'commands.jsonl').open('a')as f:f.write(json.dumps(receipt)+'\n')
(H/(name+'.status.json')).write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt));sys.exit(code)
