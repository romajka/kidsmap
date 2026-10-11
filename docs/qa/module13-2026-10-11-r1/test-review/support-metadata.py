import hashlib,json,pathlib,runpy,subprocess,sys
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[3];QA=P.parent
snapshot=json.loads((QA/'snapshot.json').read_text())
current={rel:hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() for rel in snapshot['source_files']}
untracked=ROOT/'src/catalog/testcases/test_task33_place_nature_localization.py'
donor=ROOT/'.tmp/module13-20261011-r1/test-review/head-donor'
copy=donor/untracked.relative_to(ROOT)
copy.write_bytes(untracked.read_bytes())
baseline=json.loads((P/'baseline-source.json').read_text())
baseline['supplemental_test_sources']=[{'path':untracked.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(untracked.read_bytes()).hexdigest(),'origin':'Foreign untracked WORKTREE test copied unchanged only for same-test comparison; HEAD application sources remain unchanged; pristine HEAD discovery evidence predates supplement'}]
(P/'baseline-source.json').write_text(json.dumps(baseline,indent=2),encoding='utf-8')
sys.argv=[str(QA/'run.py'),'audit-bootstrap'];runpy.run_path(str(QA/'run.py'),run_name='__qa_bootstrap__')
import django
from django.db import connection,transaction
with transaction.atomic():
    with connection.cursor() as cursor:
        cursor.execute('SET TRANSACTION READ ONLY');cursor.execute("SET LOCAL statement_timeout='5s'")
        cursor.execute('SELECT version(),current_database()');pg,db=cursor.fetchone()
meta={'source_files_verified':len(current),'source_unchanged_since_parent_snapshot':current==snapshot['source_files'],'source_digest':hashlib.sha256(json.dumps(current,sort_keys=True).encode()).hexdigest(),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),'active_run':next(x.split(':',1)[1].strip() for x in (ROOT/'docs/task33/implementation-status.md').read_text().splitlines() if x.startswith('active_run:')),'python':sys.version.split()[0],'django':django.get_version(),'node':subprocess.check_output(['C:/Program Files/nodejs/node.exe','--version'],text=True).strip(),'postgresql':pg,'metadata_connection_database':db,'metadata_transaction':'READ ONLY;5s timeout','graph':'C-kidsmap ready; metadata_changed on cited paths, direct source verified; no graph completeness claim'}
(P/'metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
print(json.dumps(meta,indent=2))
