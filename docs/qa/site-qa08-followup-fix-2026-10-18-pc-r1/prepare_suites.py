from pathlib import Path
import json
R=Path('/mnt/c/kidsmap');F=R/'docs/qa/site-qa08-fix-2026-10-18-pc-r1';O=R/'docs/qa/site-qa08-followup-fix-2026-10-18-pc-r1';Q=R/'.tmp/site08-pc-followup-r1'
def adapt(s):
 for a,b in [('site08-pc-fix-r1','site08-pc-followup-r1'),('site-qa08-fix-2026-10-18-pc-r1','site-qa08-followup-fix-2026-10-18-pc-r1'),('m10s08_fix_r1','m10s08_followup_r1'),('m10s08-fix-r1','m10s08-followup-r1'),('33580','33590')]:s=s.replace(a,b)
 return s
for n in ['start_server.py','browser_driver.py','static_probe.py','browser-sentinels.js','browser-acceptance-green.js','browser-readonly-green.js','browser-json-error-snapshots.js','browser-file-error-central.js','browser-permissions.js']:
 (O/n).write_text(adapt((F/n).read_text()))
s=adapt((F/'browser-followup-prototype.js').read_text())
start=s.index('const baseline=await measure();');end=s.index("await p.goto(base+'/admin/catalog/sitebrandingsettings/1/change/'",start)
s=s[:start]+'''const geometry=await measure();await p.screenshot({path:O+'/png/__PHASE__-alert-ru-360.png',animations:'disabled'});rows.push({id:'saved-message-ru-360',geometry,checks:{no_document_overflow:geometry.checks.no_document_overflow}});
'''+s[end:]
s=s.replace("scope:'Remaining SITE08 native after-save overflow→temporary followup CSS→exact rollback. Four native same-owned fixture setup/restore writes expected. Followup source NOT APPLIED; no source changes.'", "initial,final:await (await original.request.get(base+'/qa/site08/form-state/')).json(),scope:'Actual source RED/GREEN identical expectations; native four saves; no injection.'")
# The final authenticated read must occur before closing this context.
s=s.replace('await c.close();return{rows', 'const final=await state();await c.close();return{rows').replace("final:await (await original.request.get(base+'/qa/site08/form-state/')).json()",'final')
for phase in ['red','green']:(O/('browser-message-'+phase+'.js')).write_text(s.replace('__PHASE__',phase))
(O/'browser-sentinels-red.js').write_text((O/'browser-sentinels.js').read_text().replace('__PHASE__','red').replace('__SENTINEL_BASELINE__','null'))
(O/'IMPLEMENTATION_PLAN.md').write_bytes((F/'followup/IMPLEMENTATION_PLAN.md').read_bytes());(O/'implemented.diff').write_bytes((F/'followup/proposed.diff').read_bytes())
(O/'candidate-manifest.json').write_bytes((F/'followup/candidate-manifest.json').read_bytes())
print('Prepared native followup scripts, exact approved plan/diff; source unchanged.')
