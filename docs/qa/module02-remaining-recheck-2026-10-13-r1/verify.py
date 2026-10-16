import hashlib,json,subprocess,urllib.request
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
e=json.loads((P/'entry.json').read_text());now={str(f.relative_to(R)):sha(f) for top in ('src','static','config','locale','templates') for f in (R/top).rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc'}
assert now==e['source'];assert all(sha(R/k)==v for k,v in e['previous_reports'].items())
assert 'active_run: NONE' in (R/'docs/task33/implementation-status.md').read_text()
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==e['head']
server=json.loads((P/'server.json').read_text());runtime=json.load(urllib.request.urlopen(server['url']+'/qa/start-version/',timeout=5));assert runtime['entry_matches_startup'] and runtime['startup_matches_disk']
d=json.loads((P/'layout-probe-refined.result.json').read_text());assert len(d['rows'])==36 and all(x['status']=='PASS' for x in d['rows'])
subprocess.run(['git','diff','--check'],check=True)
manifest=[{'path':str(f.relative_to(P)),'sha256':sha(f),'bytes':f.stat().st_size} for f in sorted((P/'screenshots').glob('*.png'))];(P/'png-manifest.json').write_text(json.dumps(manifest,indent=2))
out={'application_and_existing_tests_unchanged':True,'previous_report_files_preserved':len(e['previous_reports']),'active_run':'NONE','head':e['head'],'branch':e['branch'],'runtime_source_match':True,'temporary_css_probe':{'cases':36,'pass':36,'acceptance':False},'png_count':len(manifest),'full_ACCEPT02':'NOT RUN','implementation':'NOT RUN','diff_check_exit':0}
(P/'verification.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
