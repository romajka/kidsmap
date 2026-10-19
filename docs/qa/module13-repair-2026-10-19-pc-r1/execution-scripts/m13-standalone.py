from pathlib import Path
import subprocess,os,json,re,time
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1';rows=[]
files=sorted(list((R/'scripts').glob('test_*.cjs'))+list((R/'static/js/tests').glob('*.test.js'))+list((R/'scripts/tests').glob('*.test.cjs')))
env={'PATH':os.environ['PATH'],'HOME':os.environ['HOME'],'KIDSMAP_JSDOM':str(R/'.tmp/phone-dom/node_modules/jsdom'),'DJANGO_TESTING':'1','PYTHONDONTWRITEBYTECODE':'1'}
for f in files:
 cmd=['npx','--yes','--package','node@24','node','--test',str(f)] if f.name!='test_analytics_sender.cjs' else ['npx','--yes','--package','node@24','node',str(f),str(R)]
 p=subprocess.run(cmd,cwd=R,env=env,capture_output=True,text=True);raw=p.stdout+p.stderr;(Q/(f.name+'.log')).write_text(raw)
 rows.append({'file':f.relative_to(R).as_posix(),'command':cmd,'exit':p.returncode,'TAP_counts':dict(re.findall(r'^# (tests|pass|fail|skipped) (\d+)$',raw,re.M))})
 print(f.name,p.returncode,flush=True)
(O/'evidence/javascript-full.json').write_text(json.dumps(rows,indent=2))
cmd=['python3','-m','unittest','discover','-s',str(R/'scripts/tests'),'-p','test_*.py','-v'];p=subprocess.run(cmd,cwd=R,env=env,capture_output=True,text=True);raw=p.stdout+p.stderr;(Q/'python-standalone.log').write_text(raw)
(O/'evidence/python-standalone.json').write_text(json.dumps({'command':cmd,'exit':p.returncode,'summary':[l for l in raw.splitlines() if l.startswith(('Ran ','OK','FAILED','FAIL:','ERROR:'))]},indent=2));print('Standalone Python',p.returncode,flush=True)
