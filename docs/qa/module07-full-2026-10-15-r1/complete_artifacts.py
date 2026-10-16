"""Finalize only this run's documentation; no application changes."""
import hashlib,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
accepted=json.loads((H/'accepted-observations.json').read_text())
commands=[json.loads(x)for x in(H/'commands.jsonl').read_text().splitlines()if x.strip()]
script_rows=[]
for name in accepted['selected_scripts']:
 p=H/name
 receipts=[x for x in commands if x.get('name')==name]
 script_rows.append({'script':name,'template_sha256_at_final':sha(p),'reproducible_driver_argv':[str(R/'.venv/bin/python'),str(H/'browser_run.py'),name],'driver_receipt':name+'.status.json','result':name+'.result.json','recorded_invocations':receipts})
provenance={'native_browser':'Chromium 149.0.7827.55','browser_executable':'/home/ramin/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome','session':'module07fullr1green','wrapper':'/home/ramin/.codex/skills/playwright/scripts/playwright_cli.sh','driver_chain':['browser_run.py','drive.py','playwright_cli.sh -s=module07fullr1green run-code <actual JS text>'],'driver_hashes':{n:sha(H/n)for n in('browser_run.py','drive.py')},'private_substitution':'drive.py reads template then substitutes __EXPIRED_CODE__ from own ignored expired-code in memory. Password/codes are fetched within JS from loopback own QA fixture/mail endpoints; no secret returned in semantic results. Actual argument is JS text, not the displayed <script-path> ledger placeholder. Restricted scratch retains sanitized raw output.','hash_limit':'Template hashes captured at final verification; no independent at-execution content attestation is claimed. Earlier same-named retries and overwritten PNGs are not counted as separate immutable proofs.','reproduction_limit':'Commands reproduce the driver on a fresh owned prepared profile. Stateful fixtures are consumed; do not rerun them against this final-state DB. Initial queue and subsequent recovery/post queues are linked in REPORT; selected results define accepted scope.','scripts':script_rows}
(H/'browser-command-provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2))
guide=R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md'
text=guide.read_text();edits=[]
line=next(x for x in text.splitlines()if x.startswith('- Module07 ACCESS-QA-05 —'))
added='- Module07 полная ACCEPT-07 — **LOCAL FAIL / ACCESS-QA-06 OPEN**, 2026-10-15: [свежий отчёт](module07-full-2026-10-15-r1/REPORT.md), [verification](module07-full-2026-10-15-r1/verification.json). Исторические ACCESS01–05 CLOSED LOCAL;03=ORG02 без повторного patch. 338 existing unique backend methods PASS;2232 native observations PASS/6 source FAIL,624 PNG including retained attempts. Новый06: форма обрезает крайние пробелы точной фразы удаления; [минимальный отдельный PLAN](module07-full-2026-10-15-r1/PLAN-ACCESS-QA-06.md) и готовый diff пока не применены/не одобрены. ACCEPT app0changes, собственные изолированные services/locales, SIMULATED policy/future clock. Entry files/sharedMO/HEAD/active_run/62containers/1known HTTP сверены; прежняя непрерывность четырёх исчезнувших HTTP остаётся NOT VERIFIED. Исторические числа таблицы сохранены; production/module08 NOT RUN.'
old=line+'\n';new=old+added+'\n'
assert added not in text and text.count(old)==1
edits.append({'before':old,'after':new});text=text.replace(old,new,1)
old='| 07 Аккаунты, команда, права и приватность | 5 | 4 | [Задачи](#m07) · [ACCEPT-07](#accept07) |'
new='| 07 Аккаунты, команда, права и приватность | 5 | 4 | [Задачи](#m07) · [ACCEPT-07](#accept07) · [LOCAL FAIL:06 OPEN](module07-full-2026-10-15-r1/REPORT.md) · [PLAN06](module07-full-2026-10-15-r1/PLAN-ACCESS-QA-06.md) |'
assert text.count(old)==1
edits.append({'before':old,'after':new});text=text.replace(old,new,1)
assert not(H/'guide-edits.json').exists()
(H/'guide-edits.json').write_text(json.dumps({'path':str(guide.relative_to(R)),'before_sha256':sha(guide),'edits':edits},ensure_ascii=False,indent=2))
guide.write_text(text)
next_prompt='''Продолжаем KidsMap: module07 полная ACCEPT выполнена, LOCAL FAIL / ACCESS-QA-06 OPEN.

Фактический checkout /home/ramin/kidsmap, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51, branch task33-progress, dirty WORKTREE, active_run NONE — перепроверь актуальность. Сохрани чужие файлы/processes/stands/artifacts. Без reset/clean/stash/commit/push/deploy/production/active_run assignment. Module08 не начинать.

Прочитай AGENTS.md, .agents README/registry/реальный orchestrator и применимые роли, architecture/source-of-truth/audit-contract; текущий статус и PLAN/IMPLEMENT-APPROVAL/ACCEPT правила docs/qa/continuation-and-repair-prompts-2026-10-11.md. Не загружай всю библиотеку заданий.

Исторические ACCESS01/02/04/05 CLOSED LOCAL;03=ORG02 принята module02. ACCESS05 в этом запуске исправлен только четырьмя одобренными AZ/EN PO entries: docs/qa/access-qa05-fix-2026-10-15-r1/REPORT.md и verification.json. Не повторять старые fixes.

Полная свежая приёмка: docs/qa/module07-full-2026-10-15-r1/REPORT.md, verification.json, FINDINGS.md. 338 существующих уникальных backend methods PASS. 2232 accepted native PASS/6 source FAIL.624 PNG включают сохранённые попытки, не все вручную просмотрены. Есть подробно раскрытые QA harness/env failures; не считать их отдельными app failures и не скрывать. Полный неизменившийся корпус уже выполнен один раз, не повторять его автоматически.

Новый ACCESS-QA-06 P3: AccountDeletionConfirmForm.typed_confirmation strip=True молча удаляет крайние пробелы до строгой проверки сервиса. Собственный валидный email-code + padded phrase даёт302/SCHEDULED/account inactive вместо400/active. Реальный browser RU/AZ/EN ×390/1440:6FAIL,30controlsPASS. QA-прототип4метода с24ожидаемыми source subtestFAIL и0ERROR. Рабочие коды/письма/пароли/токены — только ignored private scratch.

Сначала покажи и дождись отдельного одобрения PLAN-ACCESS-QA-06.md и proposed-ACCESS-QA-06.diff в этом full-run. На момент отчёта реализация06 НЕ ОДОБРЕНА И НЕ ПРИМЕНЕНА. Точный scope: только одна строка strip=False в src/catalog/forms.py и новый src/catalog/testcases/test_access_qa06_deletion_phrase.py. По уже полученному впоследствии одобрению scope повторно не согласовывать. Новую причину/файлы согласовать отдельно.

После одобрения — собственный fresh fix-run/services/current RU/AZ/EN isolated MO/manifest/sole LOCALE_PATHS до setup и source proof. В shared .venv отсутствовал pinned pypdf6.20.1: full-run имеет свой venv/python-deps с exact dependency, bounded child limits не ослаблялись. Не загружай .env или production credentials. Проверять fresh реальный PID/argv/cwd/container/source, а не старые порты. Full-run последний known server был426689 / HTTP34133,PG42603 own container module07-full-2026-10-15-r1-pg; live identity перепроверить, чужое не перезапускать.

Только целевые tests4GREEN+7existing deletion tests и затронутые сценарии,18nativecells RU/AZ/EN×360/390/768/1024/1280/1440: leading/trailing/both/NBSP, правильный/неверный код, активность/account state/session/typed values/keyboard/errors/console/network/PNG. Не ослаблять expected/validators. Затем новая сводная source-provenance acceptance со ссылкой на retained338методов/общие сценарии; не гонять unchanged full corpus снова. Закрыть06 только по факту. Production/real retention waiting/backup policy/cross-browser/OS-popup pixels остаются NOT RUN.

Сохранность full entry:28813files,62foreigncontainers,1knownHTTP проверяются gate. Четыре более старых HTTP исчезли после прежнего chat interruption до full entry; их continuity NOT VERIFIED, чужие не перезапускались. Не объявлять их сохранёнными ретроспективно.
'''
(H/'next-prompt.txt').write_text(next_prompt)
print(json.dumps({'guide_edits':len(edits),'driver_scripts':len(script_rows),'new_handoff':True,'application_edits':[]}))
