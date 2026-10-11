"""Behavioral assertions against the fresh rendered evidence, no source edits."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
matrix = json.loads((HERE/'browser-matrix-2.json').read_text(encoding='utf-8'))
keyboard = json.loads((HERE/'browser-keyboard-2.json').read_text(encoding='utf-8'))
assert matrix['environmentValid'] and not matrix['errors']
assert len(matrix['rows']) == 18 and len(keyboard['rows']) == 3
checks = []
for row in matrix['rows']:
    checks.append({'id':f"overflow-{row['language']}-{row['width']}",
        'pass':row['scrollWidth'] <= row['viewport']+1 and row['popup']['right'] <= row['viewport']+1,
        'scrollWidth':row['scrollWidth'],'viewport':row['viewport']})
for row in keyboard['rows']:
    checks.extend([
        {'id':f"open-focus-{row['language']}",'pass':row['opened']['tag']=='INPUT'},
        {'id':f"tab-{row['language']}",'pass':'km-pf-picker-item' in row['tab']['className']},
        {'id':f"shift-tab-{row['language']}",'pass':row['shiftTab']['tag']=='INPUT'},
        {'id':f"escape-results-{row['language']}",'pass':row['escape']['expanded']=='false' and row['escape']['focus']['className']=='km-pf-picker-btn'},
        {'id':f"selection-focus-{row['language']}",'pass':row['select']['value']=='QA05_LONG' and row['select']['focus']['className']=='km-pf-picker-btn'},
        {'id':f"escape-empty-{row['language']}",'pass':row['emptyEscape']['expanded']=='false' and row['emptyEscape']['focus']['className']=='km-pf-picker-btn'},
    ])
result = {'checks':checks,'total':len(checks),'passed':sum(c['pass'] for c in checks),
          'failed':sum(not c['pass'] for c in checks),'environment_valid':True,
          'long_labels_clipped':sum(r['longLabel']['scrollWidth'] > r['longLabel']['clientWidth']+1 for r in matrix['rows'])}
(HERE/'baseline-assertions.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k != 'checks'}))
raise SystemExit(1 if result['failed'] else 0)
