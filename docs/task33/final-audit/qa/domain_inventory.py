"""Read-only prompt/test source inventory for requirement-level audit."""
import ast
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'docs/task33/final-audit'
old=json.loads((ROOT/'docs/task33/reports/28-requirements.json').read_text(encoding='utf-8'))['requirements']
requirements=[];stages=[]
for stage in range(1,29):
    path=ROOT/f'docs/task33/prompts/{stage:02}.md';text=path.read_text(encoding='utf-8');lines=text.splitlines()
    section='';items=[]
    for line in lines:
        if line.startswith('## '):section=line[3:]
        elif line.startswith('- ') and section in {'Выполни','Приёмка','Значимые проверки'}:
            items.append((section,line[2:]))
    expected=[x for x in old if x['stage']==stage]
    assert [x['requirement'] for x in expected]==[x[1] for x in items],f'Literal requirement drift stage{stage}'
    requirements.extend({'id':row['id'],'stage':stage,'section':row['section'],'text':row['requirement'],
        'old_status_not_adopted':row['status']} for row in expected)
    deps=re.search(r'Зависимости: ([^.]+)\.',text).group(1)
    stages.append({'stage':stage,'title':lines[0].split(': ',1)[1],'dependencies':[int(n) for n in re.findall(r'\d+',deps)],
        'prompt_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'requirements_count':len(items)})
tests=[]
for path in sorted((ROOT/'src/catalog/testcases').glob('*.py')):
    text=path.read_text(encoding='utf-8');tree=ast.parse(text)
    for cls in [n for n in tree.body if isinstance(n,ast.ClassDef)]:
        for fn in cls.body:
            if isinstance(fn,(ast.FunctionDef,ast.AsyncFunctionDef)) and fn.name.startswith('test_'):
                tests.append({'id':f'catalog.testcases.{path.stem}.{cls.name}.{fn.name}',
                    'path':path.relative_to(ROOT).as_posix(),'line':fn.lineno,'end_line':fn.end_lineno})
assert len(requirements)==306 and len(stages)==28
result={'status':'SOURCE_INVENTORY_ONLY_NOT_TEST_PASS','requirements':requirements,'stages':stages,'tests':tests,
        'limitations':['A test name/path alone does not prove an individual requirement; assertion review and attributed current runtime are required.']}
(OUT/'domain-inputs.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'stages':28,'literal_requirements':306,'test_functions':len(tests),'old_status_adopted':False}))
