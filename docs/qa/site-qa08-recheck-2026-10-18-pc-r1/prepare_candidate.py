import difflib,hashlib,json
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent
template='src/catalog/templates/admin/catalog/shared_settings_change_form.html';css='static/admin/css/pages/kidsmap_settings_forms.css'
before=(R/template).read_bytes();assert b'km-settings-form-page' not in before and not (R/css).exists()
old=b'class="km-place-form-page{% if opts.model_name == \'catalogcontentsettings\' %} col-12{% endif %}"';new=b'class="km-place-form-page km-settings-form-page col-12"';assert before.count(old)==1
needle=b'  <script src="{% static \'admin/js/kidsmap_admin_form_shell.js\' %}" defer></script>'
assert before.count(needle)==1
after=before.replace(old,new).replace(needle,b'  <link rel="stylesheet" href="{% static \'admin/css/pages/kidsmap_settings_forms.css\' %}">\r\n'+needle)
styles='''/* Shared site-settings forms only; the Place/Event shell keeps its own rules. */
.km-settings-form-page .km-place-section,
.km-settings-form-page .km-place-section__body,
.km-settings-form-page fieldset {
  min-width: 0;
}

.km-settings-form-page .file-upload,
.km-settings-form-page .file-upload a,
.km-settings-form-page .clearable-file-input,
.km-settings-form-page .url {
  max-width: 100%;
  white-space: normal;
  overflow-wrap: anywhere;
}

.km-settings-form-page input[type="file"] {
  display: block;
  width: 100%;
  max-width: 100%;
}

@media (max-width: 760px) {
  .km-settings-form-page .km-place-sidebar-card--actions {
    display: block;
  }
}
'''.replace('\n','\r\n').encode()
files={template:(before,after),css:(b'',styles)};patch='';manifest={}
for rel,(a,b) in files.items():
 p=O/'candidate'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 patch+='diff --git a/'+rel+' b/'+rel+'\n'+('new file mode 100644\n' if not a else '')+''.join(difflib.unified_diff(a.decode().splitlines(keepends=True),b.decode().splitlines(keepends=True),fromfile='a/'+rel if a else '/dev/null',tofile='b/'+rel))
 manifest[rel]={'before_sha256':hashlib.sha256(a).hexdigest() if a else None,'candidate_sha256':hashlib.sha256(b).hexdigest(),'new':not bool(a)}
(O/'proposed.diff').write_bytes(patch.encode());(O/'candidate-manifest.json').write_text(json.dumps({'files':manifest,'not_applied':True,'diff_sha256':hashlib.sha256(patch.encode()).hexdigest(),'CRLF_outside_replacements_retained':True},indent=2))
print('Two-file candidate prepared ONLY inside QA package.')
