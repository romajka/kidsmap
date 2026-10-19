from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
t=(O/'browser-event-red.js').read_text().replace('/ru/account/events/','/ru/account/places/events/');(O/'browser-event-red-r2.js').write_text(t)
t=(R/'.tmp/m12-restart.py').read_text()
for a,b in [('module12-repair-2026-10-18-pc-r1','module13-repair-2026-10-19-pc-r1'),('m12-full-r1','m13-full-r1'),('m12full-r1','m13full-r1'),('33780','33810'),('qa/m12/','qa/m13/'),('module12','module13')]:t=t.replace(a,b)
(R/'.tmp/m13-restart.py').write_text(t)
(O/'evidence/browser-harness-note.md').write_text('Initial native RED attempt used an incorrect historical management URL; current canonical /account/places/events/<pk>/manage/ verified in catalog/urls.py. No model mutation in failed attempt. Corrected r2 is separate; first evidence retained.\n')
