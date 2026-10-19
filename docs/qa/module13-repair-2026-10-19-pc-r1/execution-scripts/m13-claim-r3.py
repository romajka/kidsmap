from pathlib import Path
O=Path('/mnt/c/kidsmap/docs/qa/module13-repair-2026-10-19-pc-r1')
t=(O/'browser-native-claim-r2.js').read_text().replace('/png/claim-r2-','/png/claim-r3-');(O/'browser-native-claim-r3.js').write_text(t)
(O/'evidence/claim-scheduling-note.md').write_text('r2 claim request overlapped the same synthetic instance section-OFF matrix, so the workspace correctly failed closed while disabled. No claim was created. After feature matrix finally restored exact original flags, read-only diagnosis confirmed all ON and only a fresh request action. r3 runs the complete claim workflow exclusively; no ORM repair, identity bypass or email precondition change.\n')
