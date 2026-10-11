import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ledger = [json.loads(x) for x in (HERE/'browser-command-ledger.jsonl').read_text(encoding='utf-8').splitlines()]
for name in ['browser-matrix','browser-keyboard']:
    rows = [x for x in ledger if any(a.endswith(name+'.js') for a in x['argv'])]
    for index, row in enumerate(rows):
        raw = row['stdout']
        if '### Result\n' not in raw:
            continue
        result = json.JSONDecoder().raw_decode(raw.split('### Result\n',1)[1].lstrip())[0]
        (HERE/f'{name}-{index+1}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
        if name == 'browser-matrix':
            local_failures = [r for r in result['network'] if r['url'].startswith('http://127.0.0.1:8819')]
            print(json.dumps({'run':index+1,'browser':result['browserVersion'],
                'local_failures':len(local_failures),'page_errors':len(result['errors']),
                'rows':[{'language':r['language'],'width':r['width'],'scrollWidth':r['scrollWidth'],
                         'popupRight':r['popup']['right'],'minWidth':r['minWidth']} for r in result['rows']]}))
        else:
            print(json.dumps(result, ensure_ascii=True))
