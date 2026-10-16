"""Native Linux provenance probe, separate from unchanged WSL-only suite."""
import json,subprocess
from bootstrap import ROOT,HERE,SCRATCH,PYTHON,command,write
probe=SCRATCH/'native-probe';p=probe/'source/az/LC_MESSAGES/django.po';p.parent.mkdir(parents=True)
p.write_text('msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n\nmsgid "Hello"\nmsgstr "Salam"\n')
command([PYTHON,ROOT/'scripts/build_isolated_locales.py','build','--source-locale',probe/'source','--output',probe/'build','--locales','az','--compiler','native'])
command([PYTHON,ROOT/'scripts/build_isolated_locales.py','verify','--source-locale',probe/'source','--manifest',probe/'build/manifest.json'])
p.write_text(p.read_text()+'\n# owned probe mutation\n')
args=[str(PYTHON),str(ROOT/'scripts/build_isolated_locales.py'),'verify','--source-locale',str(probe/'source'),'--manifest',str(probe/'build/manifest.json')]
r=subprocess.run(args,capture_output=True,text=True)
assert r.returncode!=0
with (HERE/'commands.jsonl').open('a') as f:f.write(json.dumps({'argv':args,'exit':r.returncode,'expected_nonzero':True})+'\n')
write('native-locale-probe.json',{'native_build':True,'valid_manifest':True,'changed_source_rejected':True,'reject_exit':r.returncode,'scope':'own probe only; not original helper suite PASS'})
print('Native probe: build, verify, stale-source rejection confirmed.')
