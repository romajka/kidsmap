# Модуль03 — специалисты и приватные документы — FAIL

Роль: KidsMap orchestrator, последовательная Django/security/browser сверка. Дата2026-10-10 Asia/Baku; raw UTC timestamps относятся также к вечеру2026-10-09. Execution identity `/root`, единственный исполнитель; независимые subagents не запускались. Definition `.agents/agents/kidsmap-orchestrator/agent.md`, active registry; приложение не исправлялось. Scope: ровно модуль03 по `module-acceptance-prompts.md:112`, после DONE01/02;04 и остальные в этом запуске не выполнялись. Historical reports использовались как checklist, результаты ниже новые.

Три подтверждённых дефекта приложения: **2 P2 +1 P3**, отдельно Windows test ERROR и локальные assets/transport ограничения. Полного PASS всему модулю нет. [Findings/промпты](#3-реальные-проблемы), [матрица](matrix.csv), [JSON](matrix.json), [evidence summary](evidence-summary.json), [команды](commands.md), [455 screenshots с SHA256](screenshots-manifest.json), [визуальная сверка](visual-review.md), [финальная preservation проверка](verification.json), [следующий чат](next-chat.txt).

## 1. Состояние области

Фактический checkout `C:\kidsmap`; branch `task33-progress`; LOCAL HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`. До собственной QA-папки были modified `docs/qa/module-acceptance-prompts.md` и untracked отчёты `module01-2026-10-09-r1`, `module01-2026-10-09-r2`, `module02-2026-10-09-r1`. Snapshot сделан после создания собственного harness: он уже показывает собственную untracked папку. **App WORKTREE соответствует HEAD в проверенном source scope; итоговое состояние source подтверждается hash manifest, не предположением.** `active_run: NONE` из `docs/task33/implementation-status.md` сохранён. Production snapshot/проверка NOT RUN: production не подключался.

Свежий собственный стенд `http://localhost:8814`, PID43560, native Python3.12.15/Django6.0.2, без reloader. PostgreSQL17-alpine WSL Docker `kidsmap-module03-20261010-r1`, loopback55434→5432; container `0b8c82cd44aea8f70fbb4caaa504f28375ea2fb8f93b6b3de74099273ab88c8c`, DB/user module03;175 migrations. Separate testDB test_module03; separate LocMem cache/email, `.tmp/module03-20261010-r1/media` и `private-media`, own cookies/session. DJANGO_TESTING=1; .env не загружен, inherited integration env очищен, external keys blank, socket guard loopback, browser transport только ownlocalhost. Synthetic credentials не включены в repository evidence. [Isolation](isolation.json), [QA settings](qa_settings.py), [entry snapshot2776 source/assets hashes](snapshot.json), [runtime/PIDs](runtime-process.json). `/qa/version/` и final hashes доказывают тот же source digest, runserver импортирует текущий `C:/kidsmap/src`. Existing ignored `.mo` входит в WORKTREE snapshot as-is и не компилировался.

Чужие8811/PID6112,8812/40848,8813/40932, Docker ports55431/55432/55433 остались запущены. Их DB/cache/files/session/active_run не использовались и не менялись. Ownstand/42 drafts/3 profiles/7 docs сохранены для воспроизведения, не удалялись. Точный старый Docker shell invocation не captured: reproduction equivalent отделён в commands; PID/ports этого ПК установлены заново.

Прочитаны AGENTS.md, canonical README/registry/orchestrator definition, architecture/source-of-truth/current snapshot, audit/engineering/orchestration/testing contracts и historical content-entry checklist. Все явно запрошенные документы для этого модуля найдены; недостающих из обязательного списка нет. Использованы skills writing-plans, kidsmap-ui-design/frontend-design, Playwright, systematic-debugging, verification-before-completion. Graph-first codebase-memory C-kidsmap: architecture81520 nodes/170420 edges, узкие specialist/document searches, inbound trace download; dynamic route trace0 не означает отсутствие endpoint. Index generation обновлялся20:03:12→20:44:57UTC, часть critical Python имеет coverage_unavailable, owner template partial/metadata_changed. Relevant source просмотрен напрямую; raw graph cache не сохранён, граф не использован как proof удаления.

Исследованный контракт: proposal draft привязан к автору/UUID и version; author может предложить, но не получает личные rights. Verified person — отдельная identity после reviewed claim; место приёма отдельно от двустороннего сотрудничества. Profile update требует person и CAS updated_at. **Сохранение черновика/отправка изменений опубликованного Specialist снимает весь профиль с публикации**, что template явно предупреждает; Place candidate/live revision механизм здесь не применяется. Guest404 до следующего одобрения — ожидаемый контракт. Private docs не становятся общедоступными из-за claim/network owner; public certificate требует approved + person opt-in + опубликованный активный профиль. Identity always private, fresh reviewer permissions на каждом download.

Свежий UI путь: частичное proposal → сохранение/reload с каждого из5 этапов → новый login/resume → bio/education → error(-1)/исправление0 → send → moderation publication → person claim → reject с причиной → repeat claim → approve → person draft/edit → reject profile с причиной → correction/resubmit → publication → public card → ещё draft/conflict/photo replacement → final administrative publication. Initial rejected proposal correction именно автором до claim отдельно **NOT RUN**: не заменено ORM и не выдано за person workflow. Все проверяемые state transitions выполнялись UI; ORM разрешён только initial isolated fixtures и final read-only aggregate observation. [Последовательность команд](commands.md).

| Сценарий | Роль/язык/ширина фактического выполнения | Результат/доказательство |
|---|---|---|
| Partial draft, все5 этапов, reload, empty experience≠0 | author RU1440 | PASS: lifecycle12 + complete-proposal5 assertions; photo приватен доsend |
| Search/remove/no duplicates, возраст3–12, RU language, mixed format | author RU1440 | PASS: direction filters/toggle, saved two practices20/35AZN и разные телефоны |
| Description/education fallback | person RU1440; guest RU/AZ/EN final card | PASS: AZ/EN поля пусты послеreload, RU показывается как fallback; нет сохранённого «автоперевода» |
| Отрицательный/чрезмерный стаж, ошибка и ввод | author/person RU1440 | PASS: -1/999999 отклонены,0 сохраняется |
| Claim/reject/reason/repeat/approve, author≠person | person/moderator RU1440 | PASS; author edit/certificates404; final verified_person differs created_by |
| Rejected person profile/correction/send/publication/edit | person/moderator/admin RU1440 | PASS; public card/reload и finalphoto PASS; initial author rejected flow NOT RUN |
| Cooperation invite/reject/repeat/confirm/cancel/new role | network/person RU1440 | PASS10;employee private person/doc denied; collaboration не даёт biography rights |
| Identity/certificate consent/review/download/withdraw |7mandatory roles RU1440 | PASS ACL/headers/consent; malformed doc FAIL SPEC-QA-01 |
| Foreign draft/profile/document/file URL и revoke role | mandatoryroles + outsider RU1440 | PASS; actual foreign file blocked; same-session download200→403 после UI revoke |
| Two tabs/repeat send/dblclick/local text recovery | person/author RU1440 +18cell states | CAS/input/data PASS; conflict photo FAIL SPEC-QA-02; online proposal repeat sameprofile3 |
| Photo original/replacement/fileerror/reload/public | person/admin RU1440; guest RU/AZ/EN | PASS7 finalprobes; corrupt image backend400, savedoriginal intact; validreplacement rendered |
| Empty/filled/open/error/conflict geometry | RU/AZ/EN×all6widths | Main324 PASS (306screens +18 data checks); states108,18 loading timing screenshot NOT RUN |
| Actual visual/internal clipping/labels | RU/AZ/EN×all6widths | FAIL mobile author/person label/arrows18cells SPEC-QA-03; ENV-03 stalecatalogsAZ/EN |
| Chosen keyboard actions | author RU/AZ/EN×all6 | PASS90; visiblefocus screenshots; completeAT traversal NOT RUN |
| Loading message on native submit | author RU/AZ/EN×all6 | PASS18 passiveDOM observations; screenshot duringnavigation NOT RUN |
| Normal browser console/network | guest/person/author/admin ×18cells | Native72probes:53clean,19 expected-font-block probes;39 intentional external-font failures,0pageerror/0localHTTPerrors |

Точная row matrix authoritative; normalized assertion rows **PASS=711, FAIL=23, NOT RUN=50**. Counts включают повторные control probes и geometry, не являются числом независимых полных acceptance paths. FAIL rows приложения21 (два uploadprobes, один photo conflict,18mobileclip), environment2(AZ/EN catalogs); не23 отдельных defects. Raw FAIL/harness errors не удалены: incompleteerrorselector, loadingtiming и403/404 expectation объяснены в environment/summary. Ни один existing assertion не менялся.

Rendered browser: уже установленный Chromium headless shell1243 через own PlaywrightCLI sessionmodule03-r1; system Chrome policy disallowed DevTools. 455PNG/13contact sheets; все13 просмотрены визуально, отдельные source-backed defects перепроверены крупными кадрами/network. PC1440/mobile390 ошибки сохранены. Viewport950 высоты — не физическое устройство. Native popup pixels, fullpage every-scroll content и full focus-tree исчерпывающе не проверены.

Targeted Django:107 tests,106PASS/1ERROR, runner24.856s/nativeexit1, launcher57.812s. Single failing-test repeat1ERROR/nativeexit1/0.386s. Eight labels и exact native commands в [backend-result](backend-result.json), [лог](backend.txt), [повтор](backend-platform-recheck.json). NativeWinError32 — отдельно environment/test-lifecycle, browser send с сохранённым фото PASS. Full backend/JS suites NOT RUN. No assertion changes/fakegreen.

## 2. Сильные стороны

Сервер отделяет автора предложения от подтверждённого человека и от организации. Fresh direct download ACL проверен7 ролями, чужой реальныйdocument6 ещё8рольными probes; private file URL blocked дажеperson/admin. Identity private независимо от checkbox; approvedcertificate безconsent404, сconsent200, withdrawal снова404. Headers attachment/octetstream/private no-store/nosniff/CSPsandbox. Revoke reviewer черезUI влияет на старуюсессию:200→403;review404. Предыдущий404-only QA FAIL здесь не defect; свежий denial recheck подтверждает403.

Draft/reload, empty≠zero experience, per-practice price/phone, dual consent cooperation, conflict refusal и local text recovery фактически работают в проверенном scope. Repeatedsend двух вкладок вернул одинаковый profile3; dblclicksaved draft сохранился послеreload. Description fallback не записывает новые переводы. Админка даёт длинной форме секции/error summary, выбранные клавиатурные действия работают; desktop navigation отображается без clipping.

## 3. Реальные проблемы

| ID | Priority/type | Факт и самостоятельный промпт |
|---|---|---|
| [SPEC-QA-01](findings/SPEC-QA-01.md) | P2 application OPEN | Corrupt9-bytePNG принят/сохранён/download200; suffix-only validation |
| [SPEC-QA-02](findings/SPEC-QA-02.md) | P2 application OPEN | Photo preview409 использует unsaved basename/media404; serverfile/data retained |
| [SPEC-QA-03](findings/SPEC-QA-03.md) | P3 application OPEN | Mobileheader/nav8px clips20pxtext/32pxarrows;18applicablecells |

Каждый файл содержит роль/URL/шаги/expectation/fact/evidence/source-backed cause/priority rationale/repair scope/dependencies и копируемый промпт. Current baseline failures, reproduction fresh. Regression/pre-existing relative to differentcommit **не установлено**; historical report не подменяет сравнение. Production effect/security exploit/data loss не заявляются.

[Environment отдельно](environment.md): ENV-01 Windows unclosedstreamingresponse test ERROR; ENV-02 Chrome policy recovered with realheadless; ENV-03 stale existing compiled catalogs8/12 freshcomparisons; font abortsSIMULATEDtransport, typographyprovider NOT RUN. Environment repair/diagnostic prompts приложены, автоматических исправлений нет.

## 4. Tech debt

Photo preview зависит от mutated ModelForm instance на ошибочном пути; persisted/new upload semantics смешаны. CSS stepper содержит старые broadselectors рядом с новыми component rules; documentoverflowprobe не ловит внутренний clipping. Source/runtime catalog freshness требует отдельной сборочной проверки, а Windows streamingresponse lifecycle — portable тестовой дисциплины. Это bounded observations, не разрешение на общий refactor.

## 5. Risks

Corrupt evidence может доходить до модератора, но разрешённое скачивание защищено headers/ACL; execution/exfiltration не подтверждены. Conflictphoto выглядит как исчезновение фото, хотя savedfile существует. Мобильный stepper ухудшает навигацию; нижние actions продолжаютработать. Reviewrole fixture теперьvolunteer; его последующий403 ожидаем. AZ/EN service labels и externalfont fallback ограничивают локальную оценку финальной типографики. Real integrations/privacy of realidentity data не проверялись и не использовались.

## 6. Dead/legacy candidates

Ничего не объявлено dead и не удалено. Legacy Specialist.owner совместно с created_by/verifiedperson присутствует в модели/admin; deprecated смыслы различены, source/UI показывает owner не доказываетidentity. Его удаление/миграция не исследованы и не рекомендованы по graph. DynamicURL/ORM links с неполной coverage не трактуются как orphan.

## 7. Tests gaps

Явные NOT RUN в [matrix](matrix.csv): полный mutation lifecycle и ACL во всех18cells; initial author rejected-proposal correction; всеoptionaladminfields; последовательный online→both→offline persistedtoggle; max30practice rows/UI/removal/replacement permutations; photo deletion; fullbackend/JSsuite; physicalmobile/Safari/Firefox/systemChrome; screenreaders/fullTaborder/modalfocus; actualexternalfonts/email/identityprovider; offline selected-file restore; liveconcurrentdownload/delete иLinuxcontrol failingtest. Loading nativeDOMstate проверен, screenshot duringnavigation недоступен из-за QA timing/navigation; aftersaveframes не выдаются заloadingproof. Independentпроверки продолжены.

## 8. Recommendations

Согласовать отдельно небольшие repair scopes SPEC-QA-01 и02, затем03; готовыеprompts в findings. Stalecatalogbuild и Windowstestdiagnostic делать отдельнымenvironment scope. Повторить freshrendered adversepaths после разрешённых исправлений, не ослаблять privateACL/CAS/moderation. Текущийзапуск завершить audit artifacts; следующийчат — **04 «Мероприятия»**, module13 послеостальных. Собственныйстенд сохранён, следующий модуль обязан создать новый; чужие и этот не переиспользовать для freshproof.

## 9. P0/P1/P2/P3

P0/P1 не подтверждены. P2: SPEC-QA-01 malformeddoc, SPEC-QA-02 conflictphoto. P3: SPEC-QA-03 mobileprogress clipping при работающих нижнихдействиях. Environment не маскируется как appdefect. **AUDIT COMPLETE with FAIL/NOT RUN limits**, не «всё работает». No application/rules/migration/assertion changes, no commit/push/deploy/production. Final [verification](verification.json) — authoritative hashes/priorpreservation/journalrow03/runtime/credentialscan/links/diffcheck.
