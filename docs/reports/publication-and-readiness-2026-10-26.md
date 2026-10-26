# Publication requests and saved-card readiness — 26 October 2026

**LOCAL PASS.** Пользователь разрешил реализацию прошлого плана и объединение подсчёта готовности. Выполнено /root последовательно, без делегирования. Scope: два связанных дефекта, без изменения публичного контракта, схемы или production.

HEAD `1b0acf8c6d03e71d8516cfb92c19018db1426ebf`, branch `codex/admin-draft-recovery-2026-10-26`. Результат находится в dirty WORKTREE. Ранее существовавшие и появившиеся параллельно чужие изменения сохранены; в частности прежние изменения draft recovery в `domain_admin/place.py` не заменены. Commit/push/deploy не выполнялись.

## Что исправлено

1. `publication.review` и `publication.publish` завершают соответствующую PENDING PUBLICATION заявку в одной транзакции с публикацией. Совпадают владелец/заявитель, ownership/source/candidate версии. Записываются модератор, время, комментарий и один audit решения. Вход через `moderate_place_request` перечитывает уже сохранённое решение и не дублирует audit. Заявки CLAIM, другой заявитель и stale версии не завершаются автоматически. Неподанный draft/rejected candidate нельзя одобрить через заявку, опубликовав вместо него прежние live данные.
2. Реальный admin POST перед публикацией сохраняет форму, меняя candidate version. Теперь сохраняется проверенный signed source/candidate контекст открытой формы. После успешной публикации он связывает решение с исходной проверенной заявкой, включая правки администратора в том же действии. Конфликт версии по-прежнему блокирует запись. Ранее устаревшая заявка не присоединяется к новому решению.
3. Новый адаптер `place_readiness.evaluate_saved_place_readiness` применяет существующие общие правила к сохранённой рабочей версии draft/pending/rejected. Его используют процент и popover в списке мест, список заявок и проверка действия публикации из списка. Revision/subcategory отношения подгружаются вместе с административным queryset; ModelForm для каждой строки не создаётся. Approved/declined revision не подменяет текущие данные. Private ServerDraft autosave не подменяет общую сохранённую версию.
4. Тарифы, вложенные группы, explicit empty/clear и сохранённое структурированное расписание учитываются в рабочей версии. Старое повреждённое расписание нормализуется тем же display parser, что в редакторе: строка списка не падает, часы остаются незаполненными. Ничего в БД этим чтением не исправляется.
5. Общая проекция формы сохраняет выбранный город вне Баку: пустой district select больше не отнимает балл у города, хранящегося в общей колонке. Legacy сохранённое значение `baku` также сохраняется при представлении. Volunteer editor использует ту же проекцию с сохранёнными днями расписания.

Знаменатель остаётся **10 обязательных требований**. Фото и координаты не добавлены к обязательным пунктам; готовность карты и рекомендации остаются отдельными сигналами. Публичные проверки продолжают применять тот же набор правил к одобренным данным, а не к черновику.

## Причины

- Публикация Place/revision не завершала соответствующую PlaceOwnershipRequest. Только одобрение через саму заявку сохраняло её решение.
- Форма показывала рабочую revision, список считал базовую Place. На воспроизведении форма имела 8/10 (80%), база и список — 2/10 (20%).
- В форме города вне Баку stored district разделялся на region + пустой district. Display snapshot терял выбранный город. Volunteer summary отдельно не читал сохранённые дни из form.initial.

## Проверки

**TDD RED:** наблюдались PENDING после прямого approve/publish; 80%/20%; реальный admin POST с изменением candidate version; город 70% вместо 80%; отказ row publish для готовой рабочей версии; volunteer hours 70% вместо 80%; одобрение неподанного draft; HTTP 500 списка при повреждённых legacy днях. Логи в `/tmp/kidsmap-readiness-20261026/evidence/` (`red.log`, `ingress-red.log`, `toggle-red.log`, `draft-red.log`, `volunteer-red.log`, `legacy-red.log`).

**Финальный Django/PostgreSQL запуск: 280 PASS, 79.246s, exit 0.** Более ранние 16/20/279 запуски не суммируются с ним.

```sh
.venv/bin/python /tmp/kidsmap-readiness-20261026/run.py final \
 catalog.testcases.test_publication_request_completion \
 catalog.testcases.test_admin_saved_readiness \
 catalog.testcases.test_task33_publication \
 catalog.testcases.test_task33_ownership \
 catalog.testcases.place_readiness \
 catalog.testcases.test_ownership_admin_preview \
 catalog.testcases.test_admin_place_moderation_fix \
 catalog.testcases.test_place_workflow_readiness \
 catalog.testcases.test_admin_saved_draft_preview \
 catalog.testcases.test_volunteer_admin \
 catalog.testcases.test_owner_readiness_projection \
 catalog.testcases.test_place_editor_preview \
 catalog.testcases.test_admin_revision_recovery
```

Runner очищает environment, устанавливает DJANGO_TESTING=1 и использует собственные PostgreSQL 17.10/test DB, Unix socket, LocMem cache/email, отдельные media/private storage и отключённые внешние интеграции. Task-owned container `kidsmap-readiness-20261026-pg` создан с `--network none`; чужие БД/контейнеры не использовались. Первоначальная подготовка socket в `/tmp` не была видна snap Docker; путь перенесён в собственный ignored `.tmp/readiness-20261026/socket`. Одна подготовка browser DB прервалась с DiskFull; повторная миграция завершилась успешно. Это ошибки подготовки стенда, а не product PASS/FAIL. Ожидаемые 403/422 в финальном логе относятся к отрицательным тестам.

**Rendered CUA browser:** 30 проверенных состояний editor/list: AZ/RU/EN × 390/768/1024/1280/1440. Реальный viewport подтверждён в DOM; переполнения документа нет; одинаковые 80% во всех четырёх индикаторах редактора и в строке списка. Popover: 8/10, недостают ровно age/price. Дополнительно: заполнение возраста + free → серверная проверка 100%; Enter на «Сохранить черновик» → редактор/list 100%; публикация через confirm modal → success modal → заявка APPROVED, pending 0 / approved 1. Для публикации вымышленная ready fixture была подготовлена как draft до действия; это не production изменение.

После последней нормализации legacy schedule сервер перезапущен с финальным кодом, повторно проверены сохранённые 100% и approved/pending 1/0. Console errors/warnings: 0. В логах собственных browser серверов HTTP 404/5xx: 0. Один captureScreenshot сразу после перехода не завершился по timeout; состояние перечитано, итоговый screenshot сохранён после загрузки.

Evidence: `browser-responsive.json`, `browser-save.json`, `browser-publication.json`, `browser-approved-final.txt`, `browser-console.json`, `screenshots/`, `final.log`, `source-manifest.json` под `/tmp/kidsmap-readiness-20261026/evidence/`.

После проверки scope hashes совпали с протестированными девятью файлами. Собственная браузерная вкладка и QA server закрыты, собственный PostgreSQL container остановлен; evidence и вымышленные fixtures сохранены. Чужие runtime не останавливались.

Дополнительно PASS: Django check; `makemigrations --check --dry-run` — No changes detected; Python AST parse девяти scope файлов; `git -c core.whitespace=cr-at-eol diff --check`. JS/CSS/templates не менялись этой правкой, Node suite не запускался. Общая app suite, physical devices/Safari и внешние email не проверялись.

## Файлы и границы

- Services: `publication.py`, `organization_ownership.py`, `place_readiness.py`, `permanent_place_rules.py`, `volunteer_editor.py`.
- Admin: `domain_admin/place.py`, `domain_admin/owner.py`.
- Новые regressions: `test_publication_request_completion.py`, `test_admin_saved_readiness.py`.
- План: `docs/plans/publication-and-readiness-2026-10-26.md`.

Production не подключался и не менялся. **Историческая заявка №351 этим локальным исправлением не закрыта.** После отдельного release её нужно сверить с историей принятой revision; одна публичность карточки не даёт основания одобрять stale/CLAIM заявку. Массовый cleanup и автоматическое переписывание прошлых решений не входят в scope.
