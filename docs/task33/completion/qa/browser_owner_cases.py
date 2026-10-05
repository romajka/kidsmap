import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
problems=json.loads(Path('/root/task33-evidence/completion-frontend-owner-red-20261004/suite-results.json').read_text())['problems']
source=(ROOT/'src/catalog/testcases/owner.py').read_text()
names={p['id'].split('.')[-1].split(' ')[0] for p in problems if '.owner.' in p['id']}
for node in ast.walk(ast.parse(source)):
    if not isinstance(node,ast.FunctionDef) or node.name not in names:continue
    lines=source.splitlines()[node.lineno-1:node.end_lineno]
    start=next((i for i,line in enumerate(lines) if 'self.assert' in line),len(lines))
    print('\n'+node.name+'\n'+'\n'.join(lines[start:]))
