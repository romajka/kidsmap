import json,hashlib,difflib
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];manifest=json.loads((O/'candidate-manifest.json').read_text());archive=O/'prototype-v2-pilot';archive.mkdir()
for rel in manifest['files']:
 p=archive/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((O/'candidate'/rel).read_bytes())
for n in ['proposed.diff','candidate-manifest.json']:(archive/n).write_bytes((O/n).read_bytes())
template='src/catalog/templates/admin/catalog/shared_settings_change_form.html';p=O/'candidate'/template;s=p.read_bytes();needle=b'km-place-form-page km-settings-form-page col-12';assert s.count(needle)==1;p.write_bytes(s.replace(needle,needle+b"{% if has_change_permission %} km-settings-form-page--editable{% endif %}"))
css='static/admin/css/pages/kidsmap_settings_forms.css';p=O/'candidate'/css;s=p.read_bytes();needle=b'.km-settings-form-page .km-place-sidebar-card--actions';assert s.count(needle)==1;p.write_bytes(s.replace(needle,b'.km-settings-form-page--editable .km-place-sidebar-card--actions'))
patch=''
for rel,d in manifest['files'].items():
 a=(R/rel).read_bytes() if not d['new'] else b'';b=(O/'candidate'/rel).read_bytes();d['candidate_sha256']=hashlib.sha256(b).hexdigest()
 patch+='diff --git a/'+rel+' b/'+rel+'\n'+('new file mode 100644\n' if not a else '')+''.join(difflib.unified_diff(a.decode().splitlines(keepends=True),b.decode().splitlines(keepends=True),fromfile='a/'+rel if a else '/dev/null',tofile='b/'+rel))
(O/'proposed.diff').write_bytes(patch.encode());manifest['diff_sha256']=hashlib.sha256(patch.encode()).hexdigest();(O/'candidate-manifest.json').write_text(json.dumps(manifest,indent=2))
p=O/'browser-prototype.js';s=p.read_text();s=s.replace("classList.add('km-settings-form-page','col-12')","classList.add('km-settings-form-page','km-settings-form-page--editable','col-12')");p.write_text(s)
(O/'permission-scope.json').write_text(json.dumps({'mobile_actions':'Restored only when existing Django has_change_permission is true; marker supplied by template','readonly_mobile_actions':'Existing hidden state retained; separate SITE20 desktop buttons not changed','backend_permissions':'No change','prototype':'Super fixtures have change permission; final full matrix uses same editable marker','pilot_v2_retained':'prototype-v2-pilot'},indent=2))
print('Final two-file PLAN candidate prepared; editable-only mobile action restoration.')
