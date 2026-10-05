"""Use two valid nearby points in one real district for the refresh regression."""
import ast
from pathlib import Path
p=Path(__file__).resolve().parents[4]/'src/catalog/testcases/owner.py'
s=p.read_text(encoding='utf-8'); lines=s.splitlines(keepends=True)
n=next(n for n in ast.walk(ast.parse(s)) if isinstance(n,ast.FunctionDef) and n.name=='test_owner_edit_form_can_force_refresh_coordinates')
t=''.join(lines[n.lineno-1:n.end_lineno])
for old,new in [('40.111111','40.4093'),('49.111111','49.8671'),('"Ясамал"','"baku_narimanov"'),('"Yasamal"','"baku_narimanov"')]:t=t.replace(old,new)
p.write_text(''.join(lines[:n.lineno-1])+t+''.join(lines[n.end_lineno:]),encoding='utf-8')
