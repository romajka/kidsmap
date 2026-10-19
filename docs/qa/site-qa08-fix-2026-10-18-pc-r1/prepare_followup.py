import difflib,hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];D=O/'followup';rel='static/admin/css/pages/kidsmap_settings_forms.css';before=(R/rel).read_bytes();assert hashlib.sha256(before).hexdigest()=='baf70032e5b918a783c136b4fa9449855c6eafb18df13f015a7ff144c7367f83'
extra='''
/* Jazzmin messages mix anonymous text and an object link; keep normal wrapping. */
body:has(.km-settings-form-page) #content > .alert {
  display: block;
  min-width: 0;
  max-width: 100%;
  overflow-wrap: anywhere;
}
'''.replace('\n','\r\n').encode();after=before+extra;p=D/'candidate'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(after)
patch='diff --git a/'+rel+' b/'+rel+'\n'+''.join(difflib.unified_diff(before.decode().splitlines(keepends=True),after.decode().splitlines(keepends=True),fromfile='a/'+rel,tofile='b/'+rel));(D/'proposed.diff').write_bytes(patch.encode());(D/'extra.css').write_bytes(extra)
(D/'candidate-manifest.json').write_text(json.dumps({'files':{rel:{'before_sha256':hashlib.sha256(before).hexdigest(),'candidate_sha256':hashlib.sha256(after).hexdigest()}},'diff_sha256':hashlib.sha256(patch.encode()).hexdigest(),'not_applied':True,'scope':'Remaining SITE08 saved-message document overflow only; no navigation/backend/SITE22 change'},indent=2))
p=O/'browser_driver.py';s=p.read_text();needle=" code=(O/name).read_text()";assert needle in s;s=s.replace(needle,needle+"\n if '__FOLLOWUP_CSS__' in code:code=code.replace('__FOLLOWUP_CSS__',json.dumps((O/'followup/extra.css').read_text()))");p.write_text(s);print('Concrete one-CSS-file followup prepared inside evidence ONLY; not applied.')
