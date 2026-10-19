from pathlib import Path
O=Path(__file__).resolve().parent
p=O/'bootstrap-wrapper-initial.py';recovery=p.read_text()
(O/'bootstrap-wrapper-recovery.py').write_text(recovery)
old="O=R/'docs/qa/site-qa20-fix-2026-10-18-pc-r1'\n(O/'bootstrap-wrapper-initial.py').write_bytes(Path(__file__).read_bytes())\n(O/'bootstrap.py').write_text(s)"
new="exec(compile(s,str(Path(__file__)), 'exec'))\nO=R/'docs/qa/site-qa20-fix-2026-10-18-pc-r1'\n(O/'bootstrap.py').write_text(s)"
assert recovery.count(old)==1
initial=recovery.replace(old,new)
p.write_text(initial)
(O/'initial-harness-failures/bootstrap-wrapper-initial.py').write_text(initial)
(O/'initial-harness-failures/bootstrap-error.txt').write_text("Setup completed: sources1034/prior40files8205/own app ready. Then wrapper failed:\nTypeError: data must be str, not socket\nAt (O/'bootstrap.py').write_text(s). exec's module scope reused s in with socket.socket() as s.\nOriginal trace is in tool output; this concise record transcribes its type/location, not raw production logs.\nRendered bootstrap regenerated without rerunning infrastructure.\n")
print('Original wrapper/recovery source and concise failure provenance retained; no setup re-executed.')
