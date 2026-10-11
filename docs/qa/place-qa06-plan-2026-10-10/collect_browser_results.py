"""Read CLI results and assert rendered strings against current PO source."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ledger = [json.loads(line) for line in (HERE/'browser-command-ledger.jsonl').read_text(encoding='utf-8').splitlines()]
row = next(row for row in reversed(ledger) if any(a.endswith('browser-baseline.js') for a in row['argv']) and '### Result\n' in row['stdout'])
result = json.JSONDecoder().raw_decode(row['stdout'].split('### Result\n',1)[1].lstrip())[0]
assert row['exit_code']==0 and len(result['rows'])==6
assert not result['errors'] and result['localResourceFailures']==0
assert all(r['htmlLanguage']==r['language'] for r in result['rows'])
(HERE/'browser-baseline.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
comparison = json.loads((HERE/'catalog-comparison.json').read_text(encoding='utf-8'))
source = {(r['language'],r['msgid']):r['source_translation'] or r['msgid'] for r in comparison['rows']}
checks = []
for row in result['rows']:
    actual = {f'Описание ({lang.upper()})':value for lang,value in row['labels'].items()}
    actual.update({'Карта пока не активна':row['mapTitle'].removesuffix('.'),
        'Геокодирование не настроено. Заполните GOOGLE_MAPS_API_KEY, чтобы рассчитывать координаты прямо из формы.':row['mapMessage']})
    for key,value in actual.items():
        expected = source[(row['language'],key)]
        checks.append({'language':row['language'],'phase':row['phase'],'msgid':key,
            'expected':expected,'actual':value,'pass':value==expected})
assertions = {'total':len(checks),'passed':sum(r['pass'] for r in checks),
    'failed':sum(not r['pass'] for r in checks),'checks':checks,'environment_valid':True}
(HERE/'browser-assertions.json').write_text(json.dumps(assertions,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in assertions.items() if k!='checks'}))
raise SystemExit(1 if assertions['failed'] else 0)
