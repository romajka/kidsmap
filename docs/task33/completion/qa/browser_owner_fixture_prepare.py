"""One-time bounded legacy test fixture migration; no application files."""
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
path=ROOT/'src/catalog/testcases/owner.py'
source=path.read_text(encoding='utf-8')
lines=source.splitlines(keepends=True)
changes=[]
for node in ast.walk(ast.parse(source)):
    if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Attribute) or node.func.attr!='post' or not node.args:
        continue
    route=node.args[0]
    if not isinstance(route,ast.Call) or not route.args or not isinstance(route.args[0],ast.Constant) or route.args[0].value!='owner_place_edit':
        continue
    args=next((k.value for k in route.keywords if k.arg=='args'),None)
    data=next((k.value for k in node.keywords if k.arg=='data'),node.args[1] if len(node.args)>1 else None)
    if not isinstance(args,ast.List) or not isinstance(data,ast.Dict) or any(isinstance(k,ast.Constant) and k.value=='publication_token' for k in data.keys):continue
    ident=args.elts[0]
    if not isinstance(ident,ast.Attribute) or ident.attr not in ('pk','id'):continue
    place=ast.get_source_segment(source,ident.value)
    if data.lineno==data.end_lineno:
        line=lines[data.lineno-1];pos=data.col_offset+1
        lines[data.lineno-1]=line[:pos]+f'"publication_token": version_token({place}), '+line[pos:]
    else:
        changes.append((data.lineno,' '* (data.col_offset+4)+f'"publication_token": version_token({place}),\n'))
for index,line in sorted(changes,reverse=True):lines.insert(index,line)
source=''.join(lines)
if 'from catalog.services.publication_forms import version_token' not in source:
    source=source.replace('import json\n','import json\nfrom catalog.services.publication_forms import version_token\n',1)
path.write_text(source,encoding='utf-8')
print(f'Added signed source token to {len(changes)} multiline edit fixture payloads; direct-call one-line additions included.')
