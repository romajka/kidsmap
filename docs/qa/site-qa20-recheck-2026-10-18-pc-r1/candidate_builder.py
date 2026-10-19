import ast,difflib,hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/site-qa20-recheck-2026-10-18-pc-r1';Q=R/'.tmp/site20-pc-plan-r1'
p='src/catalog/templates/admin/catalog/shared_settings_change_form.html'
original=(R/p).read_bytes();s=original.decode();nl='\r\n' if '\r\n' in s else '\n'
old="{% if has_change_permission %} km-settings-form-page--editable{% endif %}"
assert s.count(old)==1;s=s.replace(old,"{% if has_change_permission or add and has_add_permission %} km-settings-form-page--editable{% endif %}")
old='          <aside class="km-place-form-sidebar">'
assert s.count(old)==1;s=s.replace(old,'          {% if has_change_permission or add and has_add_permission or has_delete_permission and not add %}'+nl+old)
old='              <div class="km-place-sidebar-action-buttons">';assert s.count(old)==1
s=s.replace(old,old+nl+'                {% if has_change_permission or add and has_add_permission %}')
old='                <!-- Группа 3: Опасные действия -->';assert s.count(old)==1
s=s.replace(old,'                {% endif %}'+nl+old)
old='          </aside>';assert s.count(old)==1;s=s.replace(old,old+nl+'          {% endif %}')
target=O/'candidate'/p;target.parent.mkdir(parents=True);target.write_bytes(s.encode())
test='src/catalog/testcases/test_site_qa20_permission_actions.py';t=O/'candidate'/test;t.parent.mkdir(parents=True);t.write_bytes((O/'test_site20_candidate.py').read_bytes());ast.parse(t.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest={p:{'before_sha256':sha(R/p),'candidate_sha256':sha(target)},test:{'before_sha256':None,'candidate_sha256':sha(t)}}
diff=''.join(difflib.unified_diff(original.decode().splitlines(True),s.splitlines(True),fromfile='a/'+p,tofile='b/'+p))
diff+=''.join(difflib.unified_diff([],t.read_text().splitlines(True),fromfile='/dev/null',tofile='b/'+test))
(O/'proposed.diff').write_text(diff,newline='')
(O/'candidate-manifest.json').write_text(json.dumps({'status':'NOT APPLIED; APPROVAL PENDING','files':manifest,'diff_sha256':sha(O/'proposed.diff')},indent=2))
r=subprocess.run(['git','-C',str(R),'apply','--check',str(O/'proposed.diff')],capture_output=True,text=True)
(O/'evidence/static-apply.json').write_text(json.dumps({'command':['git','apply','--check','proposed.diff'],'exit':r.returncode,'stderr':r.stderr,'candidate_test_AST':True,'original_CRLF_preserved':s.count('\r\n')==original.count(b'\r\n')+5,'application_changes':0},indent=2));assert r.returncode==0,r.stderr
(O/'candidate_builder.py').write_bytes(Path(__file__).read_bytes())
print('Two-file candidate prepared, not applied; apply-check PASS.')
