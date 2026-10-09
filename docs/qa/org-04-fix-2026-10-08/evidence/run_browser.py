import subprocess,json,sys
from pathlib import Path
s=Path(__file__).parent;name=sys.argv[1]
r=subprocess.run(['playwright-cli','-s=org04-fix-20261008','run-code',(s/(name+'.js')).read_text()],capture_output=True,text=True)
(s/(name+'.log')).write_text(r.stdout+r.stderr)
try:
 data=json.loads(r.stdout.split('### Result\n',1)[1].split('\n### Ran Playwright code',1)[0]);(s/(name+'.json')).write_text(json.dumps(data,indent=2))
 print({'script':name,'PASS':sum(x['status']=='PASS' for x in data['rows']),'FAIL':[x for x in data['rows'] if x['status']!='PASS'],'pageerrors':len(data.get('errors',[])),'network':len(data.get('network',[]))})
except Exception as e: print({'script':name,'parse_error':str(e),'exit':r.returncode,'tail':r.stdout[-400:]})
