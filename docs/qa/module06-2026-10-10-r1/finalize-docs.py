"""Own evidence index and only module06 journal row; preserve all other bytes."""
from pathlib import Path
import json,collections,sys
P=Path(__file__).resolve().parent;R=P.parents[2]
sys.stdout.reconfigure(encoding='utf-8')
ledger=[json.loads(line) for line in (P/'command-ledger.jsonl').read_text(encoding='utf-8').splitlines()]
lines=['# Native browser command ledger','',
 'Полный журнал свежего Chromium; repeated attempts не считаются новыми independent tests. Native CLI exit authoritative; Python wrapper exit не заменяет его.',
 '', '| UTC | Точная команда | CLI exit | Seconds | Raw result |', '|---|---|---|---|---|']
for x in ledger:
 lines.append(f"| {x['utc']} | `{x['command']}` | {x['cli_exit_code']} | {x['duration_seconds']} | [{x['result']}]({x['result']}) |")
lines.extend(['','Counts: '+json.dumps(dict(collections.Counter(x['cli_exit_code'] for x in ledger)),ensure_ascii=False)+f'; attempts={len(ledger)}.',
 '', 'В ledger result имя соответствует последнему результату команды; предыдущие результаты сохранены под .attemptN.txt. Исторический UTC не означает timestamp последней версии одноимённого файла. CORRECTIONS.md и aggregate.py объясняют выбор окончательных observations.'])
(P/'BROWSER-COMMANDS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
summary=json.loads((P/'results-summary.json').read_text(encoding='utf-8'))
journal=R/'docs/qa/module-acceptance-prompts.md';before=journal.read_bytes();parts=before.splitlines(keepends=True)
ix=next(i for i,x in enumerate(parts) if x.startswith(b'| 06 |'))
ending=b'\r\n' if parts[ix].endswith(b'\r\n') else b'\n'
row='| 06 | Публичный каталог, поиск, фильтры и карта | DONE — FAIL (fresh audit complete; limits NOT RUN) | C:\\kidsmap; task33-progress; 8d188b316f800fbedf0b1e376905dfd4924cb1b6; dirty QA/docs; active_run NONE unchanged; runtime WORKTREE + existing .mo | [Отчёт](module06-2026-10-10-r1/REPORT.md), [verification](module06-2026-10-10-r1/verification.json), [matrix](module06-2026-10-10-r1/matrix.csv), [screenshots](module06-2026-10-10-r1/screenshots-manifest.json) | 4 OPEN PUBLIC-QA (3 app P2, 1 environment P3); Django93 methods:92 PASS, 1 method/2 subtest FAIL; JS6/6 PASS; 616 native PNG +13 DERIVED; SDK/conflicts/shared cache NOT RUN; foreign ledger drift recorded, no rollback; Далее07; [handoff](module06-2026-10-10-r1/next-chat.txt) |'
old=parts[ix];parts[ix]=row.encode('utf-8')+ending
if parts[ix]!=old:
 assert b'NOT RUN |' in old, 'Row06 already changed by another actor; preserve it for review'
 journal.write_bytes(b''.join(parts))
assert all(a==b for n,(a,b) in enumerate(zip(before.splitlines(keepends=True),journal.read_bytes().splitlines(keepends=True))) if n!=ix)
print(json.dumps({'browser_attempts':len(ledger),'native_cli_exits':dict(collections.Counter(x['cli_exit_code'] for x in ledger)),'journal_line':ix+1,'native_png':summary['screenshots']['NATIVE rendered Chromium screenshot']},ensure_ascii=True))
