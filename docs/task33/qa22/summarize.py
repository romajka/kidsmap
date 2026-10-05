"""Extract actual CLI result and retain summary outside Git."""
import json
import sys
from pathlib import Path
root=Path(sys.argv[1])
raw=(root/'result-cli.txt').read_text()
mark=raw.find('### Result')
if mark<0:raise RuntimeError('No actual browser result; inspect retained CLI output')
result,_=json.JSONDecoder().raw_decode(raw[raw.find('{',mark):])
(root/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
summary={key:value for key,value in result.items() if key not in ('rows','events')}
if 'rows'in result:
 failed=[row for row in result['rows'] if row.get('issues') or row.get('pass') is False or ('pass' not in row and row.get('status',200)!=200)]
 summary['failures']=[{key:value for key,value in row.items() if key in ('actor','lang','kind','width','status','issues','check','pass','scrollWidth','viewport')}for row in failed]
if 'events'in result:
 summary['events']={key:len(value)for key,value in result['events'].items()}
(root/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False))
