from pathlib import Path
import re,json
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1';raw=(Q/'full-r1.log').read_text();rows=[]
for m in re.finditer(r'^(FAIL|ERROR): ([^\n]+)\n-+\n(.*?)(?=\n=+\n|\n-+\nRan \d+|\Z)',raw,re.M|re.S):
 kind,name,body=m.groups();refs=re.findall(r'File "(/mnt/c/kidsmap/[^"\n]+)", line (\d+)',body);ex=re.findall(r'^([\w.]+(?:Error|Exception|Denied)): (.*)$',body,re.M);message=ex[-1][1] if ex else '';message=message.split('<')[0].split("b'")[0][:180]
 assert re.fullmatch(r'test_\S+ \([A-Za-z0-9_.]+\)',name)
 guard=('requires QA04 isolated settings' in body or 'requires isolated QA04 settings' in body or 'test_m13full_complete_r1' in message or "startswith('/tmp/kidsmap-task33-qa04-'" in body or 'TASK33_NOTIFICATION_CRASH_TESTS' in body or 'TASK33_QA_ROOT' in body)
 rows.append({'kind':kind,'name':name,'source_refs':refs[-4:],'exception':ex[-1][0] if ex else None,'guard_hint':guard,'safe_exception_summary':message if guard else 'Exception details retained only in ignored own raw log; inspect source references.'})
(O/'evidence/full-failure-classification-input.json').write_text(json.dumps(rows,indent=2))
for row in rows:print(json.dumps(row))
ids=set(re.findall(r'test_\S+ \((catalog\.[^)]+)\)',raw));d=json.loads((O/'evidence/full-backend-r1.json').read_text());d['all_observed_unique_ids']=sorted(ids);d['all_observed_unique_count']=len(ids);(O/'evidence/full-backend-observed-ids.json').write_text(json.dumps({'ids':sorted(ids),'unique':len(ids),'note':'Includes all method starts including command stdout interleaving; compare discovery IDs, not line prefix only.'},indent=2))
