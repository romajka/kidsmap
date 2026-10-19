import json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m12-full-r1';O=R/'docs/qa/module12-repair-2026-10-18-pc-r1'
t=(Q/'seed.py').read_text().replace("codename='view_catalogcontentsettings'","codename='view_siteanalytics'");(Q/'seed.py').write_text(t)
t=(Q/'qa_settings.py').read_text();t+="\nMIDDLEWARE=['qa_simulation.SimulationMiddleware']+list(MIDDLEWARE)\n";(Q/'qa_settings.py').write_text(t)
(Q/'simulation.json').write_text(json.dumps({'report':'disabled','storage':'healthy'}))
t=(Q/'qa_urls.py').read_text();t=t.replace("'media':media}","'media':media}")
t=t.replace("'media':media})","'media':media,'events_total':__import__('catalog.models',fromlist=['FunnelEvent']).FunnelEvent.objects.count(),'event_counts':list(__import__('catalog.models',fromlist=['FunnelEvent']).FunnelEvent.objects.values('event_type').annotate(total=__import__('django.db.models',fromlist=['Count']).Count('id'))),'simulation':__import__('qa_simulation').COUNTERS})")
(Q/'qa_urls.py').write_text(t)
settings=json.loads((Q/'playwright.json').read_text());settings['browser']['contextOptions']['userAgent']='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36';(Q/'playwright.json').write_text(json.dumps(settings))
cmd=['docker','exec','m12full-r1-app','python',str(Q/'seed.py')];p=subprocess.run(cmd,capture_output=True,text=True);(Q/'seed.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr[-300:]
cmd=['docker','exec','-d','m12full-r1-app','sh','-c','exec python '+str(Q/'runtime.py')+' serve > '+str(Q/'server.log')+' 2>&1'];subprocess.run(cmd,check=True)
(O/'evidence/native-setup.json').write_text(json.dumps({'fixture':'fresh fictional seed, view_siteanalytics viewer and denied staff','port':33780,'browser':'installed Chromium, headless; human desktop UA emulated to test bot-exclusion separately','external_provider':'disabled by default; named report states explicitly SIMULATED; never authenticates Google','storage_fault':'named SIMULATED actual repository DatabaseError','native_actions':'normal product elements; QA login helper for isolated actors'},indent=2));print('Own Module12 fixture/server ready; provider and fault adapters explicitly SIMULATED.')
