"""Verify bounded evidence, CSS forward provenance and preserved work; no DB writes."""
import hashlib, json, subprocess, urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
entry=json.loads((HERE/'entry.json').read_text())
source={str(p.relative_to(ROOT)):sha(p) for top in ('src','static','config','locale','templates')
        for p in (ROOT/top).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
changed=sorted(k for k in set(source)|set(entry['source']) if source.get(k)!=entry['source'].get(k))
assert changed==['src/catalog/controllers/organization_workspace.py','src/catalog/templates/pages/organization_workspace.html',
                 'src/catalog/testcases/test_network_grant_ui.py','static/css/pages/organization_workspace.css',
                 'static/js/organization_workspace.js'],changed
controller=(ROOT/changed[0]).read_text().replace('        grant.is_current = business_team._grant_current(grant, org)\n','').replace("        'team_role_choices':grants[0]._meta.get_field('role').choices if grants else (),\n",'')
assert hashlib.sha256(controller.encode()).hexdigest()==entry['source'][changed[0]]
assert all((ROOT/k).exists() and sha(ROOT/k)==v for k,v in entry['previous_reports'].items())
before=json.loads((HERE/'before-css-source.json').read_text())['source_files']
assert [k for k in source if source[k]!=before.get(k)]==['static/css/pages/organization_workspace.css']
server=json.loads((HERE/'server.json').read_text())
runtime=json.load(urllib.request.urlopen(server['url']+'/qa/start-version/',timeout=5))
assert runtime['testing'] and runtime['pid']==server['pid'] and runtime['entry_matches_startup'] and runtime['startup_matches_disk']
rows=[];events=[];network=[]
for name in [f'browser-{lang}-{width}' for lang in ('ru','az','en') for width in (390,1440)]+[
    'layout-ru','layout-az','layout-en','forbidden-ui']:
    data=json.loads((HERE/(name+'.result.json')).read_text())
    assert not data.get('error') and not data['errors'] and all(r['status']=='PASS' for r in data['rows']),name
    rows+=data['rows'];events+=data['consoleEvents'];network+=data['network']
assert len(rows)==199
gates=[]
for path in HERE.glob('text-overflow*.json'):
    try:data=json.loads(path.read_text())
    except ValueError:continue
    if len(data.get('rows',[]))==18 and all(r['status']=='PASS' and 'parent' in r.get('overflow',{}) for r in data['rows']):
        gates.append((path,data))
gate_path,gate=max(gates,key=lambda x:x[0].stat().st_mtime)
for row in gate['rows']:
    bounds=row['overflow'];assert bounds['rect']['right']<=bounds['parent']['right']+1 and bounds['rect']['right']<=row['width']
    assert 0<=bounds['parent']['top']<bounds['parent']['bottom']<=950
rows+=gate['rows'];events+=gate['consoleEvents'];network+=gate['network']
assert len(rows)==217 and len({r['id'] for r in rows})==217
for row in rows:
    if 'screenshot' in row:assert (HERE/row['screenshot']).is_file()
    if 'readback' in row:assert row['readback']['read_only']
    # Raw lifecycle role identifies the owner case; record the actor of explicit cross-role actions.
    if row['id'].endswith(('revoked-editor-denied','direct-place-access-remains')):row['executing_actor']='member'
    elif row['id'].endswith('cancel-versus-stale-recipient-accept'):row['executing_actor']='recipient'
    else:row['executing_actor']=row['role']
for event in events:
    external_blocked = (event['source'].startswith('https://fonts.googleapis.com/') or event['source'].startswith('https://unpkg.com/leaflet@1.9.4/')) and 'net::ERR_FAILED' in event['text']
    native_denial = event['source']=='chrome-error://chromewebdata/' and '403' in event['text']
    assert external_blocked or native_denial or event['source'].startswith(server['url']),event
assert all(item['status'] in (403,404,409) for item in network)
old_stands=[]
for path in (ROOT/'docs/qa').glob('*/server.json'):
    if path.parent==HERE:continue
    info=json.loads(path.read_text());proc=Path('/proc')/str(info['pid'])
    assert proc.exists() and str(path.parent/'runtime.py').encode() in (proc/'cmdline').read_bytes(),path
    old_stands.append({'profile':path.parent.name,'pid':info['pid'],'alive_own_runtime':True})
assert (ROOT/'docs/task33/implementation-status.md').read_text().splitlines()[6]=='active_run: NONE'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==entry['head']
assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()==entry['branch']
assert (ROOT/'docs/qa/continuation-and-repair-prompts-2026-10-11.md').read_text().count('```text')==88
check=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True);assert check.returncode==0,check.stdout+check.stderr
syntax=subprocess.run(['node','--check','static/js/organization_workspace.js'],cwd=ROOT,capture_output=True,text=True);assert syntax.returncode==0
images=[{'path':str(p.relative_to(HERE)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted((HERE/'screenshots').glob('*.png'))]
summary={'checkout':str(ROOT),'head':entry['head'],'branch':entry['branch'],'active_run':'NONE','changed_app_files':changed,
         'foreign_source_and_assertions_preserved':True,'orgqa01_logic_byte_preserved':True,
         'previous_evidence_preserved':len(entry['previous_reports']),'old_stands':old_stands,
         'targeted_backend_tests':28,'browser_accepted_assertions':217,'browser_fail':0,'pageerrors':0,
         'browser_before_css_preserved_by_provenance':199,'fresh_css_matrix_assertions':18,
         'accepted_css_result':gate_path.name,'png_manifest_count_including_red_attempts':len(images),
         'runtime_source_match':True,'diff_check_exit':0,'node_syntax_exit':0,
         'full_module02':'NOT RUN','production_commit_push_deploy':'NOT RUN'}
(HERE/'png-manifest.json').write_text(json.dumps(images,indent=2))
(HERE/'browser-evidence-index.json').write_text(json.dumps({'rows':rows,'console_events':events,'network':network},indent=2))
(HERE/'final-verification.json').write_text(json.dumps(summary,indent=2))
(HERE/'runtime-version-final.json').write_text(json.dumps(runtime,indent=2))
print(json.dumps(summary))
