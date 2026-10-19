import difflib,hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site06-pc-fix-r1';P=R/'docs/qa/site-qa06-recheck-2026-10-18-pc-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
red=json.loads((O/'evidence/refinement-red.json').read_text());assert red['exit']==1 and red['failure_observations']==3 and red['errors']==0
rel='src/catalog/domain_admin/site.py';p=R/rel;raw=p.read_bytes();assert raw==(O/'initial-applied'/rel).read_bytes()
needle=b'class _SettingsRevisionForm(forms.ModelForm):'
helper='''def _add_site_media_error(form, name, error):
    """Use the shared wrapping summary for media errors, linked to the file input."""
    form.add_error(name, error)
    error_id = f"{form[name].auto_id}_media_error"
    widget = form.fields[name].widget
    described = widget.attrs.get("aria-describedby", "").split()
    if error_id not in described:
        described.append(error_id)
    widget.attrs["aria-describedby"] = " ".join(described)
    # The clearable widget's checkbox triggers an existing no-wrap form layout.
    # Its field error remains in form.errors; display it once in the linked summary.
    form.errors[name].error_class += " d-none"
    if not hasattr(form, "site_media_error_fields"):
        form.site_media_error_fields = set()
    form.site_media_error_fields.add(name)


'''.replace('\n','\r\n').encode()
assert raw.count(needle)==1;raw=raw.replace(needle,helper+needle)
assert raw.count(b'self.add_error(name, exc)')==1 and raw.count(b'self.add_error("image", exc)')==1
raw=raw.replace(b'self.add_error(name, exc)',b'_add_site_media_error(self, name, exc)').replace(b'self.add_error("image", exc)',b'_add_site_media_error(self, "image", exc)');p.write_bytes(raw)
rel='src/catalog/templates/admin/catalog/shared_settings_change_form.html';p=R/rel;raw=p.read_bytes();assert raw==(O/'initial-applied'/rel).read_bytes()
needle=b'                {{ adminform.form.non_field_errors }}\r\n              </div>\r\n            {% endif %}'
extra='''                {{ adminform.form.non_field_errors }}
                {% if adminform.form.site_media_error_fields %}
                  <ul class="km-place-form-error-list">
                    {% for field in adminform.form %}
                      {% if field.name in adminform.form.site_media_error_fields %}
                        <li id="{{ field.auto_id }}_media_error"><a href="#{{ field.id_for_label }}"><strong>{{ field.label }}:</strong> {% for error in field.errors %}{{ error }}{% if not forloop.last %} {% endif %}{% endfor %}</a></li>
                      {% endif %}
                    {% endfor %}
                  </ul>
                {% endif %}
              </div>
            {% endif %}'''.replace('\n','\r\n').encode()
assert raw.count(needle)==1;raw=raw.replace(needle,extra);p.write_bytes(raw)
sources=json.loads((Q/'expected-source.json').read_text())['sources']
for rel in sources:sources[rel]=sha(R/rel)
(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2))
(Q/'stage.json').write_text(json.dumps({'locales':'locales-green','test_db':'test_m10s06_fix_r1_refined'}))
subprocess.run(['docker','exec','m09full-r1-pg','createdb','-U','m09full_r1','-O','m09full_r1','test_m10s06_fix_r1_refined'],check=True)
files=json.loads((P/'candidate-manifest.json').read_text())['files'];changed=[rel for rel in files if sha(R/rel)!=files[rel]['candidate_sha256']];assert len(changed)==3
diff=b''
for rel in sorted(files):
 before=(O/'entry-source'/rel).read_bytes() if (O/'entry-source'/rel).exists() else b'';after=(R/rel).read_bytes()
 diff+=b''.join(difflib.diff_bytes(difflib.unified_diff,before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile=(('a/'+rel).encode() if before else b'/dev/null'),tofile=('b/'+rel).encode()))
(O/'implemented.diff').write_bytes(diff)
(O/'refinement.json').write_text(json.dumps({'reason':'Native initial51rows/663checks:17 missing aria-describedby,5 overflow growth; timeout before complete matrix','initial_evidence':'evidence/initial-browser-green-matrix.json','root_cause':'Django AdminFileWidget.use_fieldset=True suppresses input descriptions while Jazzmin renders divs; clearable checkbox activates width:auto/flex:none and long errors expand it','correction':'Existing shared wrapping error-summary list with field anchor/id, file aria-describedby, suppress only duplicate inline media errors with existing d-none utility; preserve field errors/context/draft/preview; no CSS/JS/policy changes','changed_from_candidate':changed,'new_regression_methods':1,'existing_29_unchanged_prefix':(R/'src/catalog/testcases/test_site_qa06_media_validation.py').read_bytes().startswith((O/'initial-applied/src/catalog/testcases/test_site_qa06_media_validation.py').read_bytes()),'files':{rel:sha(R/rel) for rel in files},'diff_sha256':sha(O/'implemented.diff')},indent=2))
# New names preserve first GREEN84, static results, incomplete native rows and PNGs.
for old,new in [('run_green.py','run_refined_green.py'),('check_static.py','check_refined_static.py'),('run_static.py','run_refined_static.py'),('browser-green-matrix.js','browser-final-matrix.js')]:
 s=(O/old).read_text()
 if old=='run_green.py':s=s.replace("'green-tests.log'","'refined-green-tests.log'").replace("'evidence/green-backend.json'","'evidence/refined-green-backend.json'")
 if old=='check_static.py':s=s.replace('test_m10s06_fix_r1_green','test_m10s06_fix_r1_refined').replace('==84','==85').replace("'test_methods':84","'test_methods':85").replace("'static-result.json'","'refined-static-result.json'")
 if old=='run_static.py':s=s.replace('check_static.py','check_refined_static.py').replace('static-commands.json','refined-static-commands.json').replace("('static-result.json','static-runtime.json')","('refined-static-result.json','refined-static-runtime.json')").replace("('validator-edges.json','validator-edges.json')","('validator-edges.json','refined-validator-edges.json')")
 if old=='browser-green-matrix.js':
  s=s.replace("x.setDefaultTimeout(12000)","x.setDefaultTimeout(30000)")
  s=s.replace("await a.goto(base+hub)","await a.goto(base+hub,{waitUntil:'domcontentloaded'})").replace("await a.goto(base+branding)","await a.goto(base+branding,{waitUntil:'domcontentloaded'})").replace("await p.goto(base+(lang==='az'?'/':'/'+lang+'/'))","await p.goto(base+(lang==='az'?'/':'/'+lang+'/'),{waitUntil:'domcontentloaded'})")
  s=s.replace("O+'/png/","O+'/png/final-")
  s=s.replace("references:(e.getAttribute('aria-describedby')||'').split(/\\s+/).filter(Boolean).every(x=>!!document.getElementById(x))","references:(e.getAttribute('aria-describedby')||'').split(/\\s+/).filter(Boolean).every(x=>{const n=document.getElementById(x);return !!n&&n.getBoundingClientRect().width>0;})")
  s=s.replace("try{\nfor(const role", "try{\nfor(const context of browser.contexts())if(context!==original.context())await context.close();\nfor(const role")
 (O/new).write_text(s)
print(json.dumps({'refined_within_7_files':True,'additional_test_RED':True,'three_candidate_files_refined':changed,'fresh_test_db':True}))
