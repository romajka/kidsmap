# Этап25 — Specialist screens, design checkpoint

2026-10-03. **CREATED / REVIEW_PENDING**, revision **specialist-25-r1**. Полный этап25 не DONE: нужны принятие новых макетов, интеграция приложения и проверки её реальных контрактов. Продолжение только в рамках25;26+ NOT_STARTED, production NOT_CONTACTED.

Поручение пользователя: только25 по prompts/25.md, APPROVED IMPLEMENT. Его явная контрольная точка: если новых Specialist screens нет, выполнить независимую design-часть, показать пользователю и начать интеграцию после принятия. Stage24 DONE locally; owner-02-r1 и admin-public-03-r1 приняты2026-09-29, повторное принятие не нужно. Specialist acceptance пока отсутствует.

Checkout **C:\kidsmap**, branch **task33-progress**, LOCAL HEAD **015d031d8eb17114bd860159dde805b38df3c13c**. Исторический /home/ramin/kidsmap адаптирован к Windows checkout и /mnt/c/kidsmap для изолированного браузера WSL. HEAD не является версией dirty приложения21–24. Commit/push/merge/deployment не выполнялись.

## Сохранность и источники

Перед работой сохранены192 dirty/untracked файла и tracked binary patch в ignored scratch snapshot; каждый файл проверен SHA256. [25-entry-manifest.json](25-entry-manifest.json) содержит путь, source hashes и HEAD. Перед передачей повторная проверка: **192/192 сохранены**, **145/145 source artifacts этапа24 неизменны**, включая предыдущие QA helpers. Код приложения, миграции, nginx и принятые макеты этим checkpoint не менялись.

Прочитаны prompt25, README, decisions/D08, implementation-status, architecture/Специалисты/Экраны,24.md и необходимые source symbols; canonical registry/lead/orchestration/audit contracts. active_run был NONE при входе; занят только этим design запуском и снят при передаче.

Codebase Memory у root: index_status/check_index_coverage вернули Transport closed; scoped source fallback. У независимого browser исполнителя index generation2026-10-03T14:52:17Z, rootC:/kidsmap ready, generation_matches/hash_records_complete true; новые specialist design/qa25 пути not_tracked/coverage_unavailable. Это не полная graph coverage новых файлов. Контракты сверены непосредственно с source.

План и границы: [25-plan.md](25-plan.md). Changed source и transitive assets: [25-design-manifest.json](25-design-manifest.json),23 SHA256 artifacts; отчёт не хеширует себя. Остальные изменения этого запуска — acceptance/design README/main README/implementation-status и отчёты25. Separate QA archive не переносится через Git; новые browser evidence созданы отдельно в /root/task33-evidence, без реальных данных и secrets.

## Подготовленный набор

[Галерея](../design/specialist/index.html?lang=ru), [каталог состояний и source references](../design/specialist/README.md). Восемь HTML входов, CSS, JS и README —11 файлов. Существующие local logo/Chiron/MaterialSymbols и accepted Owner tokens, без CDN/API/DB/storage/почты. Люди, организации, документы, даты и ID синтетические; действия только в DOM/query fixtures. File input использует имя/размер, байты не отправляет и не сохраняет.

| Экран | Проверяемое поведение макета |
|---|---|
| Public profile | Специализации/возраст/языки, independent office/online, current и past отдельно; только approved opted-in qualification, identity evidence отсутствует |
| Person editor | Человек редактирует сведения; error/saved/conflict/denied; online сохраняет историю практики |
| Organization | Предложение по stable profile ID, роль/период;0/2,1/2 и2/2 согласий, обе стороны могут быть первыми; бизнес не получает person/docs editor |
| Claim | Отправка pending не создаёт verified ownership; approval только в review, rejected/withdrawn/conflict отдельно |
| Documents | Identity всегда private; qualification choice отдельно от approval; отзыв choice немедленно скрывает public badge, не удаляет приватную запись |
| Dedicated review | Claim и document решения раздельны; ordinary staff denied; reviewer не выбирает публикацию за специалиста |
| Reconciliation | Синтетические ID/старые URL и aggregate, неоднозначность в manual queue; совпадение имени/Place grant не подтверждает личность или сотрудничество |

Relevant source: catalog/models/specialist.py и specialist_domain.py; services/specialist_domain.py:confirm_employment/cancel_employment/review_claim; specialist_documents.py:is_public_document/set_document_public_choice/review_document; owner_specialist_use_cases.py; domain_admin/specialist.py. Source inspection не означает проверку реального ACL макетом.

История хранит фактические прежние согласия0/1/2, роль и исходный период; cancellation03.10.2026 отдельно, отсутствие end_date не превращается в утверждение о текущей работе. Переключение языка сохраняет actor/consent/history fixtures. Public qualification pending/rejected/revoked не присутствует в DOM/action metadata.

## Исполнители и проверки

Lead root frontend-reviewer: scope/source review, entry preservation, выбранные PNG лично просмотрены, manifests/handoff. Отдельный реальный исполнитель frontend-reviewer /root/stage25_design владел только design/specialist; отдельный browser-qa /root/stage25_browser владел qa25 и browser отчётами. Их ownership не пересекался; независимость не приписывается root самопроверке.

Браузер — реальный локальный Playwright Chromium в WSL Ubuntu24.04, cached CLI0.1.22, allowlisted static Python server127.0.0.1:8795, без Django/PostgreSQL/credentials. Exact commands и результаты — [25-browser-review.md](25-browser-review.md), [25-browser-results.json](25-browser-results.json).

Основной frozen проход:

```text
wsl -d Ubuntu-24.04 -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/qa25/run-browser.sh final2-20261003
```

Exit0: **168/168 rendered rows**,8screens×AZ/RU/EN×320/360/390/768/1024/1280/1440; **586/586 checks** =192 responsive state variants +216 actual interaction assertions +168 first keyboard focus checks +10 static preview boundary probes.24 PNG. Console errors, failed/static/external requests0. Raw /root/task33-evidence/stage25-design-final2-20261003; executed JS SHAae981f6024a573e854df303ea0c0ab741f2f1cec28e6a372c2c2cbb210e42151.

После него только copy polish reconciliation/role notices, финальный JS **63fb1de6a5ce7a72535d831b87d569dbbde24c4073613f08364da95a91db6f4a**, без логических/HTML/CSS изменений. Свежий проход:

```text
wsl -d Ubuntu-24.04 -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/qa25/run-browser.sh final-copy-20261003 /mnt/c/kidsmap/docs/task33/qa25/final-copy-keyboard.js
```

Exit0, **78/78 cells +111/111 checks**,48 default cells всех восьми экранов AZ/RU/EN390/1440 и30 denied cells;96 Tab→Enter skip-link,6 Enter reconciliation и9 pending/rejected/revoked public negatives.16 свежих PNG, events0. Captured source snapshot совпал с текущими **11/11** файлами. Root самостоятельно прочитал оба raw results.json через summary.py и повторно сверил source hashes. Основной168-cell проход относится к предыдущему указанному JS, не выдаётся за execution финальной копии.

Root лично просмотрел fresh mobile public profile, mobile organization active, desktop documents, а после final-copy — desktop gallery/reconciliation PNG; current/past, отдельные согласия и private/public label читаемы, бренд/локальные assets отображаются. Root повторил node --check prototype.js, bash -n run-browser.sh и py_compile preview.py/collect.py/summary.py: exit0. git diff --check с core.whitespace=cr-at-eol/core.safecrlf=false PASS. Передача:161 local Markdown links без missing;23/23 manifest SHA match; executed final source11/11 match;192/192 preserved;145/145 unchanged. Финальное рабочее дерево70 tracked dirty +149 untracked файлов, включая входящие изменения; branch/HEAD неизменны. QA8795 closed проверен отдельным socket probe; user preview8796 HTTP200.

## Найденные проблемы и ограничения

Первый render-only проход был зелёным, но meaningful flows обнаружили преждевременное двойное подтверждение, stale public badge после opt-out и потерю событий согласия после отмены. Исправлены в prototype, не в application source. Public pending qualification leak воспроизведён независимо RED3/3 AZ/RU/EN, raw stage25-design-pending-red-20261003, затем устранён и проверен новым browser run. Один промежуточный harness имел2 language-navigation readiness failures; исправлено ожидание загрузки, assertions не ослаблялись. Предыдущие неуспешные результаты сохранены внеGit, не подменены итоговым PASS.

Оставшийся P3 copy caveat: RU gallery description.review содержит термин reviewer scope. Функциональные и локализационные проверки конкретных рабочих экранов пройдены; эта строка отмечена reviewer и оставлена в frozen review revision, не скрыта как якобы полная редакторская проверка. При следующей polish правке потребуется affected-screen проверка. Native file/date picker chrome локализует браузер/ОС, полный screen-reader audit не выполнялся.

**NOT_RUN в stage25 design-only:** Django/backend suite, migration/DB checks, реальный fixture transfer/reconciliation, nested IDs/person-vs-org server ACL, старые Specialist URL resolver tests, CAS/concurrency, реальная приватная загрузка/антивирус/credentialed integration. Backend единственный источник правил при будущей интеграции. Предыдущие stage24 PASS — исторические evidence, не новое выполнение25. Общий application suite остаётся **NOT_GREEN** по24.md; готовность сайта/production не заявляется.

Для просмотра пользователем root запустил отдельный owned Windows Python preview **127.0.0.1:8796**, hidden PID1560, ignored record scratch/task33-stage25/preview-process.json. [Открыть галерею](http://127.0.0.1:8796/docs/task33/design/specialist/index.html?lang=ru). GET index/logo200; .env/.git/config/media/traversal404. Это static design preview, не сервер приложения. QA executor очищает только собственные session/server8795; user preview8796 оставлен для решения пользователя.

## Остаток и передача

1. Принять или дать конкретные замечания к specialist-25-r1; запись решения в design/acceptance.md сейчас REVIEW_PENDING.
2. После принятия продолжить **тот же этап25**: конкретный implementation plan, application integration и meaningful isolated backend/browser/URL/fixture checks из prompt25. Не отмечать DONE по одним макетам.
3. Только после завершения25 отдельным поручением можно26. Production/commit/push/merge не авторизованы.

## Повторное поручение25 — сверка checkpoint 2026-10-03

Run `20261003-152709Z`, root в canonical frontend-reviewer scope. Прочитаны четыре входных документа, prompt25, dependency24 и relevant architecture/contracts/registry/role definitions. Actual checkout/branch/HEAD совпадают с указанными выше. Входной active_run NONE; stage24 DONE, Owner/admin-public ACCEPTED, Specialist NOT_ACCEPTED. Повторное поручение выполнить25 не содержит принятия specialist-25-r1; условие prompt25 «Реализацию Specialist экранов начинай после их принятия» сохраняется. Stage25 остаётся REVIEW_PENDING.

Перед изменениями отчёта/журнала сохранены все **219/219** dirty/untracked файлов, SHA256 и tracked binary patch в ignored `scratch/task33-stage25-resume-entry-20261003-152709Z`. Новый inventory: [25-resume-entry-manifest.json](25-resume-entry-manifest.json). Fresh match: **23/23** artifacts25 и **145/145** artifacts24; отсутствующих/изменённых относительно этих source manifests нет. SHA отчёта в entry inventory — только его предыдущая версия до этого запуска, не самохеширование финального отчёта. Application/design/QA source не менялись; changed scope этого запуска — данный отчёт, журнал и новый entry manifest. Новых исполнителей/review не назначали; historical independent execution остаётся атрибутированным предыдущему запуску.

Свежие команды этого запуска, каждая exit0:

```powershell
python scratch/task33-stage25-resume/verify.py
node --check docs/task33/design/specialist/prototype.js
python -c "import ast,pathlib; files=list(pathlib.Path('docs/task33/qa25').glob('*.py')); [ast.parse(p.read_text(encoding='utf-8')) for p in files]; print('Python AST PASS:',len(files))"
wsl -d Ubuntu-24.04 -u root --exec /bin/bash -n /mnt/c/kidsmap/docs/task33/qa25/run-browser.sh
python -c "import urllib.request; u='http://127.0.0.1:8796/docs/task33/design/specialist/index.html?lang=ru'; r=urllib.request.urlopen(u,timeout=5); print('Preview GET',r.status,'bytes',len(r.read()))"
wsl -d Ubuntu-24.04 -u root --exec python3 /mnt/c/kidsmap/docs/task33/qa25/summary.py /root/task33-evidence/stage25-design-final2-20261003/results.json
wsl -d Ubuntu-24.04 -u root --exec python3 /mnt/c/kidsmap/docs/task33/qa25/summary.py /root/task33-evidence/stage25-design-final-copy-20261003/results.json
```

JS/bash syntax PASS, Python AST **4/4**, gallery GET **200 / 628 bytes**. Повторное чтение raw historical browser results подтвердило **168/168 +586/586** и **78/78 +111/111**, failed rows/checks/events0. Это сверка сохранённых результатов при совпадающих source SHA, а не новый browser execution. Повторный browser/backend/DB/fixture transfer/server ACL/old URL execution **NOT_RUN**: checkpoint принятия ещё ожидается, source неизменен. Новых runtime failures не обнаруживали/не классифицировали; исторический application NOT_GREEN не переоценивали. Fresh `git -c core.whitespace=cr-at-eol -c core.safecrlf=false diff --check` exit0 PASS. Entry SHA recheck:217 файлов неизменны,2 изменены только по разрешённым report25/journal путям,deleted0; новый entry manifest отдельно. HEAD неизменен.

Галерея уже подготовлена и доступна пользователю: [specialist-25-r1](http://127.0.0.1:8796/docs/task33/design/specialist/index.html?lang=ru). Следующее действие — решение по этому конкретному набору; после принятия продолжить тот же25. Stage26+/production/commit/push/merge/deploy NOT_RUN. Own active_run освобождён при передаче.
