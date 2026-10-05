"""Inspect only synthetic local browser result aggregates while source check runs."""
import json
import sys
from collections import Counter
from pathlib import Path

p=Path(sys.argv[1]);raw=(p/'result-cli.txt').read_text(encoding='utf-8')
result=json.loads(raw.split('### Result',1)[1].split('###',1)[0].strip())
print(json.dumps({'rows':len(result['rows']),'passed':result['passed'],
 'row_issues':Counter(issue for row in result['rows'] for issue in row['issues']),
 'failed_checks':[c for c in result['checks'] if not c['pass']],
 'events':{k:({'count':len(v),'samples':v[:4]} if k in ('errors','failed','staticFailures') else len(v)) for k,v in result['events'].items()},
 'first_failed_row':next((r for r in result['rows'] if r['issues']),None)},ensure_ascii=True))
