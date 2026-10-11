"""Replace only the module01 journal row, preserving every other byte."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'module-acceptance-prompts.md'
data=p.read_bytes()
rows=data.splitlines(keepends=True)
matches=[i for i,r in enumerate(rows) if r.startswith(b'| 01 |')]
assert len(matches)==1
i=matches[0]
assert b'NOT RUN' in rows[i]
ending=b'\r\n' if rows[i].endswith(b'\r\n') else b'\n'
row='| 01 | Постоянные места | DONE — FAIL (audit complete) | C:\\kidsmap; task33-progress; 8d188b316f800fbedf0b1e376905dfd4924cb1b6; entry clean; final QA-only dirty; active_run NONE unchanged | [Отчёт](module01-2026-10-09-r1/REPORT.md), [evidence](module01-2026-10-09-r1/verification.json), [matrix](module01-2026-10-09-r1/matrix.csv), [screenshots](module01-2026-10-09-r1/screenshots-manifest.json) | 5 OPEN PLACE-QA; 84 tests OK; external SDK/GPS/full suites NOT RUN; owner coordinate positive not confirmed. Далее 02; repair только отдельным scope; [handoff](module01-2026-10-09-r1/next-chat.txt) |'
rows[i]=row.encode('utf-8')+ending
updated=b''.join(rows).replace(b'owner coordinate positive not confirmed. ',b'')
assert data.splitlines(keepends=True)[:i]==updated.splitlines(keepends=True)[:i]
assert data.splitlines(keepends=True)[i+1:]==updated.splitlines(keepends=True)[i+1:]
p.write_bytes(updated)
print('Changed journal row01 only; other bytes preserved')
