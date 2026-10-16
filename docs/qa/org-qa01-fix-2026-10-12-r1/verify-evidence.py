"""Validate scope, native results, provenance and preservation without changing app data."""
import hashlib, json, subprocess, urllib.request
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
entry=json.loads((HERE/'entry.json').read_text())
current={str(p.relative_to(ROOT)):sha(p) for top in ('src','static','config','locale','templates')
         for p in (ROOT/top).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
changed=sorted(p for p in set(current)|set(entry['source']) if current.get(p)!=entry['source'].get(p))
assert changed==['src/catalog/controllers/organization_workspace.py','src/catalog/testcases/test_org_qa01_autosave_base.py'], changed
previous=all((ROOT/p).exists() and sha(ROOT/p)==h for p,h in entry['previous_reports'].items())
assert previous
server=json.loads((HERE/'server.json').read_text())
version=json.load(urllib.request.urlopen(server['url']+'/qa/start-version/',timeout=5))
assert version['testing'] and version['pid']==server['pid'] and version['entry_matches_startup'] and version['startup_matches_disk']
old=[]
for path in sorted((ROOT/'docs/qa').glob('*/server.json')):
    if path.parent==HERE:
        continue
    data=json.loads(path.read_text())
    proc=Path('/proc')/str(data['pid'])
    matches=proc.exists() and str(path.parent/'runtime.py').encode() in (proc/'cmdline').read_bytes()
    assert matches, path
    old.append({'profile':path.parent.name,'pid':data['pid'],'alive_own_source':True})
rows=[]; errors=[]; expected_network=[]; console_environment=[]
for lang in ('ru','az','en'):
    for width in (390,1440):
        result=HERE/f'browser-{lang}-{width}.result.json'
        data=json.loads(result.read_text())
        assert data.get('error') is None and len(data['rows'])==16 and not data['errors'], result
        assert all(row['status']=='PASS' for row in data['rows']), result
        assert len(data['network'])==1 and data['network'][0]['status']==409, result
        assert all(row['lang']==lang and row['width']==width for row in data['rows'])
        focus=next(row['focus'] for row in data['rows'] if 'focus' in row)
        assert focus['rect']['left']>=0 and focus['rect']['right']<=width
        assert 0<=focus['rect']['top']<focus['rect']['bottom']<=950
        for event in data['consoleEvents']:
            assert event['source'].startswith('https://fonts.googleapis.com/') or (
                event['source'].startswith(server['url']) and '/api/drafts/' in event['source']
                and '409' in event['text']), event
        for row in data['rows']:
            if 'screenshot' in row:
                assert (HERE/row['screenshot']).is_file()
            if 'readback' in row:
                assert row['readback']['read_only']
                assert row['readback']['controller_source']==str(ROOT/'src/catalog/controllers/organization_workspace.py')
                assert row['readback']['controller_hash']==current['src/catalog/controllers/organization_workspace.py']
        rows.extend(data['rows']);expected_network.extend(data['network']);console_environment.extend(data['consoleEvents'])
assert len({row['id'] for row in rows})==96
images=[{'path':str(path.relative_to(HERE)),'bytes':path.stat().st_size,'sha256':sha(path)}
        for path in sorted((HERE/'screenshots').glob('*.png'))]
assert len(images)==42
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
assert head==entry['head'] and branch==entry['branch']
assert (ROOT/'docs/task33/implementation-status.md').read_text().splitlines()[6]=='active_run: NONE'
assert (ROOT/'docs/qa/continuation-and-repair-prompts-2026-10-11.md').read_text().count('```text')==88
check=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
assert check.returncode==0, check.stdout+check.stderr
summary={'checkout':str(ROOT),'head':head,'branch':branch,'active_run':'NONE','changed_app_files':changed,
         'existing_source_and_tests_preserved':True,'previous_report_files':len(entry['previous_reports']),
         'previous_reports_preserved':previous,'old_stands_preserved':old,'browser_unique_assertions':96,
         'browser_pass':96,'browser_fail':0,'pageerrors':0,'expected_conflict_responses':len(expected_network),
         'blocked_external_fonts':True,'png_count':42,'source_runtime_match':True,
         'git_diff_check_exit':check.returncode,'production':'NOT RUN','full_module02':'NOT RUN'}
(HERE/'png-manifest.json').write_text(json.dumps(images,indent=2))
(HERE/'browser-evidence-index.json').write_text(json.dumps({'rows':rows,'expected_network':expected_network,'console_events':console_environment},indent=2))
(HERE/'final-verification.json').write_text(json.dumps(summary,indent=2))
(HERE/'runtime-version-final.json').write_text(json.dumps(version,indent=2))
print(json.dumps(summary))
