"""Close only this approved run after all evidence and rendered report pass."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path('/mnt/c/kidsmap');OUT=ROOT/'docs/task33/completion'
v=json.loads((OUT/'final-verification.json').read_text())
render=json.loads((OUT/'report-checks/results.json').read_text())
assert v['status']==render['status']=='PASS' and not render['errors']
assert (OUT/'REPORT.md').is_file() and (OUT/'report.html').is_file()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==v['head_unchanged']
status=ROOT/'docs/task33/implementation-status.md';s=status.read_text()
s=s.replace('Checkpoint completion #2,','Исторический checkpoint completion #2,').replace('Checkpoint completion,','Исторический checkpoint completion,')
active='active_run: completion-20261004-095717Z — /root kidsmap-orchestrator; APPROVED IMPLEMENT points1–5.'
assert s.count(active)==1,'Only the owning active_run may be closed'
summary=f"Пункты 1–5 принятого плана завершены локально 2026-10-04. Полные PostgreSQL host/image: по1844,0F/0E/0skip;120/120 исходных записей регрессии закрыты в обоих наборах. JS30/30; Chromium861 контекст,{v['browser_checks']} проверок, неожиданных ошибок0; native restore98tables/25public+2privatefiles PASS. Сохранены710 входных файлов; final-audit164/164 побайтно неизменны. Production/commit/push/deploy NOT_RUN; эксплуатационная готовность — отдельный пункт6. Новые доказательства: completion/REPORT.md, completion/report.html, completion/final-verification.json."
lines=s.splitlines()
for index,line in enumerate(lines):
    if line.startswith('Текущий snapshot:'):lines[index]='Текущий snapshot: '+summary
    elif line==active:lines[index]='active_run: NONE'
    elif line.startswith('current_scope:'):lines[index]='current_scope: completion points1–5 DONE locally; no active implementation; production remains separate point6.'
    elif line.startswith('source_head:'):lines[index]='source_head: '+v['head_unchanged']+'; branch task33-progress; C:\\kidsmap; dirty WORKTREE preserved; completion/final-verification.json. No commit/push/merge/deploy.'
s='\n'.join(lines)+'\n'
s+='\n## Завершение completion 1–5 — 2026-10-04\n\n'+summary+'\n\n'
s+='Run `completion-20261004-095717Z`, APPROVED IMPLEMENT по прямому плану пользователя. Миграция0134: три nullable FK;168applied/0pending, check/makemigrations и guards/cleanup PASS. Детерминированные transfer/join success/conflict/retry и crash/outbox проверки включены в оба полных набора. Финальная интеграция, browser и release/recovery выполнены root последовательно после остановки вспомогательных исполнителей; независимое финальное ревью не заявляется.\n\n'
s+='Новый image `'+v['image_id']+'`; artifact `'+v['artifact_identity']+'`. Host/image/browser сверены с теми же '+str(v['current_host_image_browser_application_files'])+' application-файлами. Старый образ сохранён. Документ аналитики передан в образ отдельным SHA-проверенным read-only QA-входом; приложение не подменялось. Native recovery читает frozen APP через внешний read-only QA reader с SHA и сверкой2803 файлов до/после.\n\n'
s+='Сквозной browser выявил и подтвердил исправление500 смешанной очереди Program/Place; сохранены RED и финальный GREEN. Неудачные backend/JS/browser/recovery attempts перечислены в новом отчёте и сохранены отдельно.30 свежих PNG плюс проверки HTML-отчёта; таблицы всех28 этапов и120problem entries. Все финальные процессы завершены и их временные ресурсы очищены; active_run освобождён. Production, реальные внешние сервисы, commit/push/deploy не выполнялись.\n'
status.write_text(s)
readme=ROOT/'docs/task33/README.md';s=readme.read_text()
marker='> **Последняя проверка — 4 октября 2026.**';assert marker in s
s=s.replace(marker,'> **Предыдущий исторический аудит — 4 октября 2026.**',1)
position=s.index('> **Предыдущий исторический аудит')
s=s[:position]+'> **Завершение пунктов 1–5 — 4 октября 2026.** '+summary+' [Новый подробный отчёт](completion/REPORT.md) · [HTML: roadmap, 120 замечаний и 30 скриншотов](completion/report.html).\n\n'+s[position:]
readme.write_text(s)
plan=OUT/'PLAN.md';plan.write_text(plan.read_text().replace('- [ ]','- [x]')+'\nFinal: все пункты подтверждены completion/final-verification.json и rendered report-checks/results.json. Root final execution sequential; active_run closed.\n')
(OUT/'README.md').write_text('# KidsMap №33 — завершение 1–5\n\n'+summary+'\n\n- [Подробный отчёт](REPORT.md)\n- [HTML с поиском, roadmap и скриншотами](report.html)\n- [Все120 исходных замечаний](regression-ledger.md)\n- [Финальная сверка исходников и результатов](final-verification.json)\n- [Изолированные команды воспроизведения](REPORT.md#неудачные-попытки-и-воспроизведение)\n\nАрхив final-audit не изменён. Raw синтетические evidence: /root/task33-evidence/completion-*.\n')
manifest=[]
for p in sorted(OUT.rglob('*')):
    if not p.is_file() or '__pycache__' in p.parts or p.name=='evidence-manifest.json':continue
    manifest.append({'path':p.relative_to(OUT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(OUT/'evidence-manifest.json').write_text(json.dumps({'files':manifest,'historical_audit_modified':False,'production':'NOT_CONTACTED'},indent=2)+'\n')
print(json.dumps({'active_run':'NONE','completion':'DONE_LOCALLY','evidence_files':len(manifest)}))
