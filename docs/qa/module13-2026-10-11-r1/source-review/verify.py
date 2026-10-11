"""Artifact/source-preservation verification only, not application tests."""
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path('C:/kidsmap')
OWN = Path(__file__).resolve().parent
data = json.loads((OWN/'inventory.json').read_text(encoding='utf-8'))
changed = [p for p, digest in data['snapshot']['source_hashes'].items()
           if not (ROOT/p).exists() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest() != digest]
syntax = []
for p in OWN.glob('*.py'):
    ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
    syntax.append(p.name)
broken = []
for p in OWN.glob('*.md'):
    for ref in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if not re.match(r'^(https?:|#)',ref) and not (p.parent/ref.split('#')[0]).exists():
            broken.append({'file':p.name,'link':ref})
head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
active = re.search(r'^active_run:\s*(.+)$',(ROOT/'docs/task33/implementation-status.md').read_text(encoding='utf-8'),re.M).group(1)
result = dict(kind='artifact_and_source_verification_only',application_tests='NOT_RUN_BY_THIS_AGENT',
    head_match=head==data['snapshot']['head'],active_run_match=active==data['snapshot']['active_run'],
    checked_source_files=len(data['snapshot']['source_hashes']),changed_source_files=changed,
    own_python_ast=syntax,broken_markdown_links=broken,
    counts={'route_declarations':len(data['routes']),'admin_route_declarations':len(data['admin_routes']),
            'model_class_candidates':len(data['models']),'admin_registration_declarations':len(data['admin_surfaces']),
            'historical_reports_read':len(data['history'])})
result['exit_code'] = 0 if result['head_match'] and result['active_run_match'] and not changed and not broken else 1
(OWN/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
raise SystemExit(result['exit_code'])
