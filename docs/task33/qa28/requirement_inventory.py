"""Inventory literal requirements, without converting old PASS into current evidence."""
import json,re,sys
from pathlib import Path
root=Path(sys.argv[1]);output=Path(sys.argv[2]);rows=[]
for n in range(1,29):
    spec=root/'docs/task33/prompts'/f'{n:02}.md'
    section=None
    for line in spec.read_text(encoding='utf8').splitlines():
        if line.startswith('## '):section=line[3:].strip()
        if section in {'Выполни','Приёмка','Значимые проверки'} and line.startswith('- '):
            rows.append({'id':f'R{n:02}-{sum(r["stage"]==n for r in rows)+1:02}', 'stage':n,'section':section,
                         'requirement':line[2:], 'spec':str(spec.relative_to(root)).replace('\\','/'),
                         'status':'PENDING_CURRENT_EVIDENCE','evidence':[]})
output.write_text(json.dumps({'stage':28,'note':'Literal spec inventory; statuses need current runtime/source/reviewer evidence, not historical PASS.',
                            'requirements':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'requirements':len(rows),'stages':len({r['stage']for r in rows})}))
