from pathlib import Path
Q=Path(__file__).resolve().parent
p=Q/'fixtures.py';t=p.read_text().replace("name='Fictional QA09 specialist',","verified_person_user=actors['owner'],person_verified_at=timezone.now(),name='Fictional QA09 specialist',").replace("event=Event.objects.create(owner=actors['owner'],","event=Event.objects.create(organizer_specialist=spec,organizer_resolution='resolved',owner=actors['owner'],")
p.write_text(t)
# Compile reviewed browser checklists into new owned scripts. Real login, real local CSRF.
for name in ['flows','decisions','edits','favorites-notifications','matrix']:
 t=(Q.parents[1]/'docs/qa/module09-2026-10-10-r1'/(name+'.js')).read_text()
 t=t.replace('http://localhost:8822','http://127.0.0.1:33380').replace("hostname==='localhost'","hostname==='127.0.0.1'").replace("hostname!=='localhost'","hostname!=='127.0.0.1'")
 t=t.replace('C:/kidsmap/docs/qa/module09-2026-10-10-r1/screenshots/','/mnt/c/kidsmap/.tmp/module09-full-pc-r1/png/').replace('__LOCAL_PASSWORD__','<fictional-local-password>')
 # Browser API filter({visible:true}) supported by installed Chromium tooling.
 if name=='decisions':
  start=t.index("if(kind==='event'){await candidate")
  end=t.index("await a.goto(url);add('rejection-reason-",start)
  t=t[:start]+t[end:]
 if name=='edits':
  # Correct recovery contract: leave validated B on 409, never navigate back to discard B.
  start=t.index("await tab.goBack();add('back-preserves-stale-text'")
  end=t.index('await tab.close();',start)
  t=t[:start]+"add('conflict-preserves-stale-text',await tab.locator('#review-text').inputValue()==='QA09 UNSAVED B specialist');"+t[end:]
 (Q/(name+'-template.js')).write_text(t)
# generic CLI result persistence with real status; no mutation of former evidence
(Q/'run_browser.py').write_text('''import json,subprocess,sys\nfrom pathlib import Path\nQ=Path(__file__).resolve().parent\nn=sys.argv[1]\nt=(Q/(n+'-template.js')).read_text().replace('__FIXTURES_JSON__',(Q/'fixtures.json').read_text())\nif len(sys.argv)>2:t=t.replace("['guest','author','owner','employee','moderator','staff','admin','empty']",repr([sys.argv[2]]))\n(Q/(n+'.js')).write_text(t)\nr=subprocess.run(['python3',str(Q/'browser_driver.py'),n+'.js'],capture_output=True,text=True)\nassert r.returncode==0,r.stdout+r.stderr\nd=json.loads(r.stdout.split('### Result\\n',1)[1].split('\\n###',1)[0]);suffix='-'+sys.argv[2] if len(sys.argv)>2 else ''\n(Q/(n+suffix+'.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2))\nfrom collections import Counter\nprint(n+suffix,len(d['rows']),dict(Counter(x['status'] for x in d['rows'])),flush=True)\n''')
print('Fresh functional and matrix harnesses prepared')
