import difflib,hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site06-pc-fix-r1';P=R/'docs/qa/site-qa06-recheck-2026-10-18-pc-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
native=json.loads((O/'evidence/browser-final-matrix.json').read_text());assert len(native['rows'])==108 and not native.get('error') and all(all(x['checks'].values()) for x in native['rows'])
refinement=json.loads((O/'refinement.json').read_text());assert all(sha(R/p)==h for p,h in refinement['files'].items())
(O/'pre-color-matrix-source.json').write_text(json.dumps({'files':refinement['files'],'native':'evidence/browser-final-matrix.json','body_text_contrast_measured':'RGB(0,154,78) against white:3.66:1; below4.5 for normal16px error text','change_authorized':'same shared error markup within seven-file scope; existing utility only'},indent=2))
rel='src/catalog/templates/admin/catalog/shared_settings_change_form.html';p=R/rel;before=p.read_bytes();(O/'pre-color-shared-template.html').write_bytes(before);needle=b'<a href="#{{ field.id_for_label }}">';assert before.count(needle)==1;p.write_bytes(before.replace(needle,b'<a class="text-body" href="#{{ field.id_for_label }}">'))
sources=json.loads((Q/'expected-source.json').read_text())['sources'];sources[rel]=sha(p);(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2));(Q/'stage.json').write_text(json.dumps({'locales':'locales-green','test_db':'test_m10s06_fix_r1_final'}))
subprocess.run(['docker','exec','m09full-r1-pg','createdb','-U','m09full_r1','-O','m09full_r1','test_m10s06_fix_r1_final'],check=True)
files=json.loads((P/'candidate-manifest.json').read_text())['files'];diff=b''
for rel in sorted(files):
 old=(O/'entry-source'/rel).read_bytes() if (O/'entry-source'/rel).exists() else b'';new=(R/rel).read_bytes();diff+=b''.join(difflib.diff_bytes(difflib.unified_diff,old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile=(('a/'+rel).encode() if old else b'/dev/null'),tofile=('b/'+rel).encode()))
(O/'implemented.diff').write_bytes(diff)
(O/'color-refinement.json').write_text(json.dumps({'reason':'Measured new media-summary link text contrast3.66:1','change':'Existing text-body utility on media-summary anchors only; no CSS/JS/policy/backend/test change','before_template_sha256':hashlib.sha256(before).hexdigest(),'after_template_sha256':sha(p),'files':{rel:sha(R/rel) for rel in files},'diff_sha256':sha(O/'implemented.diff'),'full_behavior_matrix_snapshot':'pre-color-matrix-source.json','current_render_verification':'browser-color-forms.js, all36branding cells plus post-color edge editors'},indent=2))
for old,new in [('run_refined_green.py','run_final_green.py'),('check_refined_static.py','check_final_static.py'),('run_refined_static.py','run_final_static.py')]:
 s=(O/old).read_text()
 if old.startswith('run_refined_green'):s=s.replace('refined-green','final-green')
 if old.startswith('check_'):s=s.replace('test_m10s06_fix_r1_refined','test_m10s06_fix_r1_final').replace('refined-static-result.json','final-static-result.json')
 if old=='run_refined_static.py':s=s.replace('check_refined_static.py','check_final_static.py').replace('refined-static-commands.json','final-static-commands.json').replace('refined-static-result.json','final-static-result.json').replace('refined-static-runtime.json','final-static-runtime.json').replace('refined-validator-edges.json','final-validator-edges.json')
 (O/new).write_text(s)
print(json.dumps({'color_only_shared_template_refined':True,'fresh_final_test_db':True,'backend_and_test_unchanged':True}))
