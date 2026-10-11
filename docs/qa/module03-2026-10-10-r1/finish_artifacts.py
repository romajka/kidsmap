"""Finalize own report and change exactly the requested journal row03."""
from pathlib import Path
import json
P=Path(__file__).resolve().parent;R=P.parents[2]
summary=json.loads((P/'evidence-summary.json').read_text(encoding='utf-8'))
report=P/'REPORT.md';s=report.read_text(encoding='utf-8');s=s.replace('{{MATRIX_COUNTS}}',', '.join(f'{k}={v}' for k,v in summary['normalized_matrix_counts'].items()));report.write_text(s,encoding='utf-8')
target=R/'docs/qa/module-acceptance-prompts.md';entry=(P/'journal-entry.txt').read_bytes();current=target.read_bytes();lines=current.splitlines(keepends=True)
expected=entry.splitlines(keepends=True)
assert len(lines)==len(expected)
assert all(a==b for i,(a,b) in enumerate(zip(lines,expected)) if i!=22),'Concurrent foreign journal edit: refuse overwrite.'
assert lines[22].startswith('| 03 | Специалисты и приватные документы |'.encode())
ending=b'\r\n' if lines[22].endswith(b'\r\n') else b'\n'
row='| 03 | Специалисты и приватные документы | DONE — FAIL (fresh audit complete; limits NOT RUN) | C:\\kidsmap; task33-progress; 8d188b316f800fbedf0b1e376905dfd4924cb1b6; entry QA-only dirty; active_run NONE unchanged; runtime WORKTREE + existing .mo | [Отчёт](module03-2026-10-10-r1/REPORT.md), [evidence](module03-2026-10-10-r1/verification.json), [matrix](module03-2026-10-10-r1/matrix.csv), [screenshots](module03-2026-10-10-r1/screenshots-manifest.json) | 3 OPEN SPEC-QA (2 P2, 1 P3); 106/107 Django PASS, 1 Windows ERROR; 455 PNG; locale/environment/integration/coverage limits documented; Далее 04; repair отдельным scope; [handoff](module03-2026-10-10-r1/next-chat.txt) |'
lines[22]=row.encode('utf-8')+ending;target.write_bytes(b''.join(lines))
v=P/'verification.json'
if not v.exists():v.write_text('{"status":"pending fresh verification"}\n',encoding='utf-8')
plan=P/'PLAN.md';plan.write_text(plan.read_text(encoding='utf-8')+'\nAudit result: complete with3applicationfindings and explicit NOT RUN limits. See REPORT/evidence-summary. Checklist items are audit directions, not claims of exhaustive PASS.\n',encoding='utf-8')
print('Own report finalized; journal row03 changed byte-preserving other rows. Verification still required.')
