"""Change exactly module11 row, preserving every other byte of foreign journal."""
from pathlib import Path
import json
P=Path(__file__).resolve().parent;R=P.parents[2];target=R/'docs/qa/module-acceptance-prompts.md'
prior=(P/'journal-entry.txt').read_bytes();current=target.read_bytes();assert current==prior,'Foreign journal drift: never overwrite'
lines=current.splitlines(keepends=True);idx=[i for i,x in enumerate(lines) if x.startswith(b'| 11 |')];assert len(idx)==1
i=idx[0];assert b'NOT RUN' in lines[i];ending=b'\r\n' if lines[i].endswith(b'\r\n') else b'\n'
c=json.loads((P/'counts.json').read_text())['accepted_observations'];png=len(json.loads((P/'screenshots-manifest.json').read_text()))
row=f'| 11 | SEO, языковые URL и redirects | DONE — FAIL (fresh audit complete; limits NOT RUN) | C:\\kidsmap; task33-progress; 8d188b316f800fbedf0b1e376905dfd4924cb1b6; dirty foreign WORKTREE preserved; active_run NONE unchanged; runtime WORKTREE + existing .mo matched | [Отчёт](module11-2026-10-11-r1/REPORT.md), [verification](module11-2026-10-11-r1/verification.json), [matrix](module11-2026-10-11-r1/matrix.csv), [screenshots](module11-2026-10-11-r1/screenshots-manifest.json) | 7 OPEN SEO-QA (6 P2,1 P3); 106/110 main Django PASS,4 flag-compatibility failures then 4/4 legacy PASS;33 extra PASS,9 environment/business NOT RUN;{c["PASS"]} PASS/{c["FAIL"]} FAIL/{c["NOT RUN"]} NOT RUN observations;{png} native PNG;SIMULATED/gaps recorded; Далее 12; repairs отдельно; [handoff](module11-2026-10-11-r1/next-chat.txt) |'
lines[i]=row.encode('utf-8')+ending;target.write_bytes(b''.join(lines));assert len(current.splitlines())==len(target.read_bytes().splitlines());print('Updated exactly journal row11, line',i+1)
