import re,json,ast
from pathlib import Path
ROOT=Path('/mnt/c/kidsmap');OUT=ROOT/'docs/task33/final-audit'
old=json.loads((ROOT/'docs/task33/reports/28-full-results.json').read_text())
groups={p['id']:p['classification'] for p in old['classification']['remaining_problem_entries']}
log=Path('/root/task33-evidence/final-audit-full-20261004/django.log').read_text()
inventory=json.loads((OUT/'domain-inputs.json').read_text())
tests={t['id']:t for t in inventory['tests']}
results=[]
for block in re.split(r'\n={30,}\n',log):
    hit=re.search(r'^(FAIL|ERROR): (test_\w+) \((catalog\.[^)]+)\)([^\n]*)',block)
    if not hit:continue
    id=hit[3];group=groups.get(id)
    frames=re.findall(r'File "([^"\n]+)", line (\d+), in ([^\n]+)\n\s+([^\n]+)',block)
    last=next((f for f in reversed(frames) if '/catalog/testcases/' in f[0]),None)
    exception=next((l for l in block.splitlines() if l.startswith(('AssertionError:','KeyError:','catalog.models.','django.core.'))),'')
    info=tests.get(id);body=''
    if info:
        lines=(ROOT/info['path']).read_text().splitlines();body='\n'.join(lines[info['line']-1:info['end_line']])
    results.append({'id':id,'kind':hit[1],'subtest':hit[4].strip(),'old_hint':group,
        'assert_source':{'path':last[0].split('/src/')[-1] if last else None,'line':int(last[1]) if last else None,'statement':last[3] if last else None},
        'observed_exception':exception[:250],'test_body':body})
Path('/root/task33-evidence/final-audit-domain-cross-stage-20261004/failure-source-traces.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print(json.dumps([{k:v for k,v in row.items() if k!='test_body'} for row in results if row['old_hint'] not in {'SIGNED_CANDIDATE','OPTIONAL_MEDIA_COORDS_CONTACT'}],ensure_ascii=False))
