import json
from pathlib import Path
O=Path('/mnt/c/kidsmap/docs/qa/site-qa22-fix-2026-10-18-pc-r1');s=(O/'browser-save-engine.js').read_text();models=['sitebrandingsettings','siteaboutsettings','sitecontactssettings','sitefootersettings','siteemptystatesettings','sitevisibilitysettings']
for phase in ['red','green']:
 cfg={'lang':'ru','models':['sitebrandingsettings','sitefootersettings'],'widths':[360],'long':False,'prefix':'focused-'+phase};(O/('browser-focused-'+phase+'.js')).write_text(s.replace('__CONFIG__',json.dumps(cfg)))
for lang in ['az','ru','en']:
 cfg={'lang':lang,'models':models,'widths':[360,390,768,1024,1280,1440],'long':True,'prefix':'save'};(O/('browser-saves-'+lang+'.js')).write_text(s.replace('__CONFIG__',json.dumps(cfg)))
