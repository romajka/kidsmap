import difflib,hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;rel='src/catalog/templates/admin/catalog/shared_settings_change_form.html'
old=(R/rel).read_bytes();needle=b'<div id="content-main" class="km-place-form-page">';replacement=b'<div id="content-main" class="km-place-form-page{% if opts.model_name == \'catalogcontentsettings\' %} col-12{% endif %}">'
assert old.count(needle)==1;new=old.replace(needle,replacement);dest=O/'candidate'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(new)
diff=''.join(difflib.unified_diff(old.decode().splitlines(keepends=True),new.decode().splitlines(keepends=True),fromfile='a/'+rel,tofile='b/'+rel));(O/'proposed.diff').write_bytes(diff.encode())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=subprocess.run(['git','-C',str(R),'apply','--check',str(O/'proposed.diff')],capture_output=True,text=True);assert r.returncode==0,r.stderr
(O/'candidate-manifest.json').write_text(json.dumps({'files':{rel:{'before_sha256':sha(R/rel),'candidate_sha256':sha(dest),'bytes':len(new)}},'diff_sha256':sha(O/'proposed.diff'),'original_bytes_retained_outside_replacement':new.replace(replacement,needle)==old,'application_changes':0,'not_applied':True,'GREEN':'NOT RUN'},indent=2))
print(json.dumps({'file':rel,'one_line_conditional_existing_Bootstrap_class':True,'apply_check_exit':r.returncode,'application_changes':0}))
