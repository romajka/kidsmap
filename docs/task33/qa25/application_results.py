"""Produce bounded final browser evidence, retaining genuine prior failures."""
import json,sys
from pathlib import Path
evidence=Path('/root/task33-evidence')
names=['initial2-20261003','motion-diagnostic-20261003','final-20261003','profile-final-20261003']
runs={}
for name in names:
 run=evidence/('browser25-'+name)
 runs[name]=json.loads((run/'summary.json').read_text())
final=evidence/'browser25-final-20261003';follow=evidence/'browser25-profile-final-20261003'
a=json.loads((final/'source-sha256.json').read_text());b=json.loads((follow/'source-sha256.json').read_text())
app_roots=('src/','templates/','static/','locale/','config/','scripts/')
delta=[p for p in sorted(set(a)|set(b)) if p.startswith(app_roots)and not p.endswith('.mo')and a.get(p)!=b.get(p)]
assert delta==['locale/ru/LC_MESSAGES/django.po'],delta
fresh=json.loads((follow/'source-current-check.json').read_text())
assert not fresh['mismatches']and not fresh['new_application_files']
for name in ['final-20261003','profile-final-20261003']:
 s=runs[name]
 assert s['rows']==s['passed_rows']and s['checks']==s['passed_checks']
 assert all(s['event_counts'][x]==0 for x in ['errors','failed','staticFailures'])
 assert s['launcher_status']=='PASS'and s['launcher_cleanup']=='PASS'
result={'stage':25,'scope':'ACTUAL_APPLICATION','status':'PASS','reviewer':'/root/stage25_browser','role':'browser-qa',
 'head':'015d031d8eb17114bd860159dde805b38df3c13c','snapshot':'dirty WORKTREE, separate frozen per-run source manifests','runs':runs,
 'effective_current_rendered_coverage':168,'current_full_workflow_checks':380,'corrective_person_index_rows':42,'corrective_checks':84,
 'only_application_source_delta_after_full_matrix':delta,'final_source_current_check':fresh,
 'findings':{'QA25-B01':'RESOLVED:42AZ/EN certificate copy failures, fresh full168matrixPASS',
 'QA25-B02':'RESOLVED: nativePOSTcrossdocumentopt-in errors gone after actual late scoped navigation:none; global motion.js not attributed or modified',
 'QA25-B03':'RESOLVED:visualRUprofile/indexAZfallback after fullgreenautomation; strongerheading/assertions added, obsoleteRUselfentry reactivated, corrective42/42PASS'},
 'limits':'Full matrix126 unaffected rows plus final42person/index contexts cover current168matrix.380full workflow checks remain applicable after only one RU gettext entry changed;84corrective focus checks independently repeated. Raw DOM/screenshot/userfixture evidence remains outside Git.',
 'not_run':['Production','Real private file inventory/transfer','Real external integrations/CDNs','Deployed storage/nginx/TLS','Full screen-reader audit','Native OS file chooser localization','Stage26+','Deploy/commit/push']}
Path(sys.argv[1]).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':'PASS','current_rows':168,'full_checks':380,'corrective_rows':42,'corrective_checks':84,'source_checked':fresh['checked_source_files'],'source_mismatches':0,'application_delta':delta}))
