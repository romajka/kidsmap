# Модуль08 — полный ACCEPT-08: LOCAL FAIL

2026-10-16. Полная приёмка выполнена один раз. **Исторические MOD-QA-01–08 закрыты локально в своих scope; весь модуль ещё не закрыт.** Подтверждены три новые причины: [MOD09 fuzzy-переводы](findings/MOD-QA-09.md), [MOD10 уведомления](findings/MOD-QA-10.md), [MOD11 причина решения](findings/MOD-QA-11.md). Новые application fixes не выполнялись. [Три конкретных плана](FINDINGS.md), candidate patches unapplied, требуют отдельного approval.

## 1. Состояние области

Root **/home/ramin/kidsmap**, HEAD **e4e05cc213b34e2d771ecb854901bfd016d1db51**, branch **task33-progress**, dirty WORKTREE, **active_run NONE**. [Entry snapshot](entry.json). Проверяется текущий dirty LOCAL source, не production. Один /root последовательно выполнял роли kidsmap-orchestrator/frontend-admin/Django/browser-qa/integration; независимое исполнение специалистов не заявляется. Канонические определения/knowledge/audit contract и scoped repair reports прочитаны; применены TDD/verification/KidsMap UI/accessibility/Playwright. Исторический module08-2026-10-10-r1 использован как checklist/основа QA scripts, не как runtime evidence.

Собственный новый профиль: **HTTP127.0.0.1:39213**, [PID/argv](server.json), **DBmodule08_full_r1/test_module08_full_r1** на подтверждённом ownPG **127.0.0.1:47955**, container ID **b4e125832fb38463089194b973c7bd25f61d3f4534d19bf6e079b6d1acb94766**. [Ownership](profile-reuse.json). Новые cache/media/private-media/file email/cookies, DJANGO_TESTING=1; чистое env до setup, checkout.env/production credentials не использовались. Egress Python только own PG, browser только own origin, внешние fonts/CDN намеренно blocked; ограничения не являются firewall всей машины. [Runtime](runtime-info.json), [launcher](runtime.py), [settings](settings.py).

RU/AZ/EN currentPO→новые own MO: build0/verify0, [manifest](locale-manifest.json), sole LOCALE_PATHS до django.setup. SharedMO не перезаписывались. [Current source](runtime-source-final.json):**961file**, startup/disk/baseline совпадают, actual module/template origins и opened ownMO. Graph-first moderation_hub._revision_row найден, точные relevant paths metadata_match/no_recorded_issue generation2026-10-16T08:49:00Z; граф не proof completeness и не копировался в Git.

Фикстуры:9fictional actors,7places/32organizations/34initial revisions/Event/Specialist/private fake document. Действия создают/меняют только эти own данные. [Fixture references](fixtures.json), [final read-only state](state-final.json). Для positive Event создана **новая** ownOrganization33/Event2 с правильным owner и full_clean; исходный Event1 с organizer.owner=NULL не исправлялся ORM и не выдавался за positive публикацию. [Initial-only addition](extra-fixtures.json). Состояния audited records менялись только проверяемыми native UI/HTTP действиями, не ORM подменой результата.

## 2. Сильные стороны / свежая проверка

| Сценарий | Результат / граница |
|---|---|
| Place/Organization/Event/Specialist queues, native search/empty/reset/reload | RU/AZ/EN×360/390/768/1024/1280/1440; фактический браузер |
| Sort, column toggle реальных cells, toolbar/filter controls | Все18cells для применимых Place/Event/Specialist; native disclosure закрывается Enter на summary |
| Hub first25→Next→остальные distinct→Previous | Все18cells, actual links/keyboard/query preservation |
| Current/candidate media, comparison/long text | Все18cells, actual decoded images/geometry/PNG |
| Sidebar/navigation, confirmation focus/trap/Escape/return | Все18cells; desktop/mobile применимые переходы |
| Specialist invalid Save, complete error/link/visible checkbox focus | **108PASS/18cells**, persisted state без изменений |
| Organization return→resubmit→approve→postpublication edit→final reject | Native reviewer/volunteer; candidate/live/причина в persisted state, terminal copy отдельный FAIL |
| Два модератора / stale409 / processed replay / CSRF / invalid reason | Настоящие серверные ответы, не SIMULATED |
| Volunteer native photo→draft→reload→две вкладки stale→submit→legacy approve→public reload | PASS, настоящий upload и данные/изображения после reload |
| Place partial mass publication ready+incomplete | PASS: только ready опубликован, неполный осталсяdraft |
| Event2 и Specialist1 reject custom reason→pending→published→reload | По4nativePASS; actual edit form и доступные bulk controls |
| Отзыв роли при старой открытой вкладке | Native staff-role UI, старый submit403/freshGET403, контент не изменён |
| Own volunteer draft delete Cancel/Accept/reload | PASS, soft delete только своей fictional fixture6 |
| Actual row unpublish/publish | RU390/1440, AZ390/1440, EN390/1440; status/is_active/row/readback. Один renderer incident отдельно ниже |
| Audit history / private documents | Actual admin history200/read-only; reviewer/staff403. **195ACL PASS** для9roles×3language URL routes/negative mutations и bounded state |

Свежие test commands: [20labels](test-labels.json), [полный log](full-backend.txt), [exact argv/exits/durations](commands.jsonl). **261/261PASS**,0failures/0errors/0skips,**183.790s test time**, process exit0. Полный backend corpus запускался **ровно один раз**. Сообщения об intentionally corrupt fake images/protected document404 — expected guards, не test failures. Это не global test suite.

## 3. Подтверждённые новые проблемы

| ID | P | Подтверждение / эффект | Конкретный scope |
|---|---|---|---|
| [MOD-QA-09](findings/MOD-QA-09.md) | P3 | 36drawer localeFAIL +2created-labelFAIL: current fuzzy PO исключает count/«создано» в AZ/EN | [3files](findings/MOD-QA-09-PLAN.md):2PO,2specific entries+newtest |
| [MOD-QA-10](findings/MOD-QA-10.md) | P3 | 12loading localeFAIL с SIMULATED transport и7actual success localeFAIL; операции проходят, JS literals русские | [6files](findings/MOD-QA-10-PLAN.md):JS,template,3PO,newtest |
| [MOD-QA-11](findings/MOD-QA-11.md) | P2 | 2nativeFAIL: saved final rejection reason не показан admin/reviewer на processed content detail | [2files](findings/MOD-QA-11-PLAN.md):template+newtest, row.revision уже загружен |

Это три причины, не59разных bugs. Поведение/rights/rendering ранее исправленных восьми ID не объявлено сломанным из-за новых причин. Candidate patches имеют SHA/unapplied manifests. Одобрение MOD08 на3files не распространяется на них.

## 4. Tech debt / QA corrections

[Полный журнал corrections](harness-corrections.md), [137excluded/replaced observations](excluded-observations.json). Начальные360queue результаты сохранены; ошибочные ожидания навигации/селекторов/viewport поправлены только в собственном QA, продолжение пропускало выполненные cells. Bulk reject Event/Specialist отсутствует в их custom bar по текущему дизайну: использована настоящая edit-form rejection. Event Save называется _continue; ожидание _save не выполняло POST. Первоначальная гипотеза custom confirmation не подтвердилась.

У исходного нового QA check был неверный falsy getAttribute(open).54проверки закрытия вынесены отдельно. Последовавшее ожидание Escape у native details тоже было ошибочным контрактом: [W3C APG Disclosure](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/) задаёт Enter/Space на control; Escape для этого раскрытия не реализован/не обещан, это не modal. Raw54observedFAIL сохранены и не выданы за defects; **54actual keyboard summary-close PASS** проверяют supported behavior. Existing permanent assertions не менялись. Исправления QA не превращают CLIexit0 в semanticPASS.

Шесть собственных provisional hub/media PNG с ошибочной меткой360 фактически имели1280 и были заменены правильными360; ранние pixels этих6attempts не сохранены отдельно. Raw rows/errors/commands сохранены. Диагностические1280frames остаются помечены по actual manifest dimensions; не считаются360evidence. Чужие артефакты не перезаписывались.

## 5. Risks / renderer incident

В первой actual AJAX серии один собственный AZ390 renderer после publish завис с95.5%CPU; JSON body/DOM перестали отвечать. Source stack получить не удалось; **причина UNKNOWN**, не приписана toast/i18n/sidebar без доказательств. Renderer135057 остановлен только после проверки ancestry до собственной sessionmodule08fulltransport; foreign processes не трогались. [Ownership/termination](own-renderer-interruption.json). Partial callback вернул12observations и Target crashed error; run целиком не PASS.

[Свежий AZ390repro](az-publication-repro.js.result.json):6PASS, unpublish/publish HTTP/JSON/DOM нормальны. [Только оставшиеся AZ1440/EN390/EN1440](native-publication-missing.js.result.json):15observations,9operationPASS/6localeFAIL, complete. Старые RU данные не повторялись. Это ограничивает диагноз первого зависания; incident не замаскирован под source fix, не объявлен production defect или общей continuityPASS.

Console/network собраны в raw native runs. Non-local fonts/CDN blocked; в transport ожидаемые local409/abortedrequests явно SIMULATED, server stale409 отдельно native. Произвольного «все network errors0» не заявляется. Из captured functional flows не установлена потеря чужих данных/ACL обход, но это bounded roles/endpoints/state, не универсальная security assurance.

## 6. Dead/legacy и смежный scope

Ничего не удалялось. Legacy volunteer review действующий superadmin путь, native photo approval проверен. [Смежные наблюдения](adjacent-observations.md): полная локализация Specialist editor относится к03, JS caption настройки рекомендаций главной — к10. Их copy не исправлялось и не выдавалось за принятый весь editor/settings scope; новые модули не запускались. Метаданные очередей «создано» входят в08 и явно добавлены в pending09plan.

## 7. Coverage / evidence / NOT RUN

[Authoritative matrix JSON](matrix.json), [CSV](matrix.csv), [verification](verification.json): **1272observations =1213PASS/59FAIL**, включая обоснованно retained partial observations. Это assertions/control observations, не1272независимых пользовательских путей.18core language/widthcells×4queues,18invalid Savecells,18transportcells; mutation-heavy flows представлены отдельными ролями/ширинами.90transport-supported observations явно SIMULATED; реальный доменный fingerprint дополнительно actual.

[304current native PNG](png-manifest.json), SHA256/dimensions; диагностические frames входят в count, не считаются дополнительными tests. Выборочно визуально просмотрены EN1440 real publication, RU390terminal reason, AZ360error summary и ранее scoped RU/EN/AZ drawers. Не заявляется ручной pixel-review всех304кадров. Debug/source/HTTP сами по себе не заменяли browser.

**NOT RUN:** global corpus/production/commit/push/deploy; физические устройства/другие browser engines/screen reader/OS native select popup pixels; полный mutation cross-product9roles×18cells; audit retention/исчерпывающий LogEntry history, concurrent batch stress; полный affiliation UI lifecycle (существующие backend guards исполнены); повторный полный owner/editor upload wizard (смежные02/03), полная локализация всех редакторов/настройки homepage recommendations. Новые09–11patches/postpatch regression не запускались без approval. Первое renderer зависание не имеет доказанного source diagnosis.

## 8. Сохранность / следующий шаг

[Final preservation](preservation.json):33813entryfiles; application changes в этом ACCEPT **0**, единственное разрешённое entry изменение — строка/примечание module08 guide; остальные entry files отсутствующими/изменёнными не стали. **2entryHTTP** argv/cwd и**74containers** ID/name/ports/state сохранены. HEAD/branch/active_runNONE/sharedMO неизменны. Базы прежних запусков не reseed/drop/migrate; новая DB/testDB собственные. Собственный renderer создан после entry и отдельно остановлен; это не blanket process continuity claim. Более ранние ограничения прошлых run не переписаны задним числом.

Приоритет: одобрить [MOD11 reason](findings/MOD-QA-11-PLAN.md), затем/совместно [MOD09 labels](findings/MOD-QA-09-PLAN.md) и [MOD10 toasts](findings/MOD-QA-10-PLAN.md). После approval выполнять только targeted regression/affected common scenarios и новый evidence supplement, сохраняя результаты этого единственного полного прогона. Не запускать весь261corpus снова без нового основания. [Handoff](next-prompt.txt).

## 9. Итог по приоритетам

P0/P1 подтверждённых0. **P2:1OPEN (MOD11), P3:2OPEN (MOD09/10)**. MOD01–08 scopedCLOSED LOCAL. Модуль08 **LOCAL FAIL**, требует трёх отдельных scope approvals. Production UNKNOWN, модуль09 не начат.
