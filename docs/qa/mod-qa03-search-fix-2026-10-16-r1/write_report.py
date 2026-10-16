import json
from pathlib import Path
h=Path(__file__).resolve().parent;r=h.parents[2];v=json.loads((h/'verification.json').read_text());p=v['preservation'];server=json.loads((h/'server-current.json').read_text())
text=f'''# MOD-QA-03 SEARCH — scoped LOCAL PASS; весь ID остаётся OPEN

2026-10-16. Основной исполнитель `/root`; применены канонические роли последовательно, независимые проверки другими агентами не заявляются. Основание: пользовательское «давльше» после конкретного [трёхфайлового SEARCH плана](../mod-qa03-sort-fix-2026-10-16-r1/SEARCH_FILTER_IMPLEMENTATION_PLAN.md); [APPROVAL](APPROVAL.md). Новое одобрение колонок ещё не получено.

## Snapshot и граница результата

Checkout `/home/ramin/kidsmap`, branch `{v['branch']}`, HEAD `{v['head']}`, dirty WORKTREE, `active_run: NONE`. [Entry](entry.json), [runtime source](runtime-source-final.json), [runtime info](runtime-info.json), [verification](verification.json).

Собственный текущий HTTP PID{server['pid']}, loopback49545; PostgreSQL loopback49821/database `mod03_search_fix_r1`; Python3.12.3/Django6.0.2,175 migrations. Фактические исходники работающего процесса и956 hashes совпадают с текущим WORKTREE. HEAD не включает незакоммиченные исправления. Production NOT RUN.

Поиск больше не теряет выбранные фильтры и сортировку. Search-причина принята LOCAL. Весь MOD-QA-03 остаётся OPEN из-за колонок Event/Specialist; MOD01/02 и предыдущие CSS/menu/SORT результаты сохранены, без повторного полного запуска. MOD04–08/full ACCEPT08 ещё не выполнялись.

## Причина и изменения

Jazzmin `admin_extra_filters` исключает параметры видимых list_filter. Независимая поисковая форма не содержит контролов соседней формы фильтров, поэтому после Enter терялся status и в опубликованных появлялась подходящая запись draft. Также single-value params теряли повторяющиеся значения.

Только одобренные3 файла:

- `src/catalog/templatetags/admin_dashboard_tags.py`: новый `km_search_hidden_params` возвращает все пары уже принятых `cl.filter_params`, кроме q/p/e.
- `src/catalog/templates/admin/catalog/includes/km_changelist_search_panel.html`: заменить один цикл hidden inputs. Штатное HTML escaping сохраняется.
- NEW `src/catalog/testcases/test_admin_queue_search_state.py`:6 regression methods через настоящую admin response, разбор hidden inputs и последующую отправку параметров формы.

[Exact own diff](implementation.patch). Queryset/permissions/models/JS/CSS/PO не менялись в этом scope; чужие изменения не присвоены.

## RED → GREEN

До patch:6 методов,19 assertion failures,0 errors; отдельный reset control проходит. Реальный браузер:3 sourceFAIL на Place/Event/Specialist — поиск draft106 после status=published теряет status и показывает ID110. [RED JSON](native-red.js.result.json), отдельные `screenshots/red-*.png` сохранены. После patch тот же trigger:3PASS, опубликованный фильтр сохранён, draft отсутствует. [Exact GREEN](native-exact-green.js.result.json).

Первый postpatch запуск имел3 ошибки ожидания порядка в новом тесте escaping: fixture не задавал sort, но ожидал ascending IDs. Исправлена только подготовка параметров: явно `sort=name_asc`; все assertions и expected IDs сохранены. [Описание](fixture-correction.md), [первый вывод](tests-green.txt). Итог: [14 методов PASS](tests-green-corrected.txt), exit0:6new +6existing SORT +2existing private-document ACL. Existing assertions не ослаблялись.

## Целевые проверки и evidence

[Команды, exits и durations](commands.jsonl), [воспроизводимый semantic gate](final_gate.py), [PNG manifest](png-manifest.json).

- Основной браузер: **{v['matrix_pass']} PASS**, RU/AZ/EN×360/390/768/1024/1280/1440×3очереди =54базовые ячейки;90доступных sidebar-состояний.18mobile expanded overlays явно блокируют фон; поиск проверен после штатного закрытия overlay. Нативная смена языка через меню, keyboard search→sort→pager→reload→empty→search→reset. Сверены реальные ID записей, каждый исходный фильтр и sort, сброс p, видимый keyboard focus.
- Edge: **{v['edge_pass']} PASS**, RU/AZ/EN×390/1440×3очереди: повторяющиеся status/name filters, escaping опасной строки без SVG/dialog, настоящий matching draft при явно включённом draft, recovery из e=1 после неверного lookup. Никаких подмен HTML/стилей/ответов.
- Всего принято **{v['native_accepted_total']} native PASS**, включая3exact-triggerGREEN. Локальных console/page/network/HTTP ошибок0. Внешние ресурсы, включая fonts, блокировались; соответствующие diagnostics сохранены как ожидаемое ограничение изоляции.
- **{v['png_count']} PNG** проверены по формату/размерам/SHA256: RED и GREEN раздельно; есть отдельные columns RED и interrupted attempts. Визуально просмотрены representative RU390 Place, AZ1440 Event edge и RU1024 Specialist columns. Не заявляется ручной просмотр всех PNG.
- До/после каждого полного batch и в финале совпал fingerprint всех полей/строк Place/Event/Specialist:110/110/110 собственных fictional records. [Начало](domain-before.json), [финал](domain-final.json). Это проверка указанных трёх моделей, не всех таблиц системы.

Точные target tests: `runtime.py test catalog.testcases.test_admin_queue_search_state catalog.testcases.test_mod_qa03_queue_sorting catalog.testcases.test_specialist_entry_admin.SpecialistEntryAdminTests.test_plain_editor_has_no_private_document_inline_or_count catalog.testcases.test_task33_specialist_security_review.IndependentSpecialistSecurityTests.test_ordinary_admin_cannot_observe_private_document_count`. Браузер: `drive_lang.py native-<lang>-<width>.js <lang>`; `drive_edge.py native-edge-<lang>.js`; отдельный `native-columns-recheck.js`. Все финальные commands exit0; semantic sourceFAIL колонок не скрыт за exit0.

## Прерывание и сохранённые попытки

Прерывание хода остановило собственные HTTP87944 и controller90775. Собственный PostgreSQL остался активен; source956 повторно сверен. Перезапущен только собственный HTTP, затем оставшиеся desktop batches. Шесть завершённых мобильных batches не повторялись. Частичный RU768 checkpoint/PNG и metadata сохранены в [interruption-01](interruption-01/), [описание](interruption.md). Старые PID не выдаются за работающие; непрерывность остановленного HTTP не заявляется. Первый browser-before-ready exit1 — harness failure, не sourceRED: [native attempts](native-attempts.md).

## Изоляция и сохранность

DJANGO_TESTING=1, own PostgreSQL/testDB/cache/media/private-media/file-email. Runtime очищает унаследованный env, не читает checkout.env, не использует production credentials; socket egress только в ownPG; браузер только ownloopback origin. Собственная verified копия pypdf, без сетевой установки. Secrets только в ignored scratch с ограниченными правами; в evidence нет production данных.

Текущие RU/AZ/EN PO собраны `scripts/build_isolated_locales.py` в собственный `.tmp/{h.name}/locales`; [manifest](locale-manifest.json), build/verify exit0. Manifest проверяется до django.setup, единственный LOCALE_PATHS, все3ownMO реально открыты. Общие checkout MO не менялись.

Entry {p['entry_files']} файлов: {p['unchanged_files']} без изменений, {len(p['changed_entry_files'])} допустимых изменённых existing paths,0missing; новый test и этот QA run добавлены. Изменённые paths перечислены в [preservation](preservation.json): только два одобренных app paths и status note guide (после его добавления). Все {p['entry_container_count']} чужих контейнеров сохранили ID/state/ports; добавлен свой. На входе0QA HTTP serve процессов; blanket continuity всех процессов машины не заявляется. HEAD/branch/active_run прежние. Чужих restart/reset/clean/stash операций нет.

## Оставшиеся колонки: подтверждение и следующий PLAN

[Свежий columns recheck](native-columns-recheck.js.result.json): Place1PASS, Event/Specialist2FAIL при native toggle «Обновлено / Создано», RU1024. Общий menu содержит Place-only targets; у Event/Specialist Jazzmin дополнительно не выдаёт `column-*` классы заголовков. Это отдельная причина; её sourceFAIL не включается в SearchGREEN.

[Конкретный план на четыре файла](COLUMNS_IMPLEMENTATION_PLAN.md): tags metadata из разрешённого cl.list_display, shared template loop/index/key, только JS toggler, новый regression module. Индекс берётся из фактического permission-filtered списка; сохраняется private-document ACL. Учитываются Place/trash и отдельные preferences. Код для этого плана ещё не изменён; требуется отдельное approval пользователя по его staged правилу.

## NOT RUN и решение

SEARCH: **scoped LOCAL PASS**. MOD-QA-03: **OPEN — columns**. MOD04–08/full08/all-modules acceptance, внешние интеграции, физические устройства/не-Chromium, production, commit/push/deploy NOT RUN. Смешанные старые переводы dashboard вне проверяемого поведения поиска; whole-UI localization PASS не заявляется. Module09 не начинался. Полный08 один раз после закрытия его задач.
'''
(h/'REPORT.md').write_text(text)
print('REPORT written from semantic verification')
