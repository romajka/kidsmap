import json,shutil
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site20-pc-fix-r1'
shutil.copyfile(Q/'fixture-audit.json',O/'evidence/fixture-audit.json')
p=O/'browser-delete-navigation.js';s=p.read_text()
new="if(visible){await link.focus();keyboard=await link.evaluate(e=>document.activeElement===e);await p.keyboard.press('Enter');const confirm=p.getByRole('button',{name:'Да, продолжить',exact:true});await confirm.waitFor({state:'visible'});const next=p.waitForNavigation({waitUntil:'load'});await confirm.click();response=await next;}"
old="if(visible){await link.focus();keyboard=await link.evaluate(e=>document.activeElement===e);const next=p.waitForNavigation({waitUntil:'load'});await p.keyboard.press('Enter');response=await next;}"
assert s.count(new)==1
(O/'initial-harness-failures/delete-navigation-initial.js').write_text(s.replace(new,old))
p=O/'evidence/harness-recovery.json';d=json.loads(p.read_text());d.update(delete_navigation='Initial helper omitted existing unified confirm, so waitForNavigation timed out. Original script/CLI/readonly diagnostic retained. Source+observed active confirm button guided actual modal confirmation step; route/no-write assertions unchanged. Three real correct_route failures remain SITE25.',read_only_diagnostic='A one-off inline PowerShell-quoted log-count diagnostic failed before execution; native form-state/source/fixture verification unaffected. Subsequent native/script diagnostics used saved files.')
p.write_text(json.dumps(d,indent=2))
p=O/'visual-review.json';d=json.loads(p.read_text());d['applied_source_reviewed']+=['save-siteanalytics-360.png','delete-confirm-1440.png'];d['observations']+=['Statistics success notification exceeds360 viewport while own save persists (SITE24)','Delete navigation lands admin index warning for object1/change, no deletion POST (SITE25)'];p.write_text(json.dumps(d,ensure_ascii=False,indent=2))
p=O/'graph-evidence.json';d=json.loads(p.read_text());d['fresh_fix_coverage_check']['templates/admin/catalog/site_analytics.html']='coverage_unavailable / metadata_changed; actual source read: extends base_site, direct SiteAnalytics.changelist_view destination, shared edited template absent';p.write_text(json.dumps(d,indent=2))
print('Read-only fixture audit, original helper failure and current visual/source evidence prepared.')
