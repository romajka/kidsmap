"""Write current-run reports and current07 status only after semantic GREEN."""
import collections,hashlib,json,struct,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];O=R/'docs/qa/module07-full-2026-10-15-r1';A=R/'docs/qa/module07-accept-2026-10-15-r2';S=R/'.tmp'/H.name
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
raw_green=read(H/'native-GREEN.js.result.json');status_proof=read(H/'status-recheck.js.result.json')
qa_fail=[r for r in raw_green['rows']if r['status']!='PASS'];assert len(qa_fail)==18 and all(r['id']=='signed private status rendered'and r['status']=='FAIL'for r in qa_fail)
assert len(status_proof['rows'])==18 and all(r['status']=='PASS'for r in status_proof['rows'])and not status_proof['diagnostics']
(H/'oracle-provenance.json').write_text(json.dumps({'raw_18_FAIL_retained':qa_fail,'reason':'QA script expected /account/deletion/status/, but canonical route is /account/deletion/<uuid>/status/. Original data/assertions preserved; no application changes for this QA mismatch.','source':'src/catalog/urls.py:176','stronger_separate_browser_proof':'status-recheck.js.result.json','proof_limit':status_proof['limit'],'existing_test_assertions_changed':False},indent=2))
green={**raw_green,'rows':[{**r,'script':'native-GREEN.js'}for r in raw_green['rows']if r['status']=='PASS']+[{**r,'script':'status-recheck.js'}for r in status_proof['rows']]}
counts=dict(collections.Counter(r['status']for r in green['rows']));cells={(r['lang'],r['width'])for r in green['rows']};expected={(l,w)for l in('ru','az','en')for w in(360,390,768,1024,1280,1440)}
assert counts=={'PASS':684}and cells==expected and green['source_strip']is False
assert read(H/'target-GREEN.status.json')['exit']==0 and 'Ran 11 tests'in(H/'target-GREEN.output.txt').read_text()
assert not A.exists();A.mkdir()
(H/'accepted-observations.json').write_text(json.dumps({'counts':counts,'cells':sorted(cells),'rows':green['rows'],'meaning':'observations, not684independent tests; initial fixture setup separate from native login/deletion'},ensure_ascii=False,indent=2))
images=[]
for p in sorted((H/'screenshots').glob('*.png')):
 b=p.read_bytes();width,height=struct.unpack('>II',b[16:24]);images.append({'path':str(p.relative_to(H)),'bytes':len(b),'sha256':sha(p),'width':width,'height':height,'phase':'RED'if p.name.startswith('red-')else'GREEN'})
assert len(images)==134
(H/'png-manifest.json').write_text(json.dumps(images,indent=2))
server=read(H/'server.json');source=json.load(urllib.request.urlopen(server['url']+'/qa/source/',timeout=15));state=json.load(urllib.request.urlopen(server['url']+'/qa/state/',timeout=15))
(H/'runtime-source-final.json').write_text(json.dumps(source,ensure_ascii=False,indent=2));(H/'state-final.json').write_text(json.dumps(state,indent=2))
entry=read(H/'entry.json');retained={p:d for p,d in entry['files'].items()if p.startswith(str(O.relative_to(R))+'/')};baseline=read(O/'runtime-source-baseline.json');current=read(H/'runtime-source-baseline.json')
changed=[p for p in baseline if current.get(p)!=baseline[p]];new=sorted(set(current)-set(baseline));assert changed==['src/catalog/forms.py']and new==['src/catalog/testcases/test_access_qa06_deletion_phrase.py']
(A/'retained-evidence.json').write_text(json.dumps({'previous_full_run':str(O),'all_previous_full_artifacts_sha256':retained,'previous_audit_completed':read(O/'verification.json')['audit_completed'],'historical_decision':read(O/'verification.json')['module_decision'],'retained_existing_unique_backend_methods':338,'retained_native_PASS_observations':2232,'historical_ACCESS06_native_FAIL_not_deleted':6,'old_source_count':len(baseline),'unchanged_sources':len(baseline)-len(changed),'changed_source_paths':changed,'new_source_paths':new,'current_source_count':len(current),'fresh_target_validation':str(H),'full_unchanged_corpus_rerun':False},indent=2))
combined=[]
for parent,group in [(O,'retained previous full audit'),(H,'fresh ACCESS06 target')]:
 for row in read(parent/'png-manifest.json'):combined.append({**row,'path':str((parent/row['path']).relative_to(R)),'evidence_group':group})
(A/'png-manifest.json').write_text(json.dumps(combined,indent=2))
# Update only current07 status; historical counts/evidence remain.
g=R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md';before=g.read_text();line=next(x for x in before.splitlines()if x.startswith('- Module07 полная ACCEPT-07 —'))
note='- Module07 текущая сводная ACCEPT-07 — **LOCAL PASS / ACCESS-QA-01–06 CLOSED LOCAL**, 2026-10-15: [итоговый отчёт](module07-accept-2026-10-15-r2/REPORT.md), [verification](module07-accept-2026-10-15-r2/verification.json). ACCESS06 исправлен по отдельному одобрению: одна строка strip=False в forms.py +новые4regression methods; свежие4RED(24subfailures)→GREEN,7existing target methods PASS,684native observations PASS/18cells,134PNG с RED evidence. Существующий полный корпус338methods/2232nativePASS retained по hashes, повторно целиком не запускался. Исторический full-r1 LOCAL FAIL сохранён: его06закрыт свежим fix-run.03=ORG02 без повторного patch. Сохранность/процессы/изоляция подтверждаются gate; прежняя continuity четырёх старых HTTP остаётся NOT VERIFIED. Production/module08 NOT RUN.'
old=line+'\n';newtext=old+note+'\n';assert before.count(old)==1
oldrow='| 07 Аккаунты, команда, права и приватность | 5 | 4 | [Задачи](#m07) · [ACCEPT-07](#accept07) · [LOCAL FAIL:06 OPEN](module07-full-2026-10-15-r1/REPORT.md) · [PLAN06](module07-full-2026-10-15-r1/PLAN-ACCESS-QA-06.md) |'
newrow='| 07 Аккаунты, команда, права и приватность | 5 | 4 | [Задачи](#m07) · [ACCEPT-07](#accept07) · [LOCAL PASS:01–06](module07-accept-2026-10-15-r2/REPORT.md) · [исторический full-r1](module07-full-2026-10-15-r1/REPORT.md) |'
assert before.count(oldrow)==1;after=before.replace(old,newtext,1).replace(oldrow,newrow,1)
(H/'guide-edits.json').write_text(json.dumps({'path':str(g.relative_to(R)),'before_sha256':sha(g),'edits':[{'before':old,'after':newtext},{'before':oldrow,'after':newrow}]},ensure_ascii=False,indent=2));g.write_text(after)
report='''# ACCESS-QA-06 — scoped LOCAL PASS

Одобрение пользователя «одобряю» относится к [точному плану](../module07-full-2026-10-15-r1/PLAN-ACCESS-QA-06.md); [SHA/scope](approval.json). Новый run2026-10-15. Реализация только в двух согласованных application-файлах.

## Что исправлено

`src/catalog/forms.py:907`: добавлен strip=False только полю AccountDeletionConfirmForm.typed_confirmation. До patch форма отрезала крайние пробелы, после — передаёт буквальную строку строгому сервису. Неточная фраза теперь даёт400 и сохраняет активный аккаунт/код. Новый `src/catalog/testcases/test_access_qa06_deletion_phrase.py` — ровно предложенные4метода,91строка. Другие поля, сервис/фразы/PO/JS/CSS/views/sessions/retention не менялись. [Точный inverse](inverse-proof.json) возвращает entry-байты dirty forms.py, сохраняя чужие изменения.

## Snapshot и среда

Root /home/ramin/kidsmap; HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51; branch task33-progress; dirty WORKTREE; active_run NONE. [Entry](entry.json):29682project files,63foreigncontainers,2knownHTTP. Entry mode label was inherited from the audit capture helper; [explicit metadata correction](entry-mode-correction.json) links the actual APPROVED IMPLEMENT authority. Original entry unchanged. Один исполнитель последовательно выполнял канонические orchestrator/django-reviewer/browser-qa/integration проверки; независимые специалисты не заявляются. Skills debugging/TDD/verification/Playwright, прежний concrete plan и docs сохранены.

DJANGO_TESTING=1; собственные PG41859/HTTP39199, DB/user access06_fix_r1/container+volume access-qa06-fix-2026-10-15-r1-pg; отдельные cache/media/private-media/filebased email+private mail journal. ENV очищен до setup, checkout .env не загружался; Python socket guard допускает только свой PG; browser blocks external origin. Host-wide firewall не заявляется. Только SIMULATED TEST_POLICY, production default остаётся inactive. [Runtime](runtime-info.json):Python3.12.3/Django6.0.2/pypdf6.20.1,175migrations. Exact pypdf скопирован в собственный python-deps/venv; shared environment не менялась. [Dependency hashes](dependency-manifest.json).

Fresh current RU/AZ/EN PO собраны builder→собственные MO, build0/verify0. [Manifest](locale-manifest.json); sole LOCALE_PATHS до django.setup, actual opened own3MO в [source](runtime-source-final.json). Shared MO не перезаписаны. Свой prepatch HTTP остановлен только после argv/cwd/PID check; после patch новый own interpreter загрузил strip=False. Source943paths/cached template/module origins/runtime dependency сверяются final gate. Чужие HTTP не перезапускались.

## RED → GREEN и точные проверки

[Fresh RED](regression-RED.status.json):4новых метода в app test-file,24ожидаемых subtestFAIL,0ERROR;66.607s process/29.266s tests. [Native RED](native-RED.js.result.json):RU390,5controlPASS/1sourceFAIL; raw padded string реально отправлена с кодом собственного письма, HTTP302/account inactive/SCHEDULED. Prepatch app field strip=True. Это fresh reproduction, не перенос старого FAIL.

[Target GREEN](target-GREEN.status.json):те же4метода без изменения assertions плюс прежние7целевых deletion tests,11/11PASS,exit0;89.292s process/45.341s tests. Проверены exact/raw HTTP/form, code hash/attempts, correct/wrong code, sessions, cancellation/reset requirement, signed status/foreign-user boundaries. [Selectors](GREEN-selectors.json). [Form guards](form-guards.json):12/12PASS required/max_length/exact/padded в RU/AZ/EN, без DB writes. Existing assertions не ослаблялись.

[Accepted native](accepted-observations.json):684PASS,0FAIL/0NOT RUN,18cells RU/AZ/EN×360/390/768/1024/1280/1440. Все18начинаются с собственных initial verified fixtures; registration не объявляется заново проверенной. Затем реальные UI login→deletion request→local mail. Leading/trailing/both/NBSP дают400/локализованную typed error, сохраняют исходную строку и код/активность/5attempts. Tab/Shift+Tab/visible focus и Enter; ошибки и геометрия. Exact phrase+wrong code400/4attempts; exact+valid302/SCHEDULED/inactive/code consumed, signed status, old-session denial. Последний unauthenticated replay POST не меняет состояние; это не отдельный сервисный replay при авторизованной сессии. State19SCHEDULED включает1сохранённый prepatch RED fixture и18GREEN; final processor в fix-run NOT RUN.

[QA oracle provenance](oracle-provenance.json): original native-GREEN JSON retains666PASS/18FAIL caused only by the wrong status-URL expectation. Separate status-recheck renders all18already UI-scheduled accounts at canonical signed URLs, tests missing/bad token404 and no mutation. Its18PASS replace only these QA observations in accepted684; no new native redirect proof is claimed.6new status PNGs retained.

[134PNG manifest](png-manifest.json):2RED+126GREEN+6read-only-status; нативная mask только поля кода, без DOM/CSS edits. Code сохранён приватно до mask, реальные mail bodies/passwords/tokens не включаются. Manual visual scope в [visual-review](visual-review.json); не заявляется просмотр каждого134PNG. Console/pageerror/network по каждой18cell: фактические expected HTTP400 errors и заблокированные external fonts отдельно от локальных сбоев, [diagnostics](native-GREEN.js.result.json). [Commands/exits](commands.jsonl), driver consumes actual JS text, а ledger `<path>` — ссылка на template, не literal CLI argument; собственная сессия access06fixr1green, private credential lookup только в памяти.

## Сохранность и решение

[Gate](verification.json) проверяет exact inverse формы/guide, новый test byte-match approved proposal, HEAD/branch/active_run,29682baseline files, sharedMO,63container ID/name/ports/state и2knownHTTP identity, own runtime source, semantic GREEN,PNG hashes и secret scan. Предыдущие full-r1/repair отчёты не переписаны. Четыре более старых HTTP отсутствовали ещё до full-r1: continuity остаётся NOT VERIFIED, не восстановлена задним числом.

ACCESS-QA-06 CLOSED LOCAL только по проверенному scope. [Текущая сводная приёмка модуля](../module07-accept-2026-10-15-r2/REPORT.md) сохраняет полную предыдущую приёмку по hashes;338неизменённых методов не гонялись повторно. Natural retention/backup expiry, real OAuth/SMTP, production/commit/push/deploy, cross-browser/real screen reader, module08/global corpus NOT RUN.
'''
(H/'REPORT.md').write_text(report)
summary='''# Module07 — LOCAL PASS, сводная ACCEPT-07

2026-10-15. ACCESS-QA-01–06 CLOSED LOCAL в фактически проверенных границах;03=ORG-QA-02 alias. Это сводная приёмка после отдельно одобренного06fix, с сохранённым полным корпусом. Production не проверялся, module08 не начат.

## 1. Snapshot

Root /home/ramin/kidsmap; HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51; branch task33-progress; dirty WORKTREE; active_run NONE. [Fresh entry](../access-qa06-fix-2026-10-15-r1/entry.json). Один исполнитель, канонические роли последовательно; независимый запуск специалистов не заявляется.

## 2. Основание полной приёмки

Полная [ACCEPT full-r1](../module07-full-2026-10-15-r1/REPORT.md) выполнена один раз и сохранена неизменённой. Её LOCAL FAIL был честным историческим решением: новый06оставался OPEN. Сейчас06закрыт свежим [approved fix](../access-qa06-fix-2026-10-15-r1/REPORT.md); прежние raw FAIL не удалены. [Retained evidence/source hashes](retained-evidence.json) фиксируют все предыдущие full-run artifacts. Из942источников941не изменился; единственный изменённый источник — одно поле forms.py; добавлен один test-file. Текущий943source provenance проверен новым процессом. Повторный неизменившийся full corpus не запускался по правилу пользователя.

## 3. ID и изменения

01 — reset modal focus/restore/approved outline;02 — invitations decline/replay/ACL;03=ORG02 — ранее принятый org scope;04 — team responsive controls;05 — четыре одобренные AZ/EN PO entries;06 — буквальная точная фраза на HTTP/form boundary. [Таблица и repair links](FINDINGS.md). В последнем fix только strip=False +новые4метода; логика кода, сессий, retention, views/JS/CSS/PO не расширялась.

## 4. Backend

338unique existing methods PASS в полном retained run, включая8targeted retries после изолированного dependency repair. Не считать их заново запущенными на последней форме. На текущем source11target methods PASS:4новых+7existing (эти7входят в338); отдельно12formguard observations PASS. Всего342уникальных method IDs в combined evidence, а не349свежих тестов. Fresh new4RED дали24source subtestFAIL без ERROR до patch; затем те же4GREEN. [Exact exits/selectors/output](../access-qa06-fix-2026-10-15-r1/GREEN-selectors.json), [backend inventory old](../module07-full-2026-10-15-r1/backend-verification.json).

## 5. Native browser и матрицы

Retained2232accepted PASS observations покрывают module auth/account/team/roles/URL/API/private documents/own local reset+new password+link replay, RU/AZ/EN responsive14states×6widths, native lifecycle and failures; подробная роль×действие×сущность [матрица](../module07-full-2026-10-15-r1/role-action-entity-matrix.csv). Сохранённые6sourceFAIL относятся только к06и теперь перекрыты fresh target proof.

Fresh684PASS observations:18cells RU/AZ/EN×360/390/768/1024/1280/1440, настоящий UI login/request/mail,72padded submissions refused400 с сохранением raw input/code/active state/attempts, keyboard/focus/Enter/error locale/geometry, wrong-code and correct-code controls, signed status/old-session denial. [Rows and cells](../access-qa06-fix-2026-10-15-r1/accepted-observations.json). Initial verified fixtures — setup, а не fresh signup proof. Полный Cartesian product каждого role/state/width не заявляется.

Original target native JSON keeps666PASS/18QA-FAIL from an incorrect status-route expectation. [Oracle provenance](../access-qa06-fix-2026-10-15-r1/oracle-provenance.json) preserves them; separate real browser signed-status probe18PASS (valid200, no/bad token404, no mutation) resolves only that QA gap. It uses canonical signed URLs for already UI-scheduled fixtures, not a new native transition. No application/test assertions were weakened.

## 6. PNG / console / network

[758PNG manifest](png-manifest.json):624retained full-audit attempts +134fresh target (2RED/126GREEN/6read-only-status). Это сохранённые frames/attempts, не758независимых accepted states и не ручной просмотр каждого кадра. Предыдущие oracle caveats/duplicate overwrites сохранены в full-r1; их не переклассифицировали в source PASS. Новые code fields закрыты только native screenshot mask. [Manual selected visual review](../access-qa06-fix-2026-10-15-r1/visual-review.json). Pageerror/local request failures и expected400/external-block diagnostics отделены в native JSON; не заявляется clean console всего хоста.

## 7. Isolation / privacy / retention

Новый собственный DJANGO_TESTING=1 профиль PG41859/HTTP39199/DB access06_fix_r1 с отдельными cache/media/private-media/local email; clean env без checkout .env/production credentials. Fresh RU/AZ/EN MO/manifest/sole path до setup; loaded ownMO3, own pypdf6.20.1/source/template origins. Shared MO/env не перезаписаны. Policy только SIMULATED, production default inactive. Retained full-run own reset/mail, document ACL/consent/finalization proof сохранены:5actual-now skips и5SIMULATED future completed,6private docs retained for authorized reviewers. Natural retention/backup expiry не доказаны.

## 8. Сохранность и NOT RUN

Финальный [gate](verification.json) сверяет29682entry files (кроме exact approved forms/current-guide changes), новый exact test, sharedMO, HEAD/branch/active_run,63foreigncontainers/2knownHTTP identities, старые full artifacts и current source. Никаких reset/clean/stash/active_run assignment/foreign restart. Четыре более старых HTTP были утрачены до full entry; continuity по ним остаётся NOT VERIFIED. Это не доказательство произвольных host-process/production health.

NOT RUN: production/deploy/commit/push, module08/global acceptance, повтор338unchanged corpus, fresh full auth/team/private-doc matrix после one-field patch, real external OAuth/SMTP/integrations, natural30days/legal/backup policy, cross-browser/real screen reader/OS-popup pixels. Unchanged module evidence retained by hashes, affected boundary covered fresh; LOCAL PASS ограничен этим составом evidence.

## 9. Решение и handoff

ACCESS-QA-01–06 CLOSED LOCAL; module07 LOCAL PASS. Старые отчёты и неуспешные проверки сохранены. [Next prompt](next-prompt.txt) фиксирует завершение, модуль08только по отдельному запросу. Полные counts/commands/exits и source/preservation checks — в linked fix/full reports и verification. Local pass не равен production state.
'''
(A/'REPORT.md').write_text(summary)
(A/'FINDINGS.md').write_text('''# Текущие ID модуля07

| ID | Статус | Основание |
|---|---|---|
| ACCESS-QA-01 | CLOSED LOCAL | [fix](../access-qa01-fix-2026-10-14-r1/REPORT.md), full-r1 retained |
| ACCESS-QA-02 | CLOSED LOCAL | [fix](../access-qa02-fix-2026-10-15-r1/REPORT.md), full-r1 retained |
| ACCESS-QA-03 = ORG-QA-02 | CLOSED LOCAL alias | [module02](../module02-full-2026-10-13-r2/REPORT.md), без повторного исправления |
| ACCESS-QA-04 | CLOSED LOCAL | [fix](../access-qa04-fix-2026-10-15-r1/REPORT.md), full-r1 retained |
| ACCESS-QA-05 | CLOSED LOCAL | [fix](../access-qa05-fix-2026-10-15-r1/REPORT.md), four PO entries |
| ACCESS-QA-06 | CLOSED LOCAL | [fresh RED→GREEN approved fix](../access-qa06-fix-2026-10-15-r1/REPORT.md),11target methods/684nativePASS |

Новых OPEN findings в выполненном scope нет. Исторические FAIL и NOT RUN не удалены; production/global/module08 не принимались.
''')
(A/'next-prompt.txt').write_text('''KidsMap module07 завершён LOCAL PASS в docs/qa/module07-accept-2026-10-15-r2/REPORT.md и verification.json. ACCESS01–06 CLOSED LOCAL;03=ORG02 alias. Full corpus338existing methods/2232nativePASS retained from module07-full-2026-10-15-r1; last approved06fix11target methods/684nativePASS свежие. Исторический full-r1 FAIL сохранён, новый06закрыт source/provenance evidence. Не повторяй338unchanged автоматически.

Checkout /home/ramin/kidsmap, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51, task33-progress, dirty WORKTREE, active_run NONE — перепроверь. Сохрани чужие файлы/services/artifacts; без reset/clean/stash/commit/push/deploy/production/active_run assignment. Четыре более старых HTTP continuity NOT VERIFIED; не заявляй обратное. Текущий собственный06стенд PID/argv/source смотри fresh server.json и проверяй live, не доверяй старым портам.

Module08 автоматически не начинать. Для нового модуля — отдельный запрос пользователя, canonical AGENTS/registry/role/knowledge/audit-contract/current guide и новый PLAN/approval для конкретной причины. Статусы прежних модулей — LOCAL, не production. Isolated current RU/AZ/EN MO manifest/sole LOCALE_PATHS до setup, clean DJANGO_TESTING=1 own PG/DB/cache/media/private-media/email, без .env/production credentials. Точные будущие инструкции брать из актуального guide после запроса пользователя.
''')
(H/'artifact-generation.json').write_text(json.dumps({'green_observations':len(green['rows']),'native_cells':len(cells),'PNG':len(images),'summary_png':len(combined),'summary':str(A),'retained_artifacts':len(retained),'guide_exact_edits':2},indent=2))
print(json.dumps({'reports_written':True,'target_rows':len(green['rows']),'summary':str(A),'module08_started':False}))
