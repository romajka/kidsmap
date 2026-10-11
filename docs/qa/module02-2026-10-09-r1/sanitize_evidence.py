"""Redact authentication/recovery values from our logs; never touch previous artifacts."""
from pathlib import Path
import re,json
h=Path(__file__).parent;counts={}
for p in h.rglob('*'):
 if not p.is_file() or p.suffix not in {'.txt','.log','.json','.jsonl','.md','.html'}:continue
 s=p.read_text(encoding='utf-8',errors='replace');n=0
 def redact(m):
  global n
  n+=1
  return m[1]+'[REDACTED]'+m[3]
 s=re.sub(r'(<input\b[^>]*name=[\"\'](?:csrfmiddlewaretoken|expected_state)[\"\'][^>]*value=[\"\'])([^\"\']+)([\"\'])',redact,s,flags=re.I)
 s=re.sub(r'((?:[?&]|&amp;)selection=)([^\s\"\'<>]+)()',redact,s)
 if n:p.write_text(s,encoding='utf-8');counts[p.relative_to(h).as_posix()]=n
(h/'redaction-log.json').write_text(json.dumps({'redacted_fields':counts,'note':'Only own logs; no raw token copied into this log. Screenshots have no visible auth fields.'},indent=2),encoding='utf-8')
print('Own files sanitized',len(counts),'field count',sum(counts.values()))
