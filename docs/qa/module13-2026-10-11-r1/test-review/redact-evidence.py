"""Mask ephemeral CSRF/session values in own assertion traces; outcomes unchanged."""
import json,re,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3]
S=ROOT/'.tmp/module13-20261011-r1/test-review/raw-evidence';S.mkdir(parents=True,exist_ok=True)
counts=json.loads((P/'redaction.json').read_text())['redactions'] if (P/'redaction.json').exists() else {}
patterns=[re.compile(r'((?:name=(?:\\)?["\']csrfmiddlewaretoken(?:\\)?["\'])[^>]{0,160}?value=(?:\\)?["\'])[A-Za-z0-9]{32,128}'),re.compile(r'((?:csrftoken|module13_r1_csrf|module13_r1_session)=)[A-Za-z0-9]{32,128}')]
def clean(text):
    for pattern in patterns:
        text,n=pattern.subn(lambda m:m.group(1)+'[REDACTED EPHEMERAL TOKEN]',text)
        counts['ephemeral_tokens']=counts.get('ephemeral_tokens',0)+n
    return text
def visit(value):
    if isinstance(value,str):return clean(value)
    if isinstance(value,list):return [visit(x) for x in value]
    if isinstance(value,dict):return {k:visit(v) for k,v in value.items()}
    return value
for f in sorted(P.glob('*')):
    if f.name=='redaction.json' or f.suffix not in ('.log','.json','.jsonl'):continue
    # Calling after each completed phase. Never rewrite a running phase's output.
    if f.name.startswith('baseline') and not (P/'baseline-results.json').exists():continue
    if f.name.startswith('baseline-compiled') and not (P/'baseline-compiled-results.json').exists():continue
    raw=f.read_bytes();text=raw.decode('utf-8',errors='replace')
    before=counts.get('ephemeral_tokens',0)
    try:
        if f.suffix=='.json':output=json.dumps(visit(json.loads(text)),indent=2)
        elif f.suffix=='.jsonl':output=''.join(json.dumps(visit(json.loads(line)))+'\n' for line in text.splitlines())
        else:output=clean(text)
    except json.JSONDecodeError:continue
    if counts.get('ephemeral_tokens',0)>before:
        saved=S/f.name
        if not saved.exists():saved.write_bytes(raw)
        f.write_text(output,encoding='utf-8')
        counts[f.name]=counts['ephemeral_tokens']-before
(P/'redaction.json').write_text(json.dumps({'redactions':counts,'preserved_outcomes':True,'raw_own_evidence':'Ignored own scratch only; not a repository artifact'},indent=2))
print(json.dumps(counts))
