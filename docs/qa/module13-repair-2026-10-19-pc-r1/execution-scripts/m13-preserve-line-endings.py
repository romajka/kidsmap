from pathlib import Path
import json,hashlib,difflib,shutil,subprocess
R=Path('/mnt/c/kidsmap');S=R/'docs/qa/module13-repair-2026-10-19-pc-r1/stages/cross';meta=json.loads((S/'candidate-manifest.json').read_text());attempt=S/'normalization-attempt';attempt.mkdir()
for n in ['implemented.diff','candidate-manifest.json']:shutil.copyfile(S/n,attempt/n)
diff=''
for p,item in meta.items():
 old=(R/p).read_bytes();new=(S/'candidate'/p).read_bytes();ending=b'\r\n' if old.count(b'\r\n')>old.count(b'\n')/2 else b'\n'
 if p.endswith('public_details.py'):new=old.replace(b"occurrence_state='scheduled'",b"occurrence_state__in=('scheduled', 'rescheduled')")
 elif p.endswith('test_runner.py'):
  oldimp=b'import unittest'+(b'\r\n' if b'import unittest\r\n' in old else b'\n')
  new=old.replace(oldimp,oldimp+b'import pkgutil'+ending)
  text=(S/'candidate'/p).read_text();method=text[text.index('    def build_suite('):text.index('    def get_resultclass(')]
  marker=b'    parallel_test_suite = KidsMapParallelTestSuite'+(b'\r\n' if b'KidsMapParallelTestSuite\r\n' in old else b'\n')
  new=new.replace(marker,marker+ending+method.rstrip().replace('\n',ending.decode()).encode()+ending)
 elif p.endswith('run_kidsmap_tests.sh'):new=old.replace(b'    run_suite catalog',b'    # No labels selects the canonical complete KidsMapTestRunner corpus.'+ending+b'    run_suite')
 (S/'candidate'/p).write_bytes(new);item['after']=hashlib.sha256(new).hexdigest();diff+=''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile='a/'+p,tofile='b/'+p))
(S/'candidate-manifest.json').write_text(json.dumps(meta,indent=2));(S/'implemented.diff').write_text(diff,newline='');subprocess.run(['git','-C',str(R),'apply','--check',str(S/'implemented.diff')],check=True)
print('Exact source line endings preserved; reviewed diff',len(diff.splitlines()),'lines')
