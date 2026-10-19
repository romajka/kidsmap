from pathlib import Path
import subprocess,json,hashlib
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
code="import yaml,json;from pathlib import Path;p=Path('/mnt/c/kidsmap/.github/workflows/deploy.yml');d=yaml.safe_load(p.read_text());print(json.dumps({'jobs':sorted(d['jobs']),'run_steps':[s['run'] for s in d['jobs']['quality']['steps'] if 'run' in s],'deploy_needs':d['jobs']['deploy']['needs']}))"
d=json.loads(subprocess.check_output(['python3','-c',code],text=True));assert d['jobs']==['deploy','quality'] and d['deploy_needs']=='quality';shell=[]
for i,text in enumerate(d['run_steps']):
 p=Q/('ci-step-'+str(i)+'.sh');p.write_text(text);result=subprocess.run(['bash','-n',str(p)],capture_output=True,text=True);assert result.returncode==0,result.stderr;shell.append({'step':i,'syntax_exit':result.returncode})
old=(O/'stages/quality/entry-source/.github/workflows/deploy.yml').read_bytes();new=(R/'.github/workflows/deploy.yml').read_bytes();suffix=lambda b:b[b.index(b'  deploy:'):];assert suffix(old)==suffix(new)
(O/'evidence/ci-structure.json').write_text(json.dumps({'yaml_parse':'PASS','jobs':d['jobs'],'deploy_needs':d['deploy_needs'],'deploy_bytes_sha256':hashlib.sha256(suffix(new)).hexdigest(),'deploy_job_byte_identical':True,'bash_syntax':shell,'contains_continue_on_error':'continue-on-error' in new.decode(),'actual_GitHub_execution':'NOT RUN','provision_and_cleanup_not_executed_by_this_syntax_check':True},indent=2));print('CI YAML, complete gate/deploy dependency and Bash syntax PASS; deploy byte-identical.')
# Correct latest module09 final decision; other report inputs remain unchanged.
p=R/'.tmp/m13-reconcile.py';t=p.read_text().replace("'module09-close-2026-10-18-pc-r1'","'social-qa12-fix-2026-10-18-pc-r1'");(R/'.tmp/m13-reconcile-final.py').write_text(t);subprocess.run(['python3',str(R/'.tmp/m13-reconcile-final.py')],stdout=(Q/'module-reconciliation.log').open('w'),check=True)
# Current Windows compiler branch, original9 assertions including junction control.
p=R/'.tmp/m13-python-windows.py';t=p.read_text().replace('python-windows-locales.log','python-windows-locales-final.log').replace('python-windows-locales.json','python-windows-locales-final.json');(R/'.tmp/m13-python-windows-final.py').write_text(t)
