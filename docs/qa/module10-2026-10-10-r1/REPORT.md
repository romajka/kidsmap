# Модуль 10 — настройки, разделы и общие страницы

**FAIL. Аудит одного модуля завершён с явными NOT RUN.** 15 подтверждённых проблем: 1 P1, 12 P2, 2 P3. Application fixes не выполнялись исполнителем аудита.

Роль/execution identity: `/root`, canonical orchestrator, Django, frontend-admin/public, browser-qa и bounded security-reviewer выполнены последовательно одним исполнителем; независимые subagents не запускались. Definitions: [kidsmap-orchestrator](../../../.agents/agents/kidsmap-orchestrator/agent.md), [django-reviewer](../../../.agents/agents/django-reviewer/agent.md), [frontend-admin](../../../.agents/agents/frontend-admin/agent.md), [frontend-reviewer](../../../.agents/agents/frontend-reviewer/agent.md), [browser-qa](../../../.agents/agents/browser-qa/agent.md), [security-reviewer](../../../.agents/agents/security-reviewer/agent.md); authoritative registry `.agents/registry.json`. Дата 2026-10-10; финальная сборка 2026-10-10T16:46:50.104388+00:00 UTC. Исторические отчёты использованы только как checklist/helper code, все результаты/снимки QA10 получены заново.

## 1. Состояние области

Checkout `C:\kidsmap`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, branch `task33-progress`, active_run `NONE` unchanged. Entry WORKTREE — QA/docs dirty, app matched HEAD; entry manifest2784 files/digest `933b55c01caf9ab69bce9d81d23b69e87c262ffcf5d192917e8d9272b0f7ee83`. Во время аудита появились параллельные изменения:16 modified source +4 new test files, также foreign scripts/docs. Автор не установлен; собственные команды QA10 не меняли приложение/правила/assertions. Изменения сохранены. PRODUCTION UNKNOWN, не посещалась.

Прежние own8823 PID40936 и DEBUGFalse8824 PID17432 не считаются полным current runtime после drift: загруженный Python остаётся entry, disk templates/static могут обновляться. Новый own8825 PID40836 и DEBUGFalse8826 PID40732 запущены из current WORKTREE с guard всех **2788 files**, digest `e13c36f2af3aca03513ff860a1dee7c02a8cb2ab8214c89bcffd7dd5fe5914b1`, без autoreloader. [Entry](snapshot.json), [current](current-snapshot.json), [подробный drift](SOURCE-DRIFT.md), [module10 boundary hashes](module10-source-boundary.json), [финальное runtime/source подтверждение](runtime-final.json). qa/version — echo manifest, не независимая attestation; учитываются startup guards, listener/launcher PIDs и current source equality. Старый verification FAIL сохранён, source drift не скрыт.

После drift заново выполнены: native current settings save/reload47/47; filled public + admin matrix792; focus36; flags/event/temp/404/media/org boundary85; общие11 public pages/legacy business redirect1008; simulated network recovery2. Counts/PASS/FAIL точны в [current ledger](current-checks.json) и [raw results](counts.json). Подтверждённые дефекты сохранились. Current staff GET200 повторён; upload/delete без прав доказаны раньше, соответствующие handlers hashes unchanged, дополнительных security mutations не делали. Initial empty-default variants/полный language menu loop не повторялись на новом процессе: source boundary unchanged, ранние доказательства отдельно; это не полная приёмка каждого initial-state сценария на final snapshot.

Own isolated PostgreSQL17.11 container `kidsmap-module10-20261010-r1`, port55441, DBmodule10/testDBtest_module10,175 migrations. Container ID `97fac7184d2c877743ba93c42342be06a186ae4a4f110eaf84918e16ec75d463`; volume `09a95b93e1bef30fc385c0203f058ba2befadefe23261f72b5c24ffbc2512568`. Python3.12.15/Django6.0.2, TESTING1, fictional data only; отдельные LocMem process caches/mail, media/private-media/cookies, unit DB/media. Current processes используют ту же собственную QA10 DB/files, другие cache namespace/processes, новые browser contexts. Credentials scrubbed/no .env, external sockets/routes blocked. [Isolation](isolation.json), [current launcher](run-current.py), [current settings](qa_settings_current.py).

9736 entry foreign files,9 foreign HTTP,11 foreign containers и active_run сохранены; меняется только row10 журнала. Newly introduced source preserved by current manifest; чужие scripts/docs не трогали. Документы найдены ([inventory](documents.json)). Codebase Memory C-kidsmap `Transport closed`, freshness/coverage UNKNOWN; bounded source fallback, без reindex/export ([record](graph-summary.json)).

## 2. Сильные стороны

Native save→reload подтверждает брендинг/title/subtitle/search label/decor, 9 trimmed public texts и загруженные файлы. Brand logo/footer phone/email обновляются на публичных страницах. Неверные email/URL и threshold favorite count отклоняются сервером без ложного сохранения; исправление threshold даёт правильный публичный счётчик RU/AZ/EN. Пустой EN title остаётся пустым в DB, default display не записывается как сохранённый перевод.

OFF/ON трёх flags сохраняет данные и независимость остальных flags. Org/Spec lists+details скрываются404; Event list/detail410. Catalog/map permanent Place сохраняется, temporary Place скрывается в map/catalog. Lawful Spec2 owner OFF404/ON editable-page200 проверен. Event2 owner OFF404; ON опубликованный Event по действующему правилу redirects в dashboard с сообщением, HTTP200 не доказывает editable form (NOT RUN); Organization workspace остаётся доступным. Admin Organization2 при OFF действительно сохранён через UI как draft, после reload/ON candidate сохранён, live content_version1/названия прежние ([entry readback](organization-readback.json), [current readback](current-organization-readback.json)). Для Specialist/Event доказана доступность admin editor, полный hidden save cycle NOT RUN.

Общие страницы home/about/FAQ/contacts/privacy/terms/review-rules/listing-rules/add-place + empty catalog отрисованы RU/AZ/EN ×360/390/768/1024/1280/1440 до заполнения настроек. `for-business` — поддержанный legacy redirect к add-place; selected unchanged tests проверяют redirect. Filled public/settings matrix, языковой switch с сохранением catalog query/category, native mobile/desktop menu, footer/back-to-top/focus выполнены. FAQ Space/Enter после анимации 36/36 PASS. Contacts H1 computed solid contrast ≥3 во всех18 cells; это ограниченная выборка, не полный WCAG verdict.

## 3. Реальные проблемы

[Отдельные findings и 15 копируемых repair prompts](FINDINGS.md). Наиболее серьёзный SITE-QA-01: staff без model permissions читает медиахаб и загружает/удаляет глобальный публичный logo. Валидный CSRF проверен; без CSRF403. После фиксации evidence logo восстановлен через native admin UI. Production exploitation/integrations не проверялись.

Неприменённые публичные settings (AZ about/empty, contacts, CTA/placeholder, home hero PC/mobile), corrupt image acceptance, mobile form overflow, непоследовательный events OFF для legacy temporary URL, blank410, locale/admin modal states и input recovery описаны отдельно. Initial focus/Tab modal defect перепроверен после bringToFront/1250ms без screenshot до keyboard; Escape после анимации PASS. Неизвестная первопричина focus обозначена гипотезой. CSS zoom overflow не назначен app finding.

## 4. Tech debt

Обновлённые публичные шаблоны и старые SiteSettings controls расходятся; compiled locale artifacts не содержат часть уже существующих PO strings. Custom media endpoints обходят стандартный Django admin permission/validation lifecycle. Старые tests для legacy URLs/identity требуют отдельного contract review; assertions в аудите не менялись.

## 5. Risks

Все OPEN findings подтверждены только в LOCAL entry WORKTREE. Regression относительно исторического release не установлена. Во время аудита обнаружен чужой source drift; relevant module10 hashes unchanged и новая current native проверка подтверждает findings. Исторические результаты не считаются свежей базой. SITE-QA-07 — pre-existing locale/environment artifact failure; остальные native failures — pre-existing application/UX/security, SITE-QA-14 также явно SIMULATED transport.

LocMem singleton invalidation наблюдалась после native save→reload/public в основном процессе. Multiworker/Redis не проверялись. Network abort before server и upload delay/error — SIMULATED, реальный disconnect/HTTP500 retry NOT RUN. Uploaded malformed image вызвал настоящий сохранённый broken logo; этот сбой не симуляция ответа сервера.

## 6. Dead/legacy candidates

Home hero/image settings с отсутствующим публичным consumer — candidates для product/source reconciliation, не доказательство ненужной DB структуры. Legacy temporary Place и for-business route сохраняют реальные контракты. Никаких удалений, migrations или cleanup не выполнялось.

## 7. Tests gaps и результаты

Acceptance observations: **3611 PASS / 319 FAIL / 347 NOT RUN**, 4277 всего; counts не равны уникальным сценариям. [Полная scenario/role/language/width матрица](matrix.csv), [JSON](matrix.json), [сводка по ролям/языкам/ширинам](coverage-by-role-language-width.md), [raw/excluded counts](counts.json), [точные исключения](excluded-observations.json).

После source drift повторно выполненные неизменённые selected Django tests: 46 методов, **41 PASS / 4 FAIL / 1 ERROR**. Основная выборка34:29PASS/4FAIL/1ERROR, unittest6failure+2error subtests, exit1,31.357s test-body (112.77s total). 12 PageSmoke methods:12PASS exit0,3.412s test-body (60.42s total). [Summary](test-summary.json), [основной log](tests.log), [page log](pages-tests.log), [команды](tests-command.json), [page command](pages-tests-command.json).

Один failed method — реально не локализованные section labels (SITE-QA-07, EN/AZ subtests). Три other FAIL methods и один ERROR method — baseline fixture/contracts: Specialist default-enabled test использует legacy/unverified identity (302 вместо ожидаемого200); Place old-language slug tests получают canonical301 вместо200; review block lookup получает пустое redirect body и ValueError. Native lawful canonical path проверяется отдельно и не считается passed на основании этих failed tests. Первоначальный PageSmoke run12/10PASS/2FAIL (6 subtests) имел own PUBLIC_BASE_URL mismatch localhost vs testserver; own unit runner исправлен, приложение/assertions не менялись; [attempt log](pages-tests.attempt1.log) сохранён.

Raw harness ошибки не скрыты: trailing-space expectation (12), wrong business entitlement/button and legacy identity, FAQ animation timing, too-early Escape check исключены/перепроверены. Все script attempts сохранены. Final modal focus FAIL после достаточного ожидания остаётся. DEBUG=True default404 диагностический overflow/lang — environment, заменён DEBUG=False rendered proof. CSS zoom2 — SIMULATED, realChrome200%zoom NOT RUN.

Explicit NOT RUN: two-tab/stale/duplicate settings writes в остальных language/width combinations (RU1440 выполнен), полный UI unpublish/archive/delete lifecycle (начальные fixture states доказательством переходов не являются), полный hidden Spec/Event save, realChrome200%zoom, full pixel contrast/error403/500 matrix, shared cache/multiworker, external integrations/production, full suites/CI/other browsers. [Пределы](coverage-gaps.json). Все основные 18 cells выполнены только для перечисленных public pages/settings/flags, не для каждой возможной мутации/роли.

Свежих native PNG **1605**, включая PC/mobile/error/loading/modal/footer, [SHA/dimensions manifest](screenshots-manifest.json). Нет derived снимков. Full-page images с lazy/animation ниже viewport могут содержать неинициализированные блоки; отсутствие такого блока не назначено finding без native scroll/viewport проверки. Viewport examples: [mobile modal](screenshots/modal-final-viewport.png), [PC home](screenshots/home-viewport-en-1440.png), [mobile contacts](screenshots/contacts-viewport-ru-390.png), [corrupt logo](screenshots/invalid-file-public-mobile.png), [mobile overflow](screenshots/admin-sitebrandingsettings-ru-360.png).

Console/network: current common-page matrix наблюдает pageerror, console.error и local non-document HTTP≥400. Result rows показывают действительные counts; intentional errors и другие этапы отдельно. Это ограниченная инструментальная выборка; не полный console/security audit. Expected404/410/denials, intentional abort и malformed-image failures отдельно; external SDK/integrations blocked, успешными не считаются.

## 8. Recommendations

Оформить отдельный план прежде всего для permission bypass, затем сохранённых/публичных settings, visibility/media/layout/input-recovery; prompts самостоятельные. Никакие fixes автоматически не применены. Полный список own synthetic settings edits: [settings-changes](settings-changes.json), [final DB read-only snapshot](state-final.json). Section flags ON, favorites OFF, валидный logo и EN title восстановлены. Organization2 оставлен с native current draft `Uydurma QA10 admin: CURRENT OFF candidate` для review; live прежний.

Журнал изменяется только в row10. [Текст следующего чата](next-chat.txt) направляет на **11 SEO, языковые URL и redirects**, один новый модуль;13 после01–12. Own HTTP/PG/browser оставлены для review; это не свежее evidence для следующего модуля. Чужие стенды/файлы/active_run сохранены. No commit/push/deploy/production.

## 9. P0/P1/P2/P3

P0:0; P1:1 (SITE-QA-01); P2:12 (02–10,13–15); P3:2 (11–12). Все OPEN, remediation не запускалась. [Finding index](FINDINGS.md). [Exact/replay commands](COMMANDS.md), [final preservation/source/runtime verification](verification.json). PASS этого preservation check не меняет функциональный FAIL модуля.

Current console:180 raw FAIL rows — `net::ERR_FAILED` для намеренно blocked unpkg Leaflet/MarkerCluster CSS, без pageerror. Отдельная native диагностика3 языка ×390/1440 фиксирует host/path/requestfailed/console location ([current-console](current-console.result.txt)),6/6 attribution checks PASS. Они классифицированы ENVIRONMENT/SIMULATED и внешняя загрузка оставлена NOT RUN, app findings не добавлены. Local resources/basic HTTP/geometry/language checks текущих public pages PASS. Полная карта с внешними CSS/SDK не проверена.

Две реальные native вкладки current RU1440: A сохраняет телефон, B меняет только email и возвращает старый телефон, reload подтверждает silent lost update — [SITE-QA-15](findings/SITE-QA-15.md). Native dblclick final value PASS; контакты восстановлены through native UI. [Concurrency evidence](current-concurrency.result.txt). Другие language/width combinations отдельно NOT RUN.

Дополнительная source verification: [SOURCE-DRIFT](SOURCE-DRIFT.md). Совпадение current source/runtime подтверждено отдельно; первоначальная полная empty/default матрица не заявлена повторённой на final snapshot.
