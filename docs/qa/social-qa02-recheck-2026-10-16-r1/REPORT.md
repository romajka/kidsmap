# SOCIAL-QA-02 — CONFIRMED OPEN / PLAN COMPLETE

2026-10-16, Asia/Baku. `/root`, kidsmap-orchestrator; django-reviewer/frontend-reviewer/security-reviewer/browser-qa выполнены последовательно одним исполнителем по canonical definitions. Независимая делегация не заявляется. **PLAN ONLY**, application changes этого scope0. [Точный план на три файла](IMPLEMENTATION_PLAN.md) ожидает нового scope approval.

## 1. Срез

`/home/ramin/kidsmap`, task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 +dirty WORKTREE, active_run NONE. SOCIAL01 уже [CLOSED LOCAL](../social-qa01-fix-2026-10-16-r1/REPORT.md). Его template/new regression входят в текущие968source hashes. Production, Git release cfef63e3 и модуль09 целиком не проверялись этим recheck.

[Entry](entry.json), [source/PID/MO](runtime-source.json), [readonly DB/isolation](readback.json), [verification](verification.json).

Повторно использован собственный profile этой же execution `social-qa01-fix-2026-10-16-r1` после проверки container owner label, current968source hashes, PID395141, own PostgreSQL17.10/DB/cache/media/private-media/email, DJANGO_TESTING1 и sole verified RU/AZ/EN locales до django.setup. HTTP127.0.0.1:33741, PGloopback44905, database/role social01_fix_r1. Текущие PO были собраны в собственный `.tmp/social-qa01-fix-2026-10-16-r1/locales` в этом же запуске; manifest повторно verified, неизменённые MO не пересобирались. Shared MO и .env не использовались/не перезаписывались. Inherited credentials очищены, socket guard разрешает только собственный PG; новые browser contexts блокируют внешний transport.

Native submit/approve/edit/reject с reason выполнены в том же свежем source snapshot в SOCIAL01 fix: [соответствующие accepted result files](../social-qa01-fix-2026-10-16-r1/verification.json). В этом recheck выполнены **новые login→GET→reload UI наблюдения и readonly DB readback**; повторного review POST/решения нет. Это reuse актуальных native transitions с attribution, не исторического Windows FAIL.

## 2. Что работает

Сохранённые причины и rejected revisions не потеряны:8readonly records по4типам×first/edit rejection подтверждают status=rejected, reason fixture match и SHA текста/причины. Candidate pointer очищен; approved current4/count1/average4 остаётся после отказа edit2. В форме сохранён rating из SOCIAL01: current4 либо first rejected3. Literal HTML/script не выполняется.

## 3. Свежая проблема

**SOCIAL-QA-02, P2 OPEN**, confidence HIGH, текущий LOCAL source. Автор открывает собственный отзыв после первого отказа либо отказа новой редакции и делает reload.

Ожидание: понятное решение об отказе, сохранённая причина и отклонённый текст доступны соответствующему автору. Факт: **причина отсутствует во всех16проверенных состояниях**. Для rejected edit также не показан отклонённый текст: редактор вернулся к прежнему live. Первый rejected текст остаётся в редакторе, но reason/status не объясняют отказ.

Native rendered evidence: все4типа RU390 для2rejection states; дополнительно Specialist AZ/EN390/1440. Всего **16states,64observations:40PASS/24FAIL одной группы причин,16PNG**. FAIL:16missing reason +8missing rejected-edit text. [Результат](reproduce.js.result.json), [PNG manifest](png-manifest.json). Counts — assertions, не24дефекта.

## 4. Причина и минимальная правка

`src/catalog/services/review_versions.py:moderate_candidate` намеренно очищает candidate_revision_id после решения. После отказа edit head сохраняет approved projection, а rejected reason/text лежат в history revision. `src/catalog/controllers/typed_reviews.py:87` выбирает own head, но не выбирает последнее релевантное rejected решение. `src/catalog/templates/catalog/typed_reviews.html` выводит только статус существующей candidate и текущую форму, без rejected feedback.

Сервис менять не требуется. План: controller читает последнюю revision **только собственного head**, если новой candidate нет и latest.status=rejected; template показывает private localized feedback с escaped reason/text/rating. Текущий редактор SOCIAL01 сохраняет candidate/current выбор. После correction/pending/approval старая reason скрывается. Private reports/replies в selector не участвуют.

Три будущих файла: controller, template и новый `src/catalog/testcases/test_social_qa02_rejection_feedback.py` (4methods). [Unapplied diff](proposed.diff), [test candidate](candidate/test_social_qa02_rejection_feedback.py), [source baseline](proposal-source-baseline.json). Existing assertions не менялись; новые tests **NOT RUN**. `git apply --check` exit0 доказывает применимость diff, не его работоспособность.

## 5. Security/risks

Причину/отклонённый текст показывать только соответствующему автору; опубликованный отзыв и публичный rating/count не переписывать. Head.rejection_reason недостаточен для rejected edit. Нельзя выбирать произвольную старую rejected revision после новой исправленной pending/approved. Literal reason/text должны остаться escaped. Automatic restore/editor replacement/button/JS/CSS/schema changes не входят в предложенный scope.

Current source failure подтверждён. Причина существовала на входе этого recheck; дата появления и regression относительно clean HEAD/production UNKNOWN. Постоянная потеря данных не установлена. Отдельный shared view-transition error из SOCIAL01 сохранён в его report; этот план его не исправляет.

## 6. Legacy и сохранность

Удаление/рефакторинг не предлагаются. SOCIAL01 candidate/current contract и tests сохраняются. [Preservation gate](verification.json) сравнивает34973entryfiles, исключая собственный ещё дописывавшийся SOCIAL01 evidence stream; guide — разрешённое обновление текущего статуса. Application/source968 не менялись. Entry76containers/2QAHTTP проверяются по identities/ports/state/PID/argv. Историческая continuity пяти исчезнувших HTTP до этого запуска остаётся NOT VERIFIED; foreign restarts0.

## 7. Команды и ограничения

[Ledger](commands.jsonl), [readonly readback command output](readback.txt), [browser result](reproduce.js.result.json). Основные команды:

```bash
python3 docs/qa/social-qa02-recheck-2026-10-16-r1/capture.py
.venv/bin/python docs/qa/social-qa02-recheck-2026-10-16-r1/readback.py
# exit0, READ ONLY, statement_timeout5s/lock_timeout2s,8records/source968MATCH
python3 docs/qa/social-qa02-recheck-2026-10-16-r1/drive.py reproduce.js
# CLIexit0; complete=true,40PASS/24sourceFAIL

git apply --check docs/qa/social-qa02-recheck-2026-10-16-r1/proposed.diff
# exit0, application patch unapplied
```

NOT RUN: application patch/GREEN; новые4regressions; полный RU/AZ/EN×6width feedback acceptance; native correction/resubmit после будущего feedback patch; полноценная privacy acceptance нового feedback, полный ACCEPT09/global corpus, production/commit/push/deploy, physical devices/screenreader/другие браузеры/реальные integrations. Blocked external fonts/transport — offline/SIMULATED, внешняя доставка не проверялась. Source/native checks не объявляются полным module PASS.

## 8. Следующий шаг

Новое одобрение [implementation plan](IMPLEMENTATION_PLAN.md) для **SOCIAL-QA-02 и трёх перечисленных application/test файлов**. После него весь scope выполняется без повторного запроса. SOCIAL03–09 не включены. Полный ACCEPT09 будет один раз после задач; module10 автоматически не начинается.

## 9. Приоритеты

Один подтверждённый P2 — SOCIAL02. SOCIAL01 CLOSED LOCAL, другие ID здесь не принимались. P0/P1 в этом узком recheck не установлены.

Artifact QA: первый final-gate exit1 из-за проверки ссылки на ещё не записанный verification.json. Self-link проверяется после записи; corrected final-gate exit0. Источник приложения и product assertions не менялись; этот incident не входит в product FAIL. Оба command outputs сохранены.
