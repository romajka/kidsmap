from pathlib import Path
import subprocess,json,sys
S=Path(__file__).parent;n=sys.argv[1]
r=subprocess.run(['playwright-cli','-s=place-acceptance-8792','run-code',(S/(n+'.js')).read_text()],capture_output=True,text=True)
(S/(n+'.log')).write_text(r.stdout+r.stderr)
try:
 x=json.loads(r.stdout.split('### Result\n',1)[1].split('\n### Ran Playwright code',1)[0]);(S/(n+'.json')).write_text(json.dumps(x,indent=2,ensure_ascii=False));print(json.dumps({'script':n,'PASS':sum(a.get('status')=='PASS' for a in x.get('rows',[])),'FAIL':[a for a in x.get('rows',[]) if a.get('status')!='PASS'],'error':x.get('error'),'entities':x.get('entities')},ensure_ascii=False))
except Exception as e:print(r.stdout[-2000:],r.stderr[-1000:]);raise
