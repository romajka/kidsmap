"""Sanitize and capture exact own-runtime commands and native exits."""
import json,subprocess,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;S=P.parents[2]/'.tmp'/P.name
name=sys.argv[1];args=sys.argv[2:];sec=json.loads((S/'credentials.json').read_text());start=time.monotonic()
q=subprocess.run(args,capture_output=True,text=True);out=q.stdout+q.stderr
for v in sec.values():out=out.replace(v,'[REDACTED]')
(P/(name+'.txt')).write_text(out)
result={'argv':args,'exit':q.returncode,'seconds':round(time.monotonic()-start,3)}
(P/(name+'.json')).write_text(json.dumps(result,indent=2))
with (P/'commands.jsonl').open('a') as f:f.write(json.dumps(result)+'\n')
import re
print(json.dumps(result));print('\n'.join(s[:240] for s in out.splitlines() if re.match('^(FAIL:|ERROR:|Ran |FAILED|OK|Found|System check)',s)))
sys.exit(q.returncode)
