import json,hashlib,difflib,shutil
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module12-repair-2026-10-18-pc-r1';S=O/'stages/beacon';A=S/'attempt-before-mapped-write';A.mkdir()
for name in ['candidate','candidate-manifest.json','implemented.diff']:
 src=S/name;dst=A/name
 if src.is_dir():shutil.copytree(src,dst)
 else:shutil.copyfile(src,dst)
p='src/catalog/templates/base.html';before=(S/'entry-source'/p).read_bytes();assert (R/p).read_bytes()==before;after=(S/'candidate'/p).read_bytes();needle=b'if (navigator.sendBeacon(trackUrl, blob)) return;';assert after.count(needle)==1;after=after.replace(needle,needle+b' // Enqueued');assert len(after)==len(before);(S/'candidate'/p).write_bytes(after);meta=json.loads((S/'candidate-manifest.json').read_text());meta[p]['after']=hashlib.sha256(after).hexdigest();(S/'candidate-manifest.json').write_text(json.dumps(meta,indent=2));diff=''
for path,info in meta.items():
 old=(S/'entry-source'/path).read_bytes() if info['before'] else b'';new=(S/'candidate'/path).read_bytes();diff+=''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile='a/'+path if info['before'] else '/dev/null',tofile='b/'+path))
(S/'implemented.diff').write_text(diff,newline='');(S/'evidence/mapped-file-recovery.md').write_text('''Native base.html write failed when resizing a Windows-mapped file. The shorter candidate had been written before SetLength failed. Verified every current byte equalled candidate prefix plus exact old tail, then restored exact original bytes without resizing. No unrelated source/process/attribute changed. Runtime source guard correctly rejected the intermediate state; readfailure green-r1 did not start tests and restart failed safely. These are environment/application-harness failures, not accepted test runs.

Preserved first candidates/diff/metadata under attempt-before-mapped-write. Revised candidate has identical semantics and an accurate // Enqueued comment, with exactly the original byte length; no trailing padding, CSS injection or secret content. Native helper now skips unnecessary SetLength when current length already matches. Old source hashes restored before reapplying; all final candidate hashes verified. No foreign process was stopped. Only own server had been stopped by the guarded restart; recovery starts it after verifying port8000free/source/CID.
''')
print('Mapped-file candidate repaired without changing sender semantics; first attempt preserved.')
