import json, re, hashlib, csv, subprocess
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path('C:/kidsmap')
OUT = Path(__file__).resolve().parent
QA = ROOT/'docs/qa'
ID = re.compile(r'\b([A-Z]+-QA-\d{2})\b')

def text(p):
    return p.read_text(encoding='utf-8-sig', errors='replace')

def refs(body):
    return list(dict.fromkeys(re.findall(r'(?:src|static|locale|templates|scripts)/[\w./-]+', body)))

def priority(body):
    preferred = [line for line in body.splitlines() if re.search(r'(Severity|Приоритет|Priority|P\d.*OPEN)',line,re.I)]
    for line in preferred + body.splitlines():
        m=re.search(r'P([0-3])(?!\d)', line)
        if m:return 'P'+m.group(1)
    return 'UNKNOWN'

def section_lines(body, pattern):
    return [line.strip() for line in body.splitlines() if re.search(pattern,line,re.I)]

reports=[]; occurrences=[]
for folder in sorted(QA.glob('module*')):
    if not re.match(r'module(?:0[1-9]|1[012])-',folder.name):continue
    report=folder/'REPORT.md'
    if not report.exists():continue
    body=text(report)
    snap=folder/'snapshot.json'
    snapshot=json.loads(text(snap)) if snap.exists() else {}
    counts=folder/'counts.json'
    manifest=folder/'screenshots-manifest.json'
    matrix=folder/'matrix.json'
    matrix_csv=folder/'matrix.csv'
    rows=json.loads(text(matrix)) if matrix.exists() else None
    if isinstance(rows,dict):rows=rows.get('rows',rows.get('matrix',rows.get('observations')))
    if rows is None and matrix_csv.exists():
        with matrix_csv.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    if not isinstance(rows,list):rows=[]
    mcounts=Counter(str(r.get('status','UNKNOWN')) for r in rows if isinstance(r,dict))
    old_files=snapshot.get('source_files',{})
    changed=[];missing=[];same=0
    for file,expected in old_files.items():
        disk=ROOT/file
        if not disk.exists():missing.append(file);continue
        observed=hashlib.sha256(disk.read_bytes()).hexdigest()
        if isinstance(expected,dict):expected=expected.get('sha256',expected.get('hash'))
        if observed==expected:same+=1
        else:changed.append(file)
    reports.append({'run':folder.name,'module':folder.name[6:8], 'report':str(report.relative_to(ROOT)).replace('\\','/'),
        'report_sha256':hashlib.sha256(report.read_bytes()).hexdigest(), 'snapshot_keys':list(snapshot),
        'head':snapshot.get('head',snapshot.get('HEAD',snapshot.get('git',{}).get('head'))),
        'branch':snapshot.get('branch'), 'source_digest':snapshot.get('source_digest',snapshot.get('manifest_digest',snapshot.get('digest'))),
        'snapshot':str(snap.relative_to(ROOT)).replace('\\','/') if snap.exists() else None,
        'counts_file':str(counts.relative_to(ROOT)).replace('\\','/') if counts.exists() else None,
        'matrix_file':str((matrix if matrix.exists() else matrix_csv).relative_to(ROOT)).replace('\\','/') if rows else None,
        'matrix_rows':len(rows), 'matrix_status_counts':dict(mcounts),
        'gaps':section_lines(body,r'NOT RUN|NOT VERIFIED|не провер|неподтверж|недоступн|UNKNOWN'),
        'tests':section_lines(body,r'tests|тест|exit|assertion|FAIL.*PASS'),
        'source_refs':refs(body), 'ids_in_report':sorted(set(ID.findall(body))),
        'summary':body.splitlines()[:4], 'screenshots_manifest':str(manifest.relative_to(ROOT)).replace('\\','/') if manifest.exists() else None,
        'source_comparison_current':{'historical_files':len(old_files),'same':same,'changed':changed,'missing':missing,
            'meaning':'Same recorded file hashes do not make historical runtime/tests fresh; files outside historical manifest remain unrecorded.'}})
    findings=folder/'findings'
    paths=list(findings.glob('*-QA-*.md')) if findings.exists() else []
    for path in sorted(paths):
        raw=text(path); m=ID.search(path.name)
        if not m:continue
        occurrences.append({'id':m.group(1),'module':folder.name[6:8],'run':folder.name,'title':raw.splitlines()[0].lstrip('# ').strip(),
            'severity':priority(raw),'finding':str(path.relative_to(ROOT)).replace('\\','/'),'finding_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'source_refs':refs(raw),'source_cause':section_lines(raw,r'Первопричин|Root cause|Причина|cause:|Гипотез'),
            'role_url':section_lines(raw,r'Роль|Role|URL|endpoint'),
            'dependencies':section_lines(raw,r'зависим|dependenc|Область|Scope'),
            'classification':section_lines(raw,r'baseline|environment|регресс|класс|classification'),
            'repair_prompt_present':'```text' in raw or 'repair' in raw.lower(),
            'evidence_links':re.findall(r'\[[^\]]*\]\(([^)]+)\)',raw)})
    if not paths and (folder/'FINDINGS.md').exists():
        path=folder/'FINDINGS.md';raw=text(path)
        for block in re.split(r'(?m)(?=^## [A-Z]+-QA-\d{2})',raw):
            if not re.match(r'^## [A-Z]+-QA-\d{2}',block):continue
            fid=ID.search(block).group(1)
            occurrences.append({'id':fid,'module':folder.name[6:8],'run':folder.name,'title':block.splitlines()[0].lstrip('# ').strip(),
                'severity':priority(block),'finding':str(path.relative_to(ROOT)).replace('\\','/'),'section_id':fid,'finding_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'source_refs':refs(block),'source_cause':section_lines(block,r'Первопричин|Root cause|Причина|cause:|Гипотез'),
                'role_url':section_lines(block,r'Роль|Role|URL|endpoint'),'dependencies':section_lines(block,r'зависим|dependenc|Область|Scope'),
                'classification':section_lines(block,r'baseline|environment|регресс|класс|classification'),
                'repair_prompt_present':'```text' in block,'evidence_links':re.findall(r'\[[^\]]*\]\(([^)]+)\)',block)})
byid=defaultdict(list)
for f in occurrences:byid[f['id']].append(f)
findings=[]
for fid,series in sorted(byid.items(),key=lambda x:(x[1][-1]['module'],x[0])):
    current=dict(series[-1]);current['historical_occurrences']=series;current['fresh_module13_status']='NOT RUN'
    current['historical_status']='OPEN IN LATEST MODULE REPORT; fresh reproduction required'
    findings.append(current)
payload={'scope':'Historical reconciliation ONLY; no fresh browser/test PASS inferred',
    'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
    'reports':reports,'findings':findings,'raw_finding_occurrences':len(occurrences),'unique_historical_ids':len(findings),
    'severity':dict(Counter(f['severity'] for f in findings)),
    'module_severity':{m:dict(Counter(f['severity'] for f in findings if f['module']==m)) for m in sorted(set(f['module'] for f in findings))}}
(OUT/'historical-findings.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:payload[k] for k in ['raw_finding_occurrences','unique_historical_ids','severity','module_severity']},ensure_ascii=False))
for f in findings:print(f"{f['id']} {f['severity']} {f['title']}")
