"""Change exactly row04; preserve all other bytes including concurrent foreign edits."""
from pathlib import Path
import json
P=Path(__file__).resolve().parent;R=P.parents[2];p=R/'docs/qa/module-acceptance-prompts.md'
data=p.read_bytes();lines=data.splitlines(keepends=True);indices=[i for i,s in enumerate(lines) if s.startswith(b'| 04 |')];assert len(indices)==1
i=indices[0];old=lines[i];assert b'NOT RUN' in old
summary=json.loads((P/'evidence-summary.json').read_text());assert summary['screenshots']==328 and summary['application_findings']['P2']==3
ending=b'\r\n' if old.endswith(b'\r\n') else b'\n' if old.endswith(b'\n') else b''
row='| 04 | Мероприятия | DONE — FAIL (fresh audit complete; limits NOT RUN) | C:\\kidsmap; task33-progress; 8d188b316f800fbedf0b1e376905dfd4924cb1b6; QA/docs dirty preserved; active_run NONE unchanged; runtime WORKTREE + existing .mo | [Отчёт](module04-2026-10-10-r1/REPORT.md), [verification](module04-2026-10-10-r1/verification.json), [matrix](module04-2026-10-10-r1/matrix.csv), [screenshots](module04-2026-10-10-r1/screenshots-manifest.json) | 3 OPEN P2 EVENT-QA; 118/129 Django PASS, 2 baseline FAIL, 9 environment preflight NOT RUN; 328 PNG; limits and SIMULATED integrations recorded; Далее 05; repairs отдельно; [handoff](module04-2026-10-10-r1/next-chat.txt) |'
lines[i]=row.encode('utf-8')+ending
assert p.read_bytes()==data
p.write_bytes(b''.join(lines))
print('Updated only module04 row, line',i+1)
