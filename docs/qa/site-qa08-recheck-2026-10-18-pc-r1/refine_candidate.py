import json,hashlib,difflib
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];css='static/admin/css/pages/kidsmap_settings_forms.css';p=O/'candidate'/css
archive=O/'prototype-v1';archive.mkdir();(archive/'candidate.css').write_bytes(p.read_bytes());(archive/'candidate-manifest.json').write_bytes((O/'candidate-manifest.json').read_bytes());(archive/'proposed.diff').write_bytes((O/'proposed.diff').read_bytes())
extra='''
/* A clear checkbox belongs to a file widget, not a boolean-only field row. */
.km-settings-form-page .km-place-section .form-group:has(input[type="file"]) > .row {
  flex-direction: column !important;
  align-items: stretch !important;
}

.km-settings-form-page .km-place-section .form-group:has(input[type="file"]) > .row > div {
  width: 100% !important;
  max-width: 100% !important;
  min-width: 0;
  flex: initial !important;
}

.km-settings-form-page .km-place-form-main,
.km-settings-form-page .km-place-section__body {
  grid-template-columns: minmax(0, 1fr);
}

.km-settings-form-page .select2-container {
  min-width: 0 !important;
  width: 100% !important;
  max-width: 100%;
}
'''
p.write_bytes(p.read_bytes()+extra.replace('\n','\r\n').encode())
manifest=json.loads((O/'candidate-manifest.json').read_text());manifest['files'][css]['candidate_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();patch=''
for rel,d in manifest['files'].items():
 a=(R/rel).read_bytes() if not d['new'] else b'';b=(O/'candidate'/rel).read_bytes()
 patch+='diff --git a/'+rel+' b/'+rel+'\n'+('new file mode 100644\n' if not a else '')+''.join(difflib.unified_diff(a.decode().splitlines(keepends=True),b.decode().splitlines(keepends=True),fromfile='a/'+rel if a else '/dev/null',tofile='b/'+rel))
(O/'proposed.diff').write_bytes(patch.encode());manifest['diff_sha256']=hashlib.sha256(patch.encode()).hexdigest();(O/'candidate-manifest.json').write_text(json.dumps(manifest,indent=2))
s=(O/'browser-prototype-pilot.js').read_text().replace('pilot-baseline-','pilot2-baseline-').replace('pilot-prototype-','pilot2-prototype-').replace('#content-main .file-upload\'','#content-main .file-upload,#content-main .select2-container\'')
(O/'browser-prototype-pilot2.js').write_text(s)
s=(O/'browser-prototype.js').read_text().replace('#content-main .file-upload\'','#content-main .file-upload,#content-main .select2-container\'');(O/'browser-prototype.js').write_text(s)
(O/'candidate-refinement.json').write_text(json.dumps({'application_changes':0,'v1_retained':True,'v1_failed':'file clear checkbox triggered boolean-row flex:none !important; select2 intrinsic/inline width exceeded parent','diagnostic':'evidence/browser-file-diagnostic.json','v2_change':'Scope file-specific row override and select2 sizing; cap internal grid auto minimum. Acceptance only strengthened to include visible select2 widgets; original pilot retained.'},indent=2))
print('Diagnostic-driven prototype v2 prepared; v1 retained.')
