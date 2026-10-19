import json,difflib
from pathlib import Path
R=Path('/mnt/c/kidsmap');S=R/'docs/qa/module10-sequential-2026-10-18-pc-r1/stages/SITE14';D=S/'unmounted-legacy-guard-investigation'
(D/'initial-implemented.diff').write_bytes((S/'implemented.diff').read_bytes());diff='';m=json.loads((S/'applied.json').read_text())
for p in m['files']:
 b=S/'entry-source'/p;before=b.read_bytes() if b.exists() else b'';after=(R/p).read_bytes();diff+=''.join(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),fromfile='a/'+p if b.exists() else '/dev/null',tofile='b/'+p))
(S/'implemented.diff').write_text(diff,newline='');print('Final7file SITE14 diff regenerated; initial8file diff retained.')
