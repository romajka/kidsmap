import difflib,hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module13-repair-2026-10-19-pc-r1';Q=R/'.tmp/m13-full-r1';sha=lambda b:hashlib.sha256(b).hexdigest()
def apply(stage,files,red_file):
 S=O/'stages'/stage;assert (S/'IMPLEMENTATION_PLAN.md').exists() and not (S/'applied.json').exists();red=json.loads((O/red_file).read_text());assert red['exit']==1 and red['failures'] and not red['errors'];sources=json.loads((Q/'expected-source.json').read_text())['sources'];assert all(sha((R/p).read_bytes())==h for p,h in sources.items());diff='';metadata={}
 for path,after in files.items():
  before=(R/path).read_bytes() if (R/path).exists() else None;assert before!=after
  for folder,data in [('entry-source',before),('candidate',after)]:
   if data is not None:
    p=S/folder/path;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(data)
  diff+=''.join(difflib.unified_diff((before or b'').decode().splitlines(True),after.decode().splitlines(True),fromfile='a/'+path if before else '/dev/null',tofile='b/'+path));metadata[path]={'before':sha(before) if before else None,'after':sha(after)}
 (S/'implemented.diff').write_text(diff,newline='');(S/'candidate-manifest.json').write_text(json.dumps(metadata,indent=2))
 p=subprocess.run(['git','-C',str(R),'apply','--check',str(S/'implemented.diff')],capture_output=True,text=True);assert p.returncode==0,p.stderr
 print('Prepared exact candidates after RED; apply with native host PowerShell apply-native.ps1 -StageName '+stage)
