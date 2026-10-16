"""Record exact isolated commands and native exits; redact transient CSRF/reset secrets."""
import json,re,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];name=sys.argv[1];argv=[str(R/'.venv/bin/python'),str(H/'runtime.py'),*sys.argv[2:]]
t=time.monotonic();p=subprocess.run(argv,cwd=R,capture_output=True,text=True);raw=p.stdout+p.stderr
raw=re.sub(r'(name=[\"\']csrfmiddlewaretoken[\"\']\s+value=[\"\'])[^\"\']+',r'\1[REDACTED]',raw)
(H/(name+'.txt')).write_text(raw)
with(H/'commands.jsonl').open('a')as f:f.write(json.dumps({'name':name,'argv':argv,'exit':p.returncode,'seconds':round(time.monotonic()-t,3)})+'\n')
print(json.dumps({'name':name,'exit':p.returncode,'seconds':round(time.monotonic()-t,3),'tail':raw[-1400:]}));sys.exit(p.returncode)
