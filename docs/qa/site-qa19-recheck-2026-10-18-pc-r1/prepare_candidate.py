import ast,difflib,hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
model='src/catalog/models/site.py';test='src/catalog/testcases/test_site_qa19_catalog_content.py'
before=(R/model).read_bytes();needle='return _("Контент каталога")'.encode();replacement='return str(_("Контент каталога"))'.encode()
assert before.count(needle)==1;after=before.replace(needle,replacement);assert not (R/test).exists()
test_bytes=(O/'test_site19_candidate.py').read_bytes()
files={model:(before,after),test:(b'',test_bytes)}
diff='';manifest={}
for rel,(old,new) in files.items():
 p=O/'candidate'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(new)
 ast.parse(new.decode())
 diff+=''.join(difflib.unified_diff(old.decode().splitlines(keepends=True),new.decode().splitlines(keepends=True),fromfile='a/'+rel if old else '/dev/null',tofile='b/'+rel))
 manifest[rel]={'before_sha256':sha(old) if old else None,'candidate_sha256':sha(new),'bytes':len(new)}
(O/'proposed.diff').write_bytes(diff.encode())
cmd=['git','-C',str(R),'apply','--check',str(O/'proposed.diff')];r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0,r.stderr
tree=ast.parse(test_bytes);methods=[c.name+'.'+n.name for c in tree.body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')];assert len(methods)==12
old_ast=ast.parse(before.decode());new_ast=ast.parse(after.decode())
old_class=next(n for n in old_ast.body if isinstance(n,ast.ClassDef) and n.name=='CatalogContentSettings')
new_class=next(n for n in new_ast.body if isinstance(n,ast.ClassDef) and n.name=='CatalogContentSettings')
old_method=next(n for n in old_class.body if isinstance(n,ast.FunctionDef) and n.name=='__str__')
new_method=next(n for n in new_class.body if isinstance(n,ast.FunctionDef) and n.name=='__str__')
old_method.body=new_method.body;assert ast.dump(old_ast)==ast.dump(new_ast)
(O/'candidate-manifest.json').write_text(json.dumps({'files':manifest,'diff_sha256':sha((O/'proposed.diff').read_bytes())},indent=2))
(O/'evidence/candidate-static.json').write_text(json.dumps({'python_ast':True,'only_one_existing_method_return_expression_changes':True,'original_CRLF_bytes_retained_outside_replacement':after.replace(replacement,needle)==before,'test_methods':methods,'apply_check_command':cmd,'apply_check_exit':r.returncode,'stderr':r.stderr,'not_applied':True,'green_not_run':True},indent=2))
print(json.dumps({'files':manifest,'tests':len(methods),'apply_check_exit':r.returncode,'application_changes':0},indent=2))
