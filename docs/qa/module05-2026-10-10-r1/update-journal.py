"""Only row05; byte-preserve all foreign journal content."""
from pathlib import Path
import json
P=Path(__file__).resolve().parent;path=P.parent/'module-acceptance-prompts.md'
current=path.read_bytes();entry=(P/'journal-entry.txt').read_bytes()
assert current==entry,'Journal changed externally; rebase one row explicitly, never overwrite.'
lines=current.splitlines(keepends=True);targets=[i for i,line in enumerate(lines) if line.startswith(b'| 05 |')];assert len(targets)==1
index=targets[0];assert b'NOT RUN' in lines[index]
s=json.loads((P/'results-summary.json').read_text(encoding='utf-8'))
row=f'| 05 | Программы, занятия, группы, тарифы и расписание | DONE — FAIL (fresh audit complete; limits NOT RUN) | C:\\kidsmap; task33-progress; 8d188b316f800fbedf0b1e376905dfd4924cb1b6; dirty QA/docs preserved; active_run NONE unchanged; runtime WORKTREE + existing .mo | [Отчёт](module05-2026-10-10-r1/REPORT.md), [verification](module05-2026-10-10-r1/verification.json), [matrix](module05-2026-10-10-r1/matrix.csv), [screenshots](module05-2026-10-10-r1/screenshots-manifest.json) | 8 OPEN OFFER-QA (6 P2, 2 P3; locale source/environment mixed);250/250 Django PASS;{s["browser_screenshots"]} rendered PNG +4 crops/contact; limits/SIMULATED recorded; Далее06; repairs отдельно; [handoff](module05-2026-10-10-r1/next-chat.txt) |'
ending=b'\r\n' if lines[index].endswith(b'\r\n') else b'\n';lines[index]=row.encode('utf-8')+ending
path.write_bytes(b''.join(lines));print('Only module05 journal row updated; others byte-preserved.')
