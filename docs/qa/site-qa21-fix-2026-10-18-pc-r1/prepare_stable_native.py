import json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent
needle="await p.locator('#catalogcontentsettings_form').waitFor();"
extra=needle+"await p.waitForLoadState('load');await p.waitForFunction(()=>!document.body.classList.contains('hold-transition'));await p.waitForTimeout(350);"
for phase in ['red','green']:
 old=(O/('browser-acceptance-'+phase+'.js')).read_text();assert old.count(needle)==1
 updated=old.replace(needle,extra).replace('return{root_width:rootRect.width,','return{body_classes:document.body.className,root_max_width:getComputedStyle(root).maxWidth,root_width:rootRect.width,')
 if phase=='red':updated=updated.replace("'/png/red-acceptance-'","'/png/stable-red-acceptance-'")
 target='browser-acceptance-stable-red.js' if phase=='red' else 'browser-acceptance-green.js'
 (O/target).write_text(updated)
proof={'initial_native_rows':36,'initial_checks':360,'initial_pass':305,'initial_fail':55,'same12desktop_overlaps':True,'difference_from_PLAN':'One viewer/RU768 row measured380px/root380 rather than PLAN row624/root467.9. Isolated readonly repeat immediate/350ms reports624/467.9 and max1200px; no source or fixture changes. Exact triggering timing is qualified, consistent with responsive sidebar initialization.','refinement':'Wait for native load/hold-transition removal and350ms before measuring, identically RED/GREEN; record body classes/max-width. All original check definitions retained; initial data/PNGs retained.','diagnostic':'evidence/browser-width-diagnostic.json','application_changes':0,'no_class_style_injection':True}
(O/'native-stability-refinement.json').write_text(json.dumps(proof,indent=2));print('Native responsive-layout readiness added identically; all geometry/control checks retained')
