from pathlib import Path
O=Path(__file__).resolve().parent
s=(O/'browser-prototype.js').read_text().replace("login/super/","login/viewer/").replace("['sitebrandingsettings','siteaboutsettings','sitecontactssettings','sitefootersettings','siteemptystatesettings','sitevisibilitysettings','siteanalytics','catalogcontentsettings','sitegalleryimage']","['catalogcontentsettings']").replace("classList.add('km-settings-form-page','km-settings-form-page--editable','col-12')","classList.add('km-settings-form-page','col-12')").replace(".filter(visible).length===2",".filter(visible).length===(innerWidth<=760?0:2)").replace("'/png/baseline-'","'/png/viewer-baseline-'").replace("'/png/prototype-'","'/png/viewer-prototype-'")
(O/'browser-readonly-prototype.js').write_text(s)
s=(O/'browser-prototype.js').read_text();start=s.index('const originalClass=');end=s.index('rows.push(',start)
s=s[:start]+s[end:];s=s.replace('baseline,prototype,rollback,checks:', 'geometry:baseline,checks:{...baseline.checks,').replace('checks:{...baseline.checks,{','checks:{...baseline.checks,').replace(',rollback_geometry:JSON.stringify(baseline)===JSON.stringify(rollback)','').replace("'/png/baseline-'","'/png/acceptance-'").replace("Prototype is NOT applied-source GREEN.","Actual-source acceptance; no injected classes/styles. NOT RUN in PLAN.")
s=s.replace("PLAN ONLY: actual-source baseline, temporary DOM classes and candidate style, complete rollback; no saves.","Prepared future actual-source baseline/acceptance; no saves; NOT RUN in PLAN.")
assert '__CANDIDATE_CSS__' not in s and 'classList.add' not in s and 'addStyleTag' not in s
(O/'browser-acceptance.js').write_text(s)
print('Prepared readonly prototype and future no-injection acceptance (NOT RUN).')
