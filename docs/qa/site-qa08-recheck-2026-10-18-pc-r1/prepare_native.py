from pathlib import Path
O=Path(__file__).resolve().parent
p=O/'browser_driver.py';s=p.read_text();needle=" code=(O/name).read_text()";assert needle in s
s=s.replace(needle,needle+"\n if '__CANDIDATE_CSS__' in code:code=code.replace('__CANDIDATE_CSS__',json.dumps((O/'candidate/static/admin/css/pages/kidsmap_settings_forms.css').read_text()))")
p.write_text(s)
original=(O/'browser-prototype.js').read_text();pilot=original.replace("['az','ru','en']","['ru']").replace("['sitebrandingsettings','siteaboutsettings','sitecontactssettings','sitefootersettings','siteemptystatesettings','sitevisibilitysettings','siteanalytics','catalogcontentsettings','sitegalleryimage']","['sitebrandingsettings','siteaboutsettings','sitefootersettings','sitegalleryimage']").replace('[360,390,768,1024,1280,1440]','[360,1440]').replace("[390,1440].includes(width)","[360,1440].includes(width)").replace("'/png/baseline-'","'/png/pilot-baseline-'").replace("'/png/prototype-'","'/png/pilot-prototype-'")
(O/'browser-prototype-pilot.js').write_text(pilot)
print('Prototype pilot prepared; full matrix retained separately.')
