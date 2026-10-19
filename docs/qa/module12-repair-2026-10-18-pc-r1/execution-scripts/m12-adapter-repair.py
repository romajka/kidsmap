from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m12-full-r1';O=R/'docs/qa/module12-repair-2026-10-18-pc-r1'
p=Q/'qa_urls.py';p.write_text(p.read_text().replace('qa/m11/','qa/m12/'))
t=(R/'.tmp/m11-restart.py').read_text()
for a,b in [('m11-full-r1','m12-full-r1'),('m11full-r1','m12full-r1'),('module11','module12'),('33710','33780'),('qa/m11/','qa/m12/')]:t=t.replace(a,b)
(R/'.tmp/m12-restart.py').write_text(t)
t=(O/'browser-report-baseline.js').read_text().replace('C:/kidsmap/','/mnt/c/kidsmap/');(O/'browser-report-baseline-r2.js').write_text(t)
(O/'evidence/adapter-notes.md').write_text('''# Own QA adapter corrections

Initial native baseline reached the ordinary admin login page: copying the prior QA adapter had retained qa/m11 path names while the new browser correctly used qa/m12. Corrected own routes and restarted only the owned PID after identity/cmdline verification. No product route/auth fix inferred. The original failed observer result is retained. Screenshot paths in the corrected observer use the WSL host's absolute path.

The simulation middleware belongs only to the normal synthetic fixture database; test databases must bypass it and exercise real unpatched reporting. Added a database-name check in own scratch middleware. Earlier results remain retained, not relabeled.

First ingress RED contained one unrelated own fixture location-validation error when reactivating an incomplete synthetic Place; stored-deleted setup corrected without changing assertions. Fresh r2 confirms16failure observations and0errors. The first native apply invocation from WSL lacked PowerShell module autoload/Get-FileHash and stopped before any source write; exact prepared candidates were applied and hash-verified using the native host PowerShell. Further stages use that host directly.
''')
