import json,collections
from pathlib import Path
OUT=Path('/mnt/c/kidsmap/docs/task33/final-audit')
browser=json.loads((OUT/'browser-results.json').read_text())
families=[]
for family in browser['families']:
    raw=Path(family['evidence'])/'results.json';data=json.loads(raw.read_text())
    screens=collections.defaultdict(list)
    for row in data['rows']:screens[row.get('screen',row.get('role','UNKNOWN'))].append(row)
    scopes={name:{'contexts':len(rows),'languages':sorted({r.get('lang','UNKNOWN') for r in rows}),
                  'widths':sorted({r.get('width',0) for r in rows}),
                  'http_statuses':sorted({r.get('status',0) for r in rows})} for name,rows in screens.items()}
    checks=[{k:c[k] for k in ('check','name','id','screen','role','lang','width','status','ok','passed','pass') if k in c} for c in data['checks']]
    families.append({'family':family['family'],'raw':str(raw),'screens':scopes,'checks':checks,
                     'status':family['status'],'event_counts':family['event_counts'],'cleanup':family['cleanup']})
result={'executor_attribution':browser['executor'],'artifact':browser['artifact'],'strict_gate':browser['strict_browser_gate'],
        'contexts':browser['contexts'],'checks':browser['checks'],'passed_checks':browser['passed_checks'],
        'errors':browser['runtime_error_details'],'families':families,
        'limitations':'Native/DOM checks passing do not prove every browser clause; viewtransition unexpected pageerror is retained. InitialOrg/Program/Activity display fixtures use ORM, no complete publication flow claim.'}
(OUT/'domain-browser-evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps([{'family':f['family'],'check_count':len(f['checks']),'check_names':sorted({c.get('check','UNKNOWN') for c in f['checks']})} for f in families],ensure_ascii=False))
