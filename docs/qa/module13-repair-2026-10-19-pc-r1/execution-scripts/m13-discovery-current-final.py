from pathlib import Path
import subprocess,json,hashlib
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
t=(Q/'discovery.py').read_text().replace('discovery-baseline.json','discovery-current.json');(Q/'discovery-current.py').write_text(t)
p=subprocess.run(['docker','exec','m13full-r1-app','python',str(Q/'discovery-current.py')],capture_output=True,text=True);assert p.returncode==0,p.stderr;d=json.loads((Q/'discovery-current.json').read_text());assert d['no_label']['ids']==d['exhaustive']['ids'] and not d['no_label']['duplicates'];(O/'evidence/discovery-current.json').write_bytes((Q/'discovery-current.json').read_bytes());print(p.stdout)
# Exercise actual manage.main command and real shell wrapper with discovery-only relay.
(Q/'discovery-manage.py').write_text('''import sys,json,os
sys.argv=['runtime.py','discover'];from runtime import *
os.chdir(ROOT)
from config.test_runner import KidsMapTestRunner
def flatten(s):
 for t in s:
  if hasattr(t,'_tests'):yield from flatten(t)
  else:yield t.id()
def discovery(self,labels,**kwargs):
 ids=list(flatten(self.build_suite(labels)));(QA/'manage-discovery-current.json').write_text(json.dumps({'ids':sorted(ids),'count':len(ids),'unique':len(set(ids)),'labels':labels},indent=2));return 0
KidsMapTestRunner.run_tests=discovery
import manage
sys.argv=['manage.py','test','--parallel','1']
manage.main()
''')
p=subprocess.run(['docker','exec','m13full-r1-app','python',str(Q/'discovery-manage.py')],capture_output=True,text=True);assert p.returncode==0,p.stderr
manage=json.loads((Q/'manage-discovery-current.json').read_text());assert manage['ids']==d['exhaustive']['ids'];(O/'evidence/manage-discovery-current.json').write_text(json.dumps(manage,indent=2))
# Intercept only the Python executable to capture wrapper argv; no tests are skipped in actual full execution.
binpath=Q/'wrapper-bin';binpath.mkdir(exist_ok=True);fake=binpath/'python';fake.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > '+str(Q/'wrapper-argv.txt')+'\n');fake.chmod(0o700)
p=subprocess.run(['bash',str(R/'scripts/run_kidsmap_tests.sh'),'full','--parallel','1'],cwd=Q,env={'PATH':str(binpath)+':/usr/bin:/bin'},capture_output=True,text=True);assert p.returncode==0,p.stderr
args=(Q/'wrapper-argv.txt').read_text().splitlines();assert args==['manage.py','test','--parallel','1'],args
tracked=set(subprocess.check_output(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','ls-files','src/catalog/testcases'],text=True).splitlines())
corpus={'ids':len(manage['ids']),'tracked_source_methods':sum('src/'+i.rsplit('.',2)[0].replace('.','/')+'.py' in tracked for i in manage['ids']),'wrapper_argv':args,'wrapper_real_shell_exit':p.returncode,'manage_main_discovery_only':True,'actual_GitHub_execution':'NOT RUN','root_cwd':str(R)}
(O/'evidence/discovery-corpus.json').write_text(json.dumps(corpus,indent=2));print(json.dumps(corpus,indent=2))
