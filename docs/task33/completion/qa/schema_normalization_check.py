"""Check the exact observed pg_dump deparse change and reject semantic changes."""
import ast,hashlib,json,re
from pathlib import Path
root=Path('/mnt/c/kidsmap/docs/task33/completion')
source=root/'qa/domain_recovery_commands.py'
function=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='canonical_schema')
namespace={'json':json,'re':re}
exec(compile(ast.Module(body=[function],type_ignores=[]),str(source),'exec'),namespace)
canonical=namespace['canonical_schema']
raw=Path('/root/task33-evidence/completion-recovery-c3')
before=json.loads((raw/'schema-qa_stage04.json').read_text())
restored=json.loads((raw/'schema-qa_completion_restore.json').read_text())
assert before!=restored and canonical(before)==canonical(restored)
checks=['observed_equivalent_casts_equal']
for field,change in (
    ('constraints',lambda rows:rows[0].update(definition='PRIMARY KEY (other_id)')),
    ('indexes',lambda rows:rows[0].update(indexdef=rows[0]['indexdef']+' WHERE false')),
    ('columns',lambda rows:rows[0].update(attnotnull=not rows[0]['attnotnull'])),
):
    changed=json.loads(json.dumps(restored));change(changed[field])
    assert canonical(before)!=canonical(changed)
    checks.append('changed_'+field+'_rejected')
changed=json.loads(json.dumps(restored))
row=next(x for x in changed['constraints'] if "'pending'::character varying" in x['definition'])
row['definition']=row['definition'].replace("'pending'::character varying","'denied'::character varying")
assert canonical(before)!=canonical(changed);checks.append('changed_array_value_rejected')
result={'status':'PASS','checks':checks,'checks_count':len(checks),
    'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'raw_differences':{key:sum(a!=b for a,b in zip(before[key],restored[key])) for key in before},
    'source':str(raw),'raw_metadata_preserved':True}
(root/'schema-normalization.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
