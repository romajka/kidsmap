import difflib,hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module10-sequential-2026-10-18-pc-r1';Q=R/'.tmp/m10-seq-r1'
def apply(number,files):
 S=O/'stages'/('SITE'+number);assert (S/'IMPLEMENTATION_PLAN.md').exists() and not (S/'applied.json').exists()
 if (S/'evidence/red-backend.json').exists():
  red=json.loads((S/'evidence/red-backend.json').read_text());assert red['exit']==1 and red['failures'] and not red['errors']
 else:
  red=json.loads((S/'evidence/red-native.json').read_text());assert any(False in row['checks'].values() for row in red['rows']) and not red.get('pageerrors') and not red.get('errors')
 sources=json.loads((Q/'expected-source.json').read_text())['sources'];sha=lambda b:hashlib.sha256(b).hexdigest()
 assert all(sha((R/p).read_bytes())==h for p,h in sources.items())
 metadata={};diff=''
 for rel,after in files.items():
  before=(R/rel).read_bytes() if (R/rel).exists() else None
  assert before!=after and isinstance(after,bytes)
  for name,data in [('candidate',after),('entry-source',before)]:
   if data is not None:p=S/name/rel;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(data)
  diff+=''.join(difflib.unified_diff((before or b'').decode().splitlines(True),after.decode().splitlines(True),fromfile='a/'+rel if before else '/dev/null',tofile='b/'+rel));metadata[rel]={'before':sha(before) if before else None,'after':sha(after)}
 (S/'implemented.diff').write_text(diff,newline='');p=subprocess.run(['git','-C',str(R),'apply','--check',str(S/'implemented.diff')],capture_output=True,text=True);assert p.returncode==0,p.stderr
 for rel,after in files.items():(R/rel).write_bytes(after);sources[rel]=sha(after)
 (Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2));(S/'source-applied.json').write_text(json.dumps({'sources':sources},indent=2));(S/'applied.json').write_text(json.dumps({'files':metadata,'source_count':len(sources),'apply_check_exit':0},indent=2));print('SITE'+number+' planned patch applied after RED;'+str(len(files))+'files.')
