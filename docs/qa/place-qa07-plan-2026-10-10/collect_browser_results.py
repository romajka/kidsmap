"""Source-gap acceptance comparison; retain RED baseline without changing the app."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ledger = [json.loads(line) for line in (HERE/'browser-command-ledger.jsonl').read_text(encoding='utf-8').splitlines()]
row = next(row for row in reversed(ledger) if any(arg.endswith('browser-baseline.js') for arg in row['argv']) and '### Result\n' in row['stdout'])
result = json.JSONDecoder().raw_decode(row['stdout'].split('### Result\n',1)[1].lstrip())[0]
assert row['exit_code'] == 0 and len(result['rows']) == 30
assert not result['errors'] and not result['localFailures']
assert all(row['htmlLanguage'] == row['language'] for row in result['rows'])
(HERE/'browser-baseline.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
expected = {'ru':['Бизнес','Общественное место'],'az':['Biznes','İctimai məkan'],'en':['Business','Public space']}
checks = []
for row in result['rows']:
    assert [option['value'] for option in row['options']] == ['business','public_space']
    for option, label in zip(row['options'], expected[row['language']]):
        checks.append({'language':row['language'],'width':row['width'],'phase':row['phase'],
                       'value':option['value'],'actual':option['text'],'expected':label,'pass':option['text']==label})
checks_result = {'total':len(checks),'passed':sum(row['pass'] for row in checks),
                'failed':sum(not row['pass'] for row in checks),'enum_values_unchanged':True,
                'environment_valid':True,'checks':checks}
(HERE/'browser-assertions.json').write_text(json.dumps(checks_result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({key:value for key,value in checks_result.items() if key!='checks'}))
raise SystemExit(1 if checks_result['failed'] else 0)
