"""Change requested journal row12 only; preserve all foreign bytes and row13."""
from pathlib import Path
import json
P=Path(__file__).resolve().parent;R=P.parents[2];target=R/'docs/qa/module-acceptance-prompts.md'
before=(P/'journal-entry.txt').read_bytes();assert target.read_bytes()==before,'Foreign journal change; stop rather than overwrite'
count=json.loads((P/'counts.json').read_text());s=count['normalized_observations'];newline=b'\r\n' if b'\r\n' in before else b'\n'
lines=before.splitlines(keepends=True);indices=[i for i,x in enumerate(lines) if x.startswith(b'| 12 |')];assert len(indices)==1
row=f'| 12 | Просмотры, счётчики и аналитика | DONE — FAIL | 2026-10-11 / module12-2026-10-11-r1 | [REPORT](module12-2026-10-11-r1/REPORT.md), [findings + repair prompts](module12-2026-10-11-r1/FINDINGS.md) | 8OPEN ANALYTICS-QA (6P2/2P3); existing60/60PASS, own4PASS/5FAIL; {s["PASS"]}PASS/{s["FAIL"]}FAIL/{s["NOT RUN"]}NOTRUN observations; {count["native_png"]}nativePNG; realGA/production NOTRUN; source/foreign preserved; Далее13; [handoff](module12-2026-10-11-r1/next-chat.txt) |'
lines[indices[0]]=row.encode('utf-8')+newline;target.write_bytes(b''.join(lines));print('Only row12 updated, line',indices[0]+1)
