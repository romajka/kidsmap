"""Combine unaffected168 contexts and strict CSS-only corrected42 contexts."""
import hashlib,json,sys
from pathlib import Path
evidence=Path('/root/task33-evidence');first=evidence/'browser26-final2-20261003';last=evidence/'browser26-admin-final3-20261003'
def result(root):
 raw=(root/'result-cli.txt').read_text().split('### Result',1)[1].split('###',1)[0].strip();return json.loads(raw)
a=result(first);b=result(last);ma=json.loads((first/'source-sha256.json').read_text());mb=json.loads((last/'source-sha256.json').read_text())
application=lambda p:p.startswith(('src/','templates/','static/','locale/','config/','scripts/')) and not p.endswith('.mo')
paths=sorted(p for p in set(ma)|set(mb) if application(p));delta=[p for p in paths if ma.get(p)!=mb.get(p)]
css='static/admin/css/pages/kidsmap_admin_form_shell.css';assert delta==[css],delta
data=(Path('/mnt/c/kidsmap')/css).read_bytes();assert hashlib.sha256(data).hexdigest()==mb[css]
reconstructed=False
for nl in (b'\n',b'\r\n'):
 old_group=nl.join([b'body.model-event .km-place-form-main,',b'body.model-event .km-place-form-sidebar,'])
 new_group=nl.join([b'body.model-event .km-place-form-main,',b'body.model-event .km-place-form-sections,',b'body.model-event .km-place-section,',b'body.model-event .km-place-section__body,',b'body.model-event .km-place-form-sidebar,'])
 block=nl.join([b'body.model-event .km-place-form-shell,',b'body.model-event .km-place-form-main,',b'body.model-event .km-place-form-sections,',b'body.model-event .km-place-section__body {',b'  grid-template-columns: minmax(0, 1fr);',b'}',b'',b''])
 mobile=nl.join([b'  body.model-event .km-place-form-hero {',b'    grid-template-columns: minmax(0, 1fr);',b'  }',b'',b'  body.model-event .km-place-form-hero__progress {',b'    min-width: 0;',b'    max-width: 100%;',b'    box-sizing: border-box;',b'  }',b'',b'  body.model-event .km-lang-tabs {',b'    flex-wrap: wrap;',b'    min-width: 0;',b'    max-width: 100%;',b'  }',b'',b''])
 if data.count(new_group)==1 and data.count(block)==1 and data.count(mobile)==1:
  original=data.replace(new_group,old_group,1).replace(block,b'',1).replace(mobile,b'',1)
  if hashlib.sha256(original).hexdigest()==ma[css]:reconstructed=True
assert reconstructed,'CSS-only late delta is not the scoped expected track rules'
assert hashlib.sha256(b['runtimeCss'].encode()).hexdigest()==mb[css],'Received CSS differs from frozen manifest'
assert all('/root/km26-browser-frozen' in value for value in b['runtime'].values())
rows=[r for r in a['rows'] if r['screen'] not in ('admin','admin_add')]+b['rows'];assert len(rows)==210 and len({(r['screen'],r['lang'],r['width'])for r in rows})==210
checks=[c for c in a['checks'] if c.get('screen') not in ('admin','admin_add') and not c['check'].startswith('admin_')]+b['checks']
assert len(checks)==443
assert all(not r['issues']for r in rows) and all(c['pass']for c in checks)
assert b['total']==42 and b['passed']==42 and len(b['checks'])==b['checksPassed']
for root,d in ((first,a),(last,b)):
 assert not any(d['events'][k]for k in ('errors','failed','staticFailures'))
 run=json.loads((root/'launcher/run.json').read_text());assert run['status']=='PASS' and run['cleanup']=='PASS' and run['run_root_removed'] and run['socket_root_removed']
sourcecheck=json.loads((last/'source-current-check.json').read_text());assert not sourcecheck['mismatches'] and not sourcecheck['new_application_files']
summary={'stage':26,'status':'PASS','execution_identity':'/root/stage26_browser','role':'browser-qa','head':'015d031d8eb17114bd860159dde805b38df3c13c','snapshot':'dirty WORKTREE; composite of two independent frozen runs, not one latest210 run','languages':['az','ru','en'],'widths':[320,360,390,768,1024,1280,1440],'current_distinct_contexts':210,'passed_contexts':210,'current_checks':443,'passed_checks':443,'unaffected_contexts_from_full_final2':168,'corrective_contexts_from_admin_final':42,'corrective_focus_tab_checks':84,'corrective_total_checks':len(b['checks']),'corrective_passed_checks':b['checksPassed'],'application_source_files_compared':len(paths),'application_delta':delta,'late_delta_is_only_expected_Event_scoped_track_rule':reconstructed,'source_current_check':sourcecheck,'full_final2_evidence':str(first),'corrective_evidence':str(last),'source_fingerprints':{'full_final2':hashlib.sha256((first/'source-sha256.json').read_bytes()).hexdigest(),'corrective':hashlib.sha256((last/'source-sha256.json').read_bytes()).hexdigest()},'runtime_paths':b['runtime'],'received_css_sha256':hashlib.sha256(b['runtimeCss'].encode()).hexdigest(),'errors':0,'request_failures':0,'static_failures':0,'current_overflow_contexts':0,'cleanup':'PASS bothruns','browser':'cached real Chromium via Playwright CLI','external_transport':'External integrations/CDNs stubbed; cached font served locally','not_run':['Production','Real external integrations','Physical device/full screen-reader audit','Full application suite by this browser executor','Stage27 calendar UI','Deploy/commit/push']}
Path(sys.argv[1]).write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:summary[k]for k in ['status','current_distinct_contexts','current_checks','corrective_total_checks','application_delta','late_delta_is_only_expected_Event_scoped_track_rule']}))
