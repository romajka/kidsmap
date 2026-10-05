"""Publish audit pointers without rewriting historical stage evidence."""
import json,hashlib,shutil,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT/'docs/task33/final-audit'
def read(name):return json.loads((OUT/name).read_text(encoding='utf8'))
entry=read('entry.json');browser=read('browser-results.json');image=read('image-full-r2-results.json')['suite-results.json']
assert browser['status']not in {'RUNNING','IN_PROGRESS','PENDING'} and browser['contexts']>=798
assert read('report-render.json')['status']=='PASS'
assert read('report-render.json')['report_sha256']==hashlib.sha256((OUT/'report.html').read_bytes()).hexdigest()
assert read('report-validation.json')['status']=='PASS'
assert read('final-verification.json')['status']=='PASS'
assert (OUT/'domain-review.md').is_file()
master=ROOT/'docs/agent-audits/MASTER_AUDIT.md'
additional=OUT/'additional-preservation.json'
if not additional.exists():
    dest=Path(entry['snapshot'])/'additional/docs/agent-audits/MASTER_AUDIT.md'
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(master,dest)
    record={'files':[{'path':'docs/agent-audits/MASTER_AUDIT.md','snapshot':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}]}
    additional.write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
summary=f'Итоговый сквозной аудит 2026-10-04 завершён: рассмотрены все 28 этапов и 306 требований. Основная система реализована, окончательная полнота задумки НЕ подтверждена: taxonomy/search gap, красная регрессия, UI-дефекты и внешние release gates. Fresh host 1817: 109F/11E, Task33 579/580; exact image 1817: {image["failures"]}F/{image["errors"]}E; browser {browser["status"]}: {browser["contexts"]} contexts, {browser["passed_checks"]}/{browser["checks"]} checks. Native recovery 98 tables / 25 public + 2 private files PASS. Application fixes/commit/push/production NOT_RUN.'
readme=ROOT/'docs/task33/README.md';text=readme.read_text(encoding='utf8')
pointer='\n> **Последняя проверка — 4 октября 2026.** '+summary+' [Подробный отчёт и roadmap](final-audit/REPORT.md) · [HTML со скриншотами](final-audit/report.html).\n\nИсторическое закрытие этапа 28 (цифры ниже относятся к предыдущему запуску):\n'
if '**Последняя проверка — 4 октября 2026.**' not in text:
    pos=text.index('\n**28 самостоятельных');text=text[:pos]+pointer+text[pos:];readme.write_text(text,encoding='utf8')
status=ROOT/'docs/task33/implementation-status.md';text=status.read_text(encoding='utf8');lines=text.splitlines()
for i,line in enumerate(lines):
    if line.startswith('Текущий snapshot:'):lines[i]='Текущий snapshot: '+summary+' Evidence: final-audit/REPORT.md. Исторические DONE этапов ниже сохранены и не означают отсутствие долга.'
    if line.startswith('active_run:'):lines[i]='active_run: NONE — comprehensive audit closed; implementation follow-up not started.'
    if line.startswith('current_scope:'):lines[i]='current_scope: AUDIT_COMPLETE_WITH_FINDINGS; all28 reviewed; recommendations only; application/production read-only.'
text='\n'.join(lines)+'\n';heading='## Итоговый сквозной аудит 2026-10-04'
if heading not in text:text+='\n'+heading+'\n\n'+summary+'\n\nСохранены все 545 исходных dirty paths и binary patch; 218 source hashes предыдущего приёмочного snapshot проверены. Все первоначальные неудачные попытки и новые результаты сохранены. [Отчёт](final-audit/REPORT.md), [HTML](final-audit/report.html), [306 требований](final-audit/REQUIREMENTS.md), [Проверка сохранности](final-audit/final-verification.json). Следующий шаг — согласование конкретного объёма исправлений из roadmap.\n'
status.write_text(text,encoding='utf8')
text=master.read_text(encoding='utf8');prefix='> **Последний аудит Task33: 2026-10-04.** '
if not text.startswith(prefix):master.write_text(prefix+summary+' [Итоговый отчёт](../task33/final-audit/REPORT.md) · [HTML / screenshots](../task33/final-audit/report.html).\n\n---\n\n'+text,encoding='utf8')
plan=OUT/'PLAN.md';plan.write_text(plan.read_text(encoding='utf8').replace('- [ ]','- [x]'),encoding='utf8')
(OUT/'closure.json').write_text(json.dumps({'status':'AUDIT_COMPLETE_WITH_FINDINGS','closed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'run':entry['run'],'production':'NOT_CONTACTED','application_fixes':'NONE','next_work':'Separate agreed scope from report roadmap'},indent=2)+'\n',encoding='utf8')
print(summary)
