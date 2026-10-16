"""PLAN-only own HTTP/cache/locales; reuse verified fictional owned PostgreSQL profile."""
import hashlib,json,secrets,shutil,socket,subprocess,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];OLD=H.parent/'social-qa02-fix-2026-10-16-r1';S=R/'.tmp'/H.name;OS=R/'.tmp'/OLD.name
assert json.loads((OLD/'verification.json').read_text())['decision']=='SOCIAL-QA-02 CLOSED LOCAL'
oldmeta=json.loads((OLD/'server.json').read_text());oldsource=json.load(urllib.request.urlopen(oldmeta['url']+'/qa/source/'));baseline=json.loads((OLD/'runtime-source-green-tests.json').read_text());assert oldsource['source']==baseline and oldsource['startup_matches_disk'] and oldsource['pid']==oldmeta['pid']
cfg=json.loads((OS/'config.json').read_text());inspection=json.loads(subprocess.check_output(['docker','inspect',cfg['container']],text=True))[0];assert inspection['Config']['Labels']['kidsmap.qa.run']==OLD.name and inspection['State']['Running']
assert inspection['NetworkSettings']['Ports']['5432/tcp']==[{'HostIp':'127.0.0.1','HostPort':str(cfg['pg_port'])}]
(H/'reuse-profile.json').write_text(json.dumps({'owner':OLD.name,'same_task_owned_profile':True,'container':cfg['container'],'pg_port':cfg['pg_port'],'database':cfg['database'],'source_match_files':len(baseline),'old_http_pid':oldmeta['pid'],'new_own_http_cache_media_locales':True,'reuse_reason':'Targeted new bug reproduction uses unused fictional repeat actor; completed SOCIAL02 actors/current/public projection untouched'},indent=2))
for name in ['capture.py','runtime.py','settings.py','qa_urls.py','run_command.py','source-paths.json','fixtures.json']:
 text=(OLD/name).read_text().replace(OLD.name,H.name).replace('APPROVED SOCIAL-QA-02','PLAN SOCIAL-QA-03').replace('test_social02_fix_r1','test_social03_recheck_r1').replace('social02fixr1','social03recheckr1');(H/name).write_text(text)
subprocess.run(['python3',str(H/'capture.py')],cwd=R,check=True)
(H/'index-entry.json').write_text(json.dumps({'sha256':hashlib.sha256((R/'.git/index').read_bytes()).hexdigest()}))
secret=json.loads((OS/'credentials.json').read_text());secret['django_secret']=secrets.token_urlsafe(48);(S/'credentials.json').write_text(json.dumps(secret));(S/'credentials.json').chmod(0o600)
with socket.socket()as sock:sock.bind(('127.0.0.1',0));cfg['http_port']=sock.getsockname()[1]
(S/'config.json').write_text(json.dumps(cfg));shutil.copytree(OS/'python-deps',S/'python-deps')
(H/'runtime-source-baseline.json').write_text(json.dumps(baseline,indent=2));py=str(R/'.venv/bin/python')
def run(name,args):subprocess.run(['python3',str(H/'run_command.py'),name,*args],cwd=R,check=True)
run('locales-build',[py,'scripts/build_isolated_locales.py','build','--output',str(S/'locales'),'--locales','ru','az','en','--compiler','native'])
run('locales-verify',[py,'scripts/build_isolated_locales.py','verify','--manifest',str(S/'locales/manifest.json')]);(H/'locale-manifest.json').write_bytes((S/'locales/manifest.json').read_bytes())
run('runtime-info',[py,str(H/'runtime.py'),'runtime-info'])
a=[py,str(H/'runtime.py'),'serve']
with(S/'server.log').open('ab')as log:p=subprocess.Popen(a,cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
meta={'pid':p.pid,'argv':a,'url':f"http://127.0.0.1:{cfg['http_port']}",'container':cfg['container'],'pg_port':cfg['pg_port']};(H/'server.json').write_text(json.dumps(meta,indent=2))
for _ in range(100):
 try:
  source=json.load(urllib.request.urlopen(meta['url']+'/qa/source/',timeout=2));assert source['pid']==p.pid and source['source']==baseline and source['startup_matches_disk'];break
 except Exception:time.sleep(.2)
else:raise RuntimeError('Own HTTP not ready')
(H/'runtime-source-start.json').write_text(json.dumps(source,indent=2))
print(json.dumps({'pid':p.pid,'source':len(baseline),'http_port':cfg['http_port'],'DB':'verified owned synthetic profile reuse; no seed/migrate'}))
