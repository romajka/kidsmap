import json,hashlib,difflib
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];manifest=json.loads((O/'candidate-manifest.json').read_text());archive=O/'prototype-v2-full';archive.mkdir()
for rel in manifest['files']:
 p=archive/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((O/'candidate'/rel).read_bytes())
for n in ['proposed.diff','candidate-manifest.json','browser-prototype.js','browser-readonly-prototype.js']:(archive/n).write_bytes((O/n).read_bytes())
css='static/admin/css/pages/kidsmap_settings_forms.css';p=O/'candidate'/css
extra='''
/* Boolean help text must shrink with its row instead of retaining max-content. */
.km-settings-form-page .km-place-section .form-group:has(input[type="checkbox"]) > .row > div {
  min-width: 0;
  max-width: 100% !important;
  flex: 0 1 auto !important;
}

.km-settings-form-page .km-place-section .form-group:has(input[type="checkbox"]) > .row > label {
  max-width: 100% !important;
  overflow-wrap: anywhere;
}

@media (max-width: 760px) {
  .km-settings-form-page .km-place-section .form-group:has(input[type="checkbox"]) > .row {
    flex-direction: column !important;
    align-items: stretch !important;
  }

  .km-settings-form-page .km-place-section .form-group:has(input[type="checkbox"]) > .row > div {
    width: 100% !important;
  }
}
''';p.write_bytes(p.read_bytes()+extra.replace('\n','\r\n').encode());patch=''
for rel,d in manifest['files'].items():
 a=(R/rel).read_bytes() if not d['new'] else b'';b=(O/'candidate'/rel).read_bytes();d['candidate_sha256']=hashlib.sha256(b).hexdigest()
 patch+='diff --git a/'+rel+' b/'+rel+'\n'+('new file mode 100644\n' if not a else '')+''.join(difflib.unified_diff(a.decode().splitlines(keepends=True),b.decode().splitlines(keepends=True),fromfile='a/'+rel if a else '/dev/null',tofile='b/'+rel))
(O/'proposed.diff').write_bytes(patch.encode());manifest['diff_sha256']=hashlib.sha256(patch.encode()).hexdigest();(O/'candidate-manifest.json').write_text(json.dumps(manifest,indent=2))
for n in ['browser-prototype','browser-readonly-prototype']:
 s=(O/(n+'.js')).read_text().replace('#content-main .select2-container\'','#content-main .select2-container,#content-main .help-block\'').replace("'/png/baseline-'","'/png/final-baseline-'").replace("'/png/prototype-'","'/png/final-prototype-'").replace("'/png/viewer-baseline-'","'/png/final-viewer-baseline-'").replace("'/png/viewer-prototype-'","'/png/final-viewer-prototype-'")
 (O/(n+'-final.js')).write_text(s)
(O/'boolean-refinement.json').write_text(json.dumps({'application_changes':0,'v2_full_retained':True,'v2_full':'793/810 prototype geometry PASS,17FAIL all analytics document overflow;486/486 controls and rollback PASS','diagnostic':'evidence/browser-analytics-diagnostic.json: boolean helper flex:none/max-width:none wrapper1095.66px','v3':'Allow boolean help wrapper shrink, cap label, stack boolean row only at<=760; include visible help blocks in bounds checks','not_changed':'No application source or assertions weakened; original native results retained'},indent=2))
print('Diagnostic-driven final candidate; v2 full matrix and candidate retained.')
