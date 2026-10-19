from pathlib import Path
Q=Path(__file__).resolve().parent
p=Q/'run_browser.py';t=p.read_text();at=t.index('n=sys.argv[1]');t=t[:at]+'''if len(sys.argv)>2 and sys.argv[1]=='matrix' and sys.argv[2] in ['moderator','staff','admin','empty']:
 print('Matrix '+sys.argv[2]+' assigned to separate owned browser session; no result claimed here',flush=True)
 raise SystemExit(0)
'''+t[at:];p.write_text(t)
(Q/'secondary_driver.py').write_text((Q/'browser_driver.py').read_text().replace('-s=module09-full-pc-r1','-s=module09-full-pc-r1-secondary'))
(Q/'secondary.py').write_text('''import json,subprocess,sys\nfrom pathlib import Path\nfrom collections import Counter\nQ=Path(__file__).resolve().parent\nrole=sys.argv[1];name='matrix-'+role\nt=(Q/'matrix-template.js').read_text().replace('__FIXTURES_JSON__',(Q/'fixtures.json').read_text()).replace("['guest','author','owner','employee','moderator','staff','admin','empty']",repr([role]))\n(Q/(name+'.js')).write_text(t)\nr=subprocess.run(['python3',str(Q/'secondary_driver.py'),name+'.js'],capture_output=True,text=True)\nassert r.returncode==0,r.stdout+r.stderr\nd=json.loads(r.stdout.split('### Result\\n',1)[1].split('\\n###',1)[0]);(Q/(name+'.json')).write_text(json.dumps(d,indent=2,ensure_ascii=False))\nprint(name,len(d['rows']),dict(Counter(x['status'] for x in d['rows'])),flush=True)\n''')
(Q/'secondary.sh').write_text('''#!/bin/sh
set -eu
qa=/mnt/c/kidsmap/.tmp/module09-full-pc-r1
python3 "$qa/secondary_driver.py" open http://127.0.0.1:33380/ru/reviews/ --config="$qa/playwright.json"
for role in moderator staff admin empty; do
 python3 "$qa/secondary.py" "$role"
done
''')
print('Four role batches assigned to second owned browser session; source and fixture transitions unchanged')
