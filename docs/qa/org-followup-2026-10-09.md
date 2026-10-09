# Оставшиеся замечания организаций: локальные исправления, 2026-10-09

Роль: kidsmap-orchestrator, одна execution identity; source/frontend/browser/integration проверки выполнены последовательно, независимые агенты не запускались. Definition: `.agents/agents/kidsmap-orchestrator/agent.md`. Scope согласован ответом пользователя «делаем»; [план](../superpowers/plans/2026-10-09-org-followup.md).

## 1. Состояние области и версия

LOCAL HEAD: `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5`, ветка `task33-progress`. Проверен dirty WORKTREE, приложение тестировалось с его изменениями, а не только HEAD. PRODUCTION: UNKNOWN / NOT RUN.

Стенд: http://localhost:8788/qa/, DJANGO_TESTING=1; PostgreSQL через Unix socket, контейнер без сети и опубликованных портов; isolated cache/email/media, внешние запросы браузера заблокированы. Использованы существующие вымышленные владельцы/сотрудник и организация67 с7 филиалами. Новые бизнес-объекты не создавались.

Финальный application manifest:2766 файлов, SHA256 `2103684f9e10e93c0fe4fed68c79ffd7215b15804124537abf3fdcc18f22e989`. Startup проверяет каждый файл, runtime endpoint совпал с manifest. [Snapshot](org-followup-2026-10-09/evidence/snapshot.json), [runtime](org-followup-2026-10-09/evidence/runtime-observed.json).

## 2. Что исправлено

| Задача | Причина | Минимальное изменение | Результат |
|---|---|---|---|
| ORG-PAGINATION-FOCUS-01, P2 | renderPage удалял активную кнопку вместе с DOM пагинации | semantic key кнопки, восстановление фокуса; если previous/next disabled — текущая страница; aria-current | Enter/Space, повтор, границы, Tab/Shift+Tab, поиск и reload проверены |
| OWNER-PLACES-OVERFLOW-01, P2 | flex-content после column breakpoint оставался шириной по содержимому | width:100% внутри существующего breakpoint860px | При768px scrollWidth815 →768; содержимое не обрезается |
| NAVIGATION-TRANSITION-01, P3 | rejected ready/finally создавал необработанный Promise; incoming opt-out кабинета прерывал нативный переход до доступного обработчика | cleanup для resolve/reject; ранняя регистрация в head; explicit skip исходящего перехода в account перед reveal | Публичная анимация сохранена; общий обработчик unhandledrejection не добавлялся |
| CATALOG-META-DRIFT-01, P2 | существующие verbose_name/plural четырех моделей отсутствовали в migration state |0141_catalog_admin_names: только4 AlterModelOptions | makemigrations --check теперь чистый; forward/reverse/forward без SQL и изменения схемы |

Затронуты четыре существующих application файла: base.html, account_profile.css, motion.js, organization_workspace.js; добавлена state-only миграция. Два новых JS regression scripts. Локальный diff считается от сохранённого WORKTREE до этого scope: [local.diff](org-followup-2026-10-09/evidence/local.diff). Обычный git diff включает чужую предыдущую работу.

## 3. Свежие проверки

| Проверка | PASS / FAIL / NOT RUN | Доказательство |
|---|---|---|
| Focus: owner+employee × RU/AZ/EN ×360/390/768/1440 |336 PASS /0 FAIL |focus-green.json |
| Owner places: два владельца ×3 языка ×4 ширины, навигация и кнопки |114 PASS /0 FAIL |places.json |
| Native transitions: RU/AZ/EN |10 PASS /0 FAIL,0 pageerror |motion.json |
| Финальная матрица native transitions | 37 PASS /0 FAIL,0 pageerror |motion-matrix.json |
| Reduced motion | 4 PASS /0 FAIL,0 pageerror |motion-reduced.json |
| Финальные viewport screenshots |3 PASS /0 FAIL |screens.json |
| JS regression suites |38 PASS /0 FAIL |js-final.log |
| Ownership/ACL/recovery/connections/concurrency:7 suites |149 PASS /0 FAIL /0 skipped,93.485s |server-tests.log |
| Admin labels + workspace после переноса script в head |14 PASS /0 FAIL,11.919s |server-template-final.log |
| check; makemigrations check/dry-run |PASS / exit0, No changes detected |check-final.log |
| Миграция в отдельной local QA DB: forward/reverse/forward |PASS,0 SQL operations, schema unchanged |migration-verify.log; migration-forward.sql; migration-reverse.sql |
| Domain fixture preservation |631 строки/17 моделей unchanged |domain-after.json |
| Полный suite / все сущности end-to-end / production |NOT RUN |Не подменяется результатами выбранных suites |

149 и14 — два отдельных запуска с пересекающимися tests; это не163 уникальных теста.

Команды (из корня репозитория; runners обнуляют окружение и проверяют isolation guard):

```bash
DJANGO_TESTING=1 NODE_PATH=.tmp/coordinate-location/dom/node_modules node --test \
 scripts/test_motion_transition_rejection.cjs scripts/test_organization_pagination_focus.cjs \
 scripts/test_organization_invitation_result.cjs scripts/test_organization_invitation_transport.cjs \
 scripts/test_organization_current_data.cjs scripts/test_organization_editor_errors.cjs \
 scripts/test_organization_autosave.cjs scripts/test_organization_creation_draft.cjs
.venv/bin/python .tmp/org-followup-20261009/run_unit.py \
 catalog.testcases.test_organization_join_recovery catalog.testcases.test_task33_ownership \
 catalog.testcases.test_task33_organization_workspace catalog.testcases.test_task33_permissions \
 catalog.testcases.test_organization_join_visibility catalog.testcases.test_organization_connections \
 catalog.testcases.test_organization_connections_concurrency
.venv/bin/python .tmp/org-followup-20261009/run_unit.py \
 catalog.testcases.test_organization_admin_labels catalog.testcases.test_task33_organization_workspace
.venv/bin/python .tmp/org-followup-20261009/run_unit.py --script checks.py
.venv/bin/python .tmp/org-followup-20261009/run.py --script migration_verify.py
.venv/bin/python .tmp/org-followup-20261009/run.py --script domain_snapshot.py
.venv/bin/python .tmp/org-followup-20261009/run_browser.py focus
.venv/bin/python .tmp/org-followup-20261009/run_browser.py places
.venv/bin/python .tmp/org-followup-20261009/run_browser.py motion-matrix
.venv/bin/python .tmp/org-followup-20261009/run_browser.py motion-reduced
.venv/bin/python .tmp/org-followup-20261009/run_browser.py screens
```

### RED и исправленные промежуточные попытки

Focus до изменения:192 PASS/144 FAIL; DOM regression1 PASS/2 FAIL. Геометрия768:815; проверка width гипотезы дала768. Migration check до изменения exit1,4 Meta operations. Motion unit до изменения:2 PASS/2 FAIL; отдельный account skip test также падает до исправления.

Первое исправление Promise и перенос в head отдельно не устранили нативный opt-out:9 PASS/1 FAIL,6 pageerrors. Результат не скрыт. Контрольная подмена none→auto в браузере дала0 ошибок; в приложение она не вошла. Изменение расположения CSS opt-in также не помогло и отменено. Финальное исправление пропускает account transition на исходящей странице и сохраняет существующий opt-out форм. Диагностика повторена в отдельном Chrome через Playwright, без CLI wrapper.

Ошибки harness: первоначально node не находил jsdom (исправлен NODE_PATH); один browser run начался раньше старта сервера (connection refused, повторён); у первой генерированной motion matrix была ошибка переменной key (исправлена, повторена). Это не PASS приложения и не дефекты приложения. У локального runner parse failure теперь exit1.

## 4. Технический долг

Не проведена общая приёмка всех форм/разделов после этих узких изменений. Migration0141 потребуется включить в будущий разрешённый release; production миграция здесь не запускалась.

## 5. Риски и границы

account_profile.css общий для кабинета: проверены места и организации; другие страницы кабинета не проходили полную визуальную матрицу. motion.js/base.html общие: проверены реальные переходы организация↔recovery и кабинет↔public place, а также unit fallback/abort/complete. Другие браузерные движки не проверены. Script в head небольшой, но production performance/slow-network метрики не измерены. Ранняя регистрация pagereveal соответствует [Chrome documentation](https://developer.chrome.com/docs/web-platform/view-transitions/cross-document).

## 6. Legacy / удаления

Ничего не удалено. canonical request_join/confirm_join/detach/cancel, ACL, organizer/venue/publication и модельные поля не менялись. Стили новой recovery UI сохранены. static/css/motion.css после экспериментальной диагностики восстановлен байт-в-байт к исходному WORKTREE.

## 7. NOT RUN

Полный suite; полная браузерная цепочка создания/модерации/публикации четырех сущностей; документы и uploads; все остальные account страницы; Firefox/WebKit; настоящий экранный диктор; production/email/maps/OAuth; production performance; commit/push/deploy. Подключение/отвязка/CAS проверены выбранными серверными suites, не заявлены как новый полный browser POST acceptance.

## 8. Рекомендации

Эти четыре замечания закрываются только по приведённым свежим локальным доказательствам. Следующая отдельная работа — общая приёмка существующих опубликованных изменений на изолированном стенде; release требует отдельного разрешения.

## 9. Приоритеты и сохранность

P0/P1 в этом scope не обнаружены. Три пользовательских/QA P2 и технический P3 рассмотрены выше.2761 существующий application файл и6 PO/MO остались неизменны; изменены только4 заявленных source файла, добавлена одна миграция. HEAD неизменен. Предыдущие изменения base.html/organization_workspace.js сохранены в scoped diff.631 прежняя domain строка не изменена; создавались лишь auth sessions/QA login state и запись обратимой migration state в изолированной базе.

Скриншоты (вымышленные данные): [пагинация PC](org-followup-2026-10-09/screenshots/pagination-1440.png), [пагинация mobile](org-followup-2026-10-09/screenshots/pagination-390.png), [кабинет PC](org-followup-2026-10-09/screenshots/places-viewport-1440.png), [mobile](org-followup-2026-10-09/screenshots/places-viewport-390.png), [768](org-followup-2026-10-09/screenshots/places-viewport-768.png), [до исправления768](org-followup-2026-10-09/screenshots/places-768-before.png). Полные длинные страницы сохранены рядом.
