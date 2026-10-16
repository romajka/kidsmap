import json,re,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name
name=sys.argv[1];argv=sys.argv[2:];started=time.monotonic();p=subprocess.run(argv,cwd=R,capture_output=True,text=True);raw=p.stdout+p.stderr;(S/(name+'.raw.log')).write_text(raw)
for value in json.loads((S/'credentials.json').read_text()).values():raw=raw.replace(value,'[OWN-SECRET]')
raw=re.sub(r'[0-9a-f]{8}-[0-9a-f-]{27,}','[OWN-ID]',raw,flags=re.I);raw=re.sub(r'([?&]token=)[^\s"<>]+',r'\1[OWN-TOKEN]',raw)
(H/(name+'.output.txt')).write_text(raw);d={'name':name,'argv':argv,'exit':p.returncode,'seconds':round(time.monotonic()-started,3)};(H/(name+'.status.json')).write_text(json.dumps(d,indent=2))
with(H/'commands.jsonl').open('a')as f:f.write(json.dumps(d)+'\n')
print(json.dumps(d));print(raw[-1200:]);sys.exit(p.returncode)
