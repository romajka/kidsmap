"""Own audit artifacts and ONLY journal row08. No application mutations."""
from pathlib import Path
import json,collections,datetime
P=Path(__file__).resolve().parent;R=P.parents[2]
def read(name):return json.loads((P/name).read_text(encoding='utf-8'))
def put(name,text):
 path=P/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text.strip()+'\n',encoding='utf-8')
S=read('results-summary.json');X=read('snapshot.json');I=read('isolation.json')
findings=[
 dict(id='MOD-QA-01',title='В центре модерации нет перехода к следующим страницам',role='admin / content reviewer',url='/ru/admin/volunteer/moderation/?status=pending',cells='RU/AZ/EN × 360/390/768/1024/1280/1440',steps='Открыть очередь с более чем 25 предложениями. Прокрутить таблицу и найти переход на страницу 2. Затем сравнить с реально отрисованной страницей ?page=2.',expected='Доступные с клавиатуры предыдущая/следующая страница, номер страницы и сохранение выбранных фильтров.',actual='На первой странице 25 строк, ссылок page=2 нет. Pending counter показывает 32. Страница 2 существует и содержит другие предложения, но попасть на неё из очереди нельзя.',cause='View передаёт Paginator(rows,25).get_page(...), а hub_index.html завершает таблицу без pagination controls. Подтверждено source и 18 rendered cells.',source='src/catalog/domain_admin/volunteer.py:282–296; src/catalog/templates/admin/volunteer/hub_index.html:19–23',evidence=['matrix.result.txt','supplement.result.txt','screenshots/hub-ru-1440.png','screenshots/hub-page2-ru-1440.png'],impact='Часть очереди недоступна через штатную навигацию; обход требует ручного изменения URL.',scope='hub_index.html / moderation_hub_index; сохранить ACL, counts, GET-фильтры и порядок.',dependencies='Django moderation hub; общая доступная навигация страниц.',accept='Создать 26+ вымышленных предложений; пройти UI page1→page2→page1 клавиатурой, с entity/status/date filters. Проверить RU/AZ/EN и шесть ширин; empty и out-of-range page.'),
 dict(id='MOD-QA-02',title='Фото и галерея в централизованной модерации отображаются путями',role='admin / content reviewer',url='/ru/admin/volunteer/moderation/content/39/',cells='Свежий валидный candidate: RU 1440/390; общая таблица comparison — 18 cells',steps='В кабинете владельца выбрать главное фото и два фото галереи, дождаться ready, сохранить черновик, reload и отправить. Открыть реальную pending-заявку в moderation hub.',expected='Просмотр текущего и предложенного главного фото и галереи с порядком, пригодный для визуального решения.',actual='В .km-volunteer нет ни одного img. Главное фото — places/gallery.webp, галерея — строковое представление массива словарей. При этом native approve применяет фотографии; публичная карточка после reload реально загружает все три фото.',cause='hub_detail.html выводит before/after как обычные строки. Native valid payload и публичный readback подтверждают, что дело не в повреждённой фикстуре. Отдельная legacy review имеет preview, но она superadmin-only; штатный content reviewer получает там 403.',source='src/catalog/templates/admin/volunteer/hub_detail.html:9–11; src/catalog/services/moderation_hub.py:reviewer_scopes / changes',evidence=['gallery-finish.result.txt','flows2.result.txt','acl.result.txt','screenshots/gallery-valid-pending-hub-pc.png','screenshots/gallery-valid-pending-hub-mobile.png','screenshots/gallery-approved-public-en-390.png'],impact='Проверяющий может принять фотографии, которых не видит в доступной ему поверхности.',scope='Typed presentation of media changes in moderation hub; безопасная выдача preview по существующим правам.',dependencies='publication payload/gallery order; privacy/storage; модуль01. Не расширять права на приватные документы.',accept='Native owner/volunteer photo+gallery draft→reload→submit→review; видимые current/candidate previews и порядок, corrupt/missing media state. Approve/reject не меняют прежний контракт live; reviewer без прав private docs не получает их.'),
 dict(id='MOD-QA-03',title='Панель очередей выходит за экран при ширине 1024',role='admin',url='/ru/admin/catalog/place/; /ru/admin/catalog/event/; /ru/admin/catalog/specialist/',cells='RU/AZ/EN × 1024; повторная проверка всех трёх очередей',steps='Открыть очередь на 1024px с обычным sidebar. Дождаться settled layout. Сравнить viewport и правый край toolbar, раскрыть сортировку/колонки. Посмотреть строки мест.',expected='Панель поиска/сортировки/колонок помещается в доступную ширину; таблица прокручивается в своём контейнере и остаётся читаемой.',actual='Root scrollWidth=1162 в RU/AZ и 1099 в EN при viewport=1024. .km-toolbar-right выходит до x=1162.31/1099.09. Кнопки справа обрезаны; у мест первые строки достигают 548px, колонка обновления сжимается до почти нулевой ширины.',cause='Подтверждён источник общего overflow: nowrap в search form, min-width:280px у поиска и toolbar-right при sidebar; wrapping breakpoint только max-width:900. Причина сжатия отдельных table columns/548px row требует дополнительного CSS разбора — гипотеза, не доказанная общая первопричина.',source='static/admin/css/pages/kidsmap_changelist.css:445–491,731,989–998,2862; src/catalog/templates/admin/catalog/includes/km_changelist_search_panel.html:95',evidence=['final-proof.result.txt','supplement.result.txt','screenshots/queue-place-settled-ru-1024.png','screenshots/queue-event-settled-en-1024.png','screenshots/queue-specialist-settled-az-1024.png'],impact='На планшетной ширине часть управляющих элементов недоступна без горизонтального перемещения, строки мест плохо читаются.',scope='Shared changelist toolbar responsive layout и scoped table column rules. Не менять данные/фильтрацию.',dependencies='sidebar available content width; Place/Event/Specialist shared template; модули01/03/04.',accept='RU/AZ/EN × 360/390/768/1024/1280/1440, sidebar open/closed, dropdowns open. Root overflow ≤1px, все управляющие элементы доступны; таблица имеет локальный scroll, строки обновления не превращаются в вертикальный текст.'),
 dict(id='MOD-QA-04',title='Escape не закрывает мобильную административную навигацию',role='admin',url='/ru/admin/; /ru/admin/catalog/place/',cells='RU/AZ/EN × 360/390/768',steps='Фокусировать кнопку навигации, открыть Enter, нажать Escape. Проверить видимость sidebar и body.sidebar-open. Затем активировать оставшуюся сфокусированной кнопку Enter.',expected='Escape закрывает открытое перекрывающее меню и сохраняет понятный видимый фокус.',actual='После Escape sidebar остаётся видимым и sidebar-open сохраняется во всех 9 cells. Enter на прежней кнопке закрывает его. При pointer попытке нажать эту кнопку открытый sidebar/logo перекрывает её.',cause='Обёртка использует data-widget=pushmenu; локальный kidsmap_admin_sidebar.js обрабатывает клавиши accordion-пунктов, но не обеспечивает Escape для внешнего sidebar. Runtime подтверждает отсутствие closure. Точная ответственность vendor pushmenu/местного adapter требует решения при исправлении.',source='static/admin/js/kidsmap_admin_sidebar.js:1–82; административный header data-widget=pushmenu / Jazzmin PushMenu',evidence=['matrix.result.txt','final-proof.result.txt','screenshots/sidebar-Escape-proof-ru-390.png','screenshots/sidebar-Escape-proof-en-768.png'],impact='Пользователь клавиатуры остаётся с перекрытым содержимым и фокусом на закрытом меню элементе.',scope='Интеграция header/sidebar PushMenu: Escape, видимый close/toggle и возврат фокуса.',dependencies='Vendor Jazzmin/AdminLTE; accordion semantics не ломать; не приписывать sidebar role=dialog без решения по контракту.',accept='Native Tab/Shift+Tab/Enter/Space/Escape на 360/390/768 во всех языках. Видимый opener/close, меню закрывается Escape и overlay, после закрытия виден правильный фокус.'),
 dict(id='MOD-QA-05',title='В подтверждении снятия с публикации фокус остаётся на BODY',role='admin',url='/ru/admin/catalog/place/ → row menu → toggle-publication confirmation',cells='Все 18 language/width cells; cause повторён в RU/AZ/EN × 390/1440',steps='Фокусировать row more-actions, Enter, выбрать снятие с публикации. Нажимать Tab и Shift+Tab, затем Escape.',expected='Начальный фокус внутри alertdialog, кнопки доступны Tab/Shift+Tab, после Escape фокус возвращается на видимый row opener.',actual='Начальный фокус BODY, последовательные Tab остаются BODY. Escape закрывает modal, но фокус не возвращается opener. В списке focusables первый элемент — SVG use href=#kmi-warning с tabIndex=-1 и aria-hidden=true.',cause='getFocusableElements включает любой [href], в том числе SVG use. Warning confirm не соответствует primary/danger selector, поэтому autofocus и trapping используют нефокусируемый use. lastFocusedElement записывается после закрытия row menu, без явного видимого opener; native readback возвращает BODY.',source='static/admin/js/kidsmap_notifications.js:64–75,90–138,157–177,319–327; static/admin/js/kidsmap_place_changelist.js:row action handler',evidence=['supplement.result.txt','final-proof.result.txt','screenshots/modal-focus-cause-ru-1440.png','screenshots/modal-focus-cause-en-390.png','screenshots/modal-focus-restored-en-390.png'],impact='Подтверждение публикационного действия практически недоступно через прямой Tab-путь; потеря фокуса после закрытия.',scope='Общий kmModal focus engine + передача/восстановление row trigger. Только реально focusable HTML controls; warning tone учитывать.',dependencies='Общий компонент влияет на confirmations в других модулях; отдельно MOD-QA-06 i18n.',accept='Реальный browser, sprite и fallback icons, primary/danger/warning, первый/последний Tab/Shift+Tab, Enter/Space/Escape, close/cancel, видимый focus return. Все 18 cells; не ограничиваться jsdom.'),
 dict(id='MOD-QA-06',title='AZ/EN подтверждение снятия с публикации написано по-русски',role='admin',url='/admin/catalog/place/ и /en/admin/catalog/place/ → row unpublish',cells='AZ/EN × все 6 ширин; RU контроль',steps='Перейти в AZ или EN очередь и открыть подтверждение снятия опубликованного места.',expected='Заголовок, объяснение и кнопки на выбранном языке; пользовательское название места может сохранять свой язык.',actual='«Снять с публикации?», русское объяснение, «Да, снять», «Отмена» в AZ и EN. На EN окружающая основная административная UI переведена. Подтверждено 12 captured texts и 4 повторных browser cells.',cause='Строки захардкожены в kidsmap_place_changelist.js:647–654 и не получают i18n/data labels. Source не зависит от версии .mo. Собственный первоначальный matcher содержал mojibake; статус исправлен по сохранённому rendered text и независимо повторён final-proof.',source='static/admin/js/kidsmap_place_changelist.js:647–654,575–579; shared notifications defaults',evidence=['supplement.result.txt','final-proof.result.txt','matrix.json','screenshots/unpublish-modal-en-390.png','screenshots/unpublish-modal-az-1440.png'],impact='Критичное объяснение снятия карточки непонятно пользователю выбранного языка.',scope='Локализованные labels для row unpublish confirmation; связанные hardcoded success text проверить отдельно, они пока source-only.',dependencies='Django gettext/data attributes; MOD-QA-05 для общей modal проверки; не переводить пользовательские сохранённые названия.',accept='AZ/RU/EN: native modal title/body/cancel/confirm и фактически выполненные уведомления, все 6 ширин. Проверить source↔compiled catalogs; отдельно указать fallback, не записывать перевод в модель.'),
 dict(id='MOD-QA-07',title='Сводка ошибки специалиста разбивает HTML на отдельные символы',role='admin; передать владельцу модуля03',url='/ru/admin/catalog/specialist/1/change/',cells='RU/AZ/EN × 390/1440',steps='В admin снять все специализации, выбрать rejected, указать причину, нажать Save и принять нативное подтверждение. Сервер отклоняет форму. Посмотреть верхнюю error summary.',expected='Одна понятная ошибка «Обязательное поле» с переходом к специализациям, честное состояние несохранённого ввода.',actual='Одна .errorlist превращается в 84 error-summary links: «Специализации: <», затем «u», «l», символы class/errorlist markup и далее. Красный блок занимает большую часть экрана. Allowlisted persisted state остаётся прежним, что является правильной валидацией.',cause='В specialist/change_form.html цикл for error in field.errors перебирает AdminField.errors() как HTML string; нужен список ошибок underlying bound field. Подтверждены rendered links и source; это ошибка отображения, а не отсутствие required validation.',source='src/catalog/templates/admin/catalog/specialist/change_form.html:12–14; Django admin.helpers.AdminField.errors',evidence=['specialist-finish.result.txt','specialist-save-proof.result.txt','screenshots/specialist-error-banner-ru-1440.png','screenshots/specialist-error-banner-en-390.png'],impact='Сводка не сообщает пригодное для исправления сообщение и создаёт десятки лишних keyboard targets.',scope='Specialist server error summary и переход к underlying field/checkbox group; application validation не ослаблять.',dependencies='Модуль03; Django AdminField vs BoundField; inline error summaries проверить на тот же тип.',accept='Одна и несколько серверных ошибок, inline errors, длинные тексты и native Save confirmation; понятные сообщения без HTML chars, правильные focus targets, сохранность ввода. RU/AZ/EN × 390/1440 минимум; existing assertions не менять ради зелёного.'),
 dict(id='MOD-QA-08',title='Панели фильтров мероприятий и специалистов открываются пустыми',role='admin',url='/ru/admin/catalog/event/; /ru/admin/catalog/specialist/',cells='RU/AZ/EN × все 6 ширин, 36 открытых panels',steps='Открыть очередь, кнопкой Filter/Enter раскрыть панель. Попытаться выбрать статус, дату события или формат консультации. Сравнить с конфигурацией admin и настоящими filter_specs.',expected='Поля применимых фильтров, определённых для данной сущности; выбор и применение меняют GET и список.',actual='Панель содержит пустую область, заголовок качества данных, Reset/Apply и счётчик, но не содержит native select. Для специалиста доступны в server filter_specs status/is_active/consultation_format/specializations; для события status/start_datetime/owner, но UI их не выводит.',cause='Общий search_panel фильтрует spec.field_path по фиксированному whitelist мест created_by/created_date/category/district/is_verified и place quality fields. km_primary_filters Event и Specialist не используется в этом rendering. В фикстуре Event единственная категория поэтому Django законно не выводит category; остальные доступные specs также проигнорированы.',source='src/catalog/templates/admin/catalog/includes/km_changelist_search_panel.html:280–315; src/catalog/domain_admin/place.py:938,1549; src/catalog/domain_admin/specialist.py:451–455',evidence=['drawers.result.txt','filter-contract.json','screenshots/filters-open-event-ru-390.png','screenshots/filters-open-specialist-en-1440.png','contacts/filters-en.png'],impact='Обещанные дополнительные фильтры отсутствуют; часть отбора приходится делать вручную. Status tabs остаются отдельным работающим способом.',scope='Shared filter renderer по entity-specific config/filter_specs; preserve query, chips, counts и reset/apply behavior.',dependencies='SimpleListFilter и стандартные FieldListFilter; связанные очереди других сущностей; не менять бизнес-фильтрацию и права.',accept='Вымышленные Event с разными датами/категориями/status и Specialist с разными format/status/directions. Реальный UI selection→Apply→reload→reset; правильные counts/chips, пустой результат; RU/AZ/EN × все 6 ширин.')
]
for f in findings:
 ev=', '.join(f'[{Path(e).name}]({"../"+e})' for e in f['evidence'])
 put('findings/'+f['id']+'.md',f'''# {f['id']} — {f['title']}

OPEN · P2 · 2026-10-10 · LOCAL WORKTREE/HEAD {X['head']} · run module08-2026-10-10-r1. Browser evidence produced by /root; no independent specialist execution. Confidence HIGH для факта. Production UNKNOWN. Класс: существующий baseline текущего локального source, не regression от этого аудита.

Роль: {f['role']}. URL/endpoint: `{f['url']}`. Проверенные cells: {f['cells']}.

Шаги: {f['steps']}

Ожидание: {f['expected']}

Факт: {f['actual']}

Причина / границы гипотезы: {f['cause']}

Source: {f['source']}. Доказательства: {ev}. Полная [матрица](../matrix.json), [snapshot](../snapshot.json).

Приоритет P2: {f['impact']} Критическая потеря данных/компрометация этим evidence не установлена.

Область: {f['scope']} Зависимости / ownership: frontend-admin + Django владелец указанной поверхности; {f['dependencies']}

Приложение не исправлено. Следующий шаг: согласованный отдельный repair scope, [копируемый промпт](../repair-prompts/{f['id']}.txt).
''')
 put('repair-prompts/'+f['id']+'.txt',f'''KidsMap: исправь только {f['id']} — {f['title']}.

Сначала определи фактический checkout, HEAD/branch/dirty WORKTREE и active_run. Прочитай AGENTS.md, канонические .agents и актуальное описание дефекта docs/qa/module08-2026-10-10-r1/findings/{f['id']}.md с указанными fresh evidence. Сверь текущий source: исходный snapshot 8d188b316f800fbedf0b1e376905dfd4924cb1b6; не предполагай, что он не изменился. Сохрани чужие изменения, active_run и стенды. Представь конкретный план и работай только в согласованном scope; уже согласованную область не переспрашивай, расширение согласуй отдельно.

Роль/trigger: {f['role']}; {f['url']}. {f['steps']}
Факт: {f['actual']}
Source: {f['source']}. Причина: {f['cause']}

Разрешённая область исправления: {f['scope']}
Зависимости: {f['dependencies']}
Целевое поведение: {f['expected']}
Приёмка: {f['accept']}

Создай новый собственный локальный стенд DJANGO_TESTING=1 с отдельными DB/cache/media/private-media/email и вымышленными данными. Проверяемые переходы выполняй через реальный UI; source inspection/jsdom/HTTP200 не заменяют rendered browser, сохранение/reload. Применяй существующие skills и meaningful targeted tests, не ослабляй assertions или авторизацию. Без production credentials/интеграций, commit/push/deploy. Сохрани новый report/evidence/screenshots, exact commands/counts/exit codes, candidate/live readback и NOT RUN ограничения. Обнови статус дефекта только по свежим доказательствам; остальные findings не исправляй автоматически.
''')
table='\n'.join(f"| [{f['id']}](findings/{f['id']}.md) | P2 | {f['title']} | [Промпт](repair-prompts/{f['id']}.txt) |" for f in findings)
put('FINDINGS.md','# Подтверждённые дефекты модуля08\n\n8 OPEN P2. Все подтверждены свежим browser/source evidence. Исправлений приложения нет.\n\n| ID | Приоритет | Факт | Самостоятельный repair prompt |\n|---|---|---|---|\n'+table)
ledger=[json.loads(s) for s in (P/'command-ledger.jsonl').read_text(encoding='utf-8').splitlines()]
totals=collections.Counter(l['result'] for l in ledger);seen=collections.Counter();command_rows=[]
for n,l in enumerate(ledger):
 seen[l['result']]+=1
 original=Path(l['result']);result=original.name if seen[l['result']]==totals[l['result']] else original.stem+f'.attempt{seen[l["result"]]}.txt'
 assert (P/result).exists()
 command_rows.append(f"| {n+1} | `{l['command']}` | {l['cli_exit_code']} | {l['duration_seconds']} | [{result}]({result}) |")
commands='\n'.join(command_rows)
tests=read('tests-command.json');test_cmd=' '.join(tests['command'])
put('commands.md',f'''# Команды и фактические результаты

Working directory C:\\kidsmap, PowerShell, login:false. Browser driver запускает установленный Node/Playwright CLI с session module08-r1; effective JS с placeholders сохранён рядом. Пароль читается только из ignored scratch; executed code с секретом не сохраняется. CLI exit0 означает выполнение скрипта, а не PASS всех observations.

## Targeted existing Django tests

```text
{test_cmd}
```

215/215 PASS, failures0/errors0/skipped0,147.499s, native exit0. [Точный argv и exit](tests-command.json), [stdout/stderr](tests.log). Изолирован test_module08, unit-media/unit-private-media/LocMem email. CSRF cookie в unit process csrftoken под существующие тесты; browser stand использует собственный cookie. Assertions приложения не менялись.

## Реальный Chromium

| № | Exact driver command | CLI exit | Seconds | Raw result |
|---|---|---|---|---|
{commands}

В журнале {len(ledger)} native browser executions; exits {dict(collections.Counter(l['cli_exit_code'] for l in ledger))}. Counts authoritative: [results-summary](results-summary.json), [matrix.json](matrix.json), [{S['excluded_rows']} исключённых/заменённых observations](excluded-observations.json). Не-JSON uncaught harness failures не получают выдуманного количества assertion rows. Все попытки сохранены; latest результаты выбирает [aggregate.py](aggregate.py).

## Подготовка и финальная проверка

```powershell
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/prepare.py
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/run.py snapshot
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/run.py migrate
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/seed.py
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/bootstrap-retry.py
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/run.py serve
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/seed-extra.py
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/seed-taxonomy.py
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/filter-contract.py
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/aggregate.py
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/contacts.py
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/drawer-contacts.py
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/write-report.py
.venv/Scripts/python.exe docs/qa/module08-2026-10-10-r1/verify.py
git diff --check
wsl.exe -- docker inspect kidsmap-module08-20261010-r1 --format '{{{{.Id}}}} {{{{.Config.Image}}}} {{{{json .Mounts}}}}'
wsl.exe -- docker exec kidsmap-module08-20261010-r1 postgres --version
```

Setup: первый migrate exit1 (PG ещё не готов), первый seed exit1 (неполная обязательная category), следующий seed exit1 (гонка с завершением migrations/UndefinedColumn). Собственная незавершённая QA DB переинициализирована до browser transitions; guarded bootstrap-retry exit0 после175 migrations. Итоговый migrate exit0 [migrations.log](migrations.log); serve остаётся running PID42060, это не завершившаяся команда с exit0. prepare/snapshot/extra fixtures/taxonomy/filter-contract/aggregate/contacts exits0. Итог verify/git diff --check подтверждается [verification.json](verification.json), а не ожиданием скрипта.

Docker stand: новый postgres:17-alpine, actual PostgreSQL17.11, localhost55439, unique container/volume в [runtime-final](runtime-final.json). Полный первоначальный shell argv docker creation отдельно не записан; current image/mount/ID проверены read-only inspect. Команды выше не являются сценарием для повторного запуска поверх завершённого stand: bootstrap содержит guards и fixtures не идемпотентны.

Exploratory source reads с неверным путём и собственные PowerShell quoting/cp1251 ошибки не являются failures приложения. Финальные Python AST/JS syntax проверки включены в verify. Production/foreign stand commands не выполнялись.
''')
put('next-chat.txt','''Продолжаем KidsMap в C:\\kidsmap. Прочитай AGENTS.md, канонические .agents и docs/qa/module-acceptance-prompts.md целиком. Определи свежие checkout/HEAD/branch/dirty WORKTREE/active_run и фактическую версию стенда; сохрани чужие изменения и стенды.

Модуль08 завершён DONE — FAIL, отчёт docs/qa/module08-2026-10-10-r1/REPORT.md: 8 OPEN P2 MOD-QA, исправлений приложения нет. Его исторические PASS используй только как checklist. Следующий первый незавершённый — 09 «Отзывы, избранное и уведомления». Выполни ТОЛЬКО его полный канонический промпт до отчёта, в AUDIT ONLY. Модуль13 после остальных.

Создай новый собственный изолированный стенд DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email и вымышленные данные. Не используй чужие credentials/volumes/сессии и не предполагай доступность адресов с другого ПК. Текущий stand08: localhost8821/PID42060/PG55439, container kidsmap-module08-20261010-r1; прежние стенды сохранены — не останавливай и не перезаписывай их.

Без app/rules/migrations/assertion fixes, production, commit/push/deploy. Проверь функционал и визуал в настоящем браузере RU/AZ/EN×360/390/768/1024/1280/1440. Сохрани свежие evidence/screenshots, exact commands/counts/exit codes и PASS/FAIL/NOT RUN; отдели baseline/environment/SIMULATED. Каждый подтверждённый defect — отдельно с готовым repair prompt. Обнови только row09 журнала, дай handoff10. Если текущий журнал изменился, выбери первый незавершённый среди01–12 по нему.
''')
counts=' / '.join(f'{k}={v}' for k,v in S['observations'].items())
by_run='\n'.join('| '+name+' | '+str(c.get('PASS',0))+' | '+str(c.get('FAIL',0))+' | '+str(c.get('NOT RUN',0))+' |' for name,c in S['by_run'].items())
put('REPORT.md',f'''# Модуль08 — админка, модерация и волонтёрский кабинет

**DONE — FAIL**, fresh run module08-2026-10-10-r1,2026-10-10,Asia/Baku. Восемь OPEN P2; application fixes/commit/push/deploy/production отсутствуют. Execution identity: один /root, роли orchestrator/frontend-admin/Django-security/browser-qa последовательно; независимые specialists не запускались. Definitions: .agents/agents/kidsmap-orchestrator/agent.md, frontend-admin и browser-qa; scope строго один модуль08. Исторический content-entry audit использован как checklist.

## 1. Состояние области

Checkout **C:\\kidsmap**, branch **{X['branch']}**, HEAD **{X['head']}**, active_run **NONE**. Entry dirty — QA/docs предыдущих модулей/repair plans плюс уже созданная own run08 папка, см. [snapshot](snapshot.json). Tracked приложение не изменено. Runtime — текущий WORKTREE и существующие compiled .mo, не production и не стенд исходного Linux ПК. Source manifest: **2784 файла**, SHA256 **{X['source_digest']}**. Startup guard run.py сверил source перед запуском, autoreloader выключен; финальная manifest/HEAD/PID проверка в [verification](verification.json). /qa/version только возвращает manifest, сам по себе не является независимой аттестацией. [Runtime identity](runtime-final.json), [isolation](isolation.json).

Stand новый: HTTP localhost8821, PID42060, PG localhost55439/module08/test_module08, новый контейнер kidsmap-module08-20261010-r1, unique volume. Python {I['python']}, Django {I['django']}, PostgreSQL17.11, Chromium153.0.8010.12/headless shell1243, own browser sessionmodule08-r1. Отдельные LocMem cache/email, media/private-media, session/CSRF cookies. DJANGO_TESTING=1, inherited credentials очищены, checkout .env не загружается в testing, server external sockets и browser non-local transport блокированы. Google/maps/OAuth/IndexNow/GA отключены. [Own QA launcher](run.py), [QA settings](qa_settings.py), [allowlisted read-only state endpoint](qa_urls.py).

Исходные фикстуры:9 actors/7places/32orgs/34revisions/event/specialist/private fake document; [fixtures](fixtures.json). Дополнительные NEW initial-only valid Event2+Org36 и synthetic specialization1 отдельно: [extra fixtures](extra-fixtures.json), [taxonomy](extra-taxonomy.json). Не исправляли существующие проверяемые переходы ORM: они выполнялись native UI/HTTP. Final read-only fictional state: [state-final](state-final.json). Setup races/неполные initial fixtures и собственные selector/async/confirm ошибки описаны в [commands](commands.md), не выданы за defects.

Нужные документы доступны, missing=[] в [documents](documents.json); прочитаны также canonical knowledge/rules/role definitions и применимые skills. Codebase Memory C-kidsmap использован первым для architecture/coverage: root совпадает, index ready; initial125509nodes/227637edges,74 partial parses/60 unindexed dirs, timestamp/generation свежести UNKNOWN. Во время QA architecture index вырос до135543nodes/237881edges. Граф — исследовательские hints; Django permissions, URL registration и critical source edges проверены текстом/файлами. Caches графа не сохранялись.

Фактические поверхности: Django Place/Organization/Event/Specialist changelists; /admin/volunteer/ и edit/proposal; moderation hub и content detail; superadmin legacy review; moderation SLA; staffaccessuser role UI. Hub объединяет Place/Organization/Program/Activity/OfferingGroup/affiliation, Event/Specialist идут через отдельные admin surfaces. [Source mapping](SOURCE-MAP.md).

| Роль initial fixture | Фактический доступ в RU/AZ/EN |
|---|---|
| anonymous, owner, outsider | admin302; direct protected mutations/state без разрешения не проходят |
| volunteer / volunteer_b | собственные authored owner=NULL объекты; чужой ID404, moderation403 |
| moderator preset | hub200 для affiliation scope, content detail404; legacy review403 |
| reviewer / reviewer_b: explicit change_place permission | content hub/detail200, legacy review403; private document404 |
| staff без business permissions | защищённые surfaces403 |
| admin superuser | нужные очереди/review200, fake private document200 |

Это scope/perms конкретных fictional actors, не универсальный вывод по названию роли. [195 ACL checks](acl.result.txt) включают negative GET/POST и сравнение allowlisted place/org/revision/photo/event/spec состояния и двух counts; они не проверяют абсолютно все DB таблицы/логи/session writes.

## 2. Сильные стороны

| Сценарий | Роль / язык / ширина | Свежий результат |
|---|---|---|
| Pending org→return reason→draft correction/reload→resubmit→approve→postpublished candidate→final reject | volunteer/reviewer RU390/1440 | PASS; live не заменяется draft/pending/rejected candidate |
| Два reviewers с одной version, один решает, другой stale | reviewer/reviewer_b RU1440 | PASS;409, allowlisted state без изменений |
| Две вкладки volunteer editor | volunteer RU390 | PASS; stale draft не перезаписывает первый, ввод остаётся |
| Native volunteer main photo upload/draft/reload/submit/legacy approval/public reload | volunteer/admin/anonymous RU390/1440 | PASS; настоящие normalized media и live readback |
| Owner main+gallery ready→draft→reload→pending→native hub approve→public reload | owner/admin RU1440; anonymous RU/AZ/EN390 | PASS data pipeline; review preview FAIL MOD-QA-02 |
| Processed action / invalid action / missing reason / stale / CSRF | selected roles RU/AZ/EN | PASS denied/no allowed side effects; actual409/403 |
| Частичная массовая публикация Place | admin RU1440 | PASS: ровно1 published,1 quality skipped; неполная карточка остаётся draft |
| Event2 rejected с собственной причиной→pending→published | admin RU1440 | PASS native UI; валидный organizer, photo; Event1 fixture invalid excluded |
| Specialist required error→выбор synthetic direction→rejected reason→pending→published→reload | admin RU1440 | PASS native Save confirmation и state; error summary FAIL MOD-QA-07 |
| Role revoke в staffaccessuser UI и старая вкладка | former volunteer_b RU390 | PASS native403; fresh GET403; содержание не изменилось |
| Native own draft delete cancel/accept/reload | volunteer RU390 | PASS; отмена не меняет state, подтверждение soft-deletes только own fixture6 |
| Place/Organization/Event/Specialist native search/empty result | admin RU/AZ/EN × all6 widths | По точным rows searches.result; никаких ORM substitutions |
| Filled/empty/error/conflict/long comparison/SLA и keyboard filter focus | admin/volunteer RU/AZ/EN × all6 widths | Rendered evidence; missing pagination/overflow/sidebar — отдельные FAIL |
| Native open/close filter panels | admin RU/AZ/EN × all6 widths | Place controls/focus PASS; Event/Specialist empty panels FAIL MOD-QA-08 |
| Loading/repeat guard/conflict/error/retry | admin RU/AZ/EN × all6 widths | PASS handler checks, **SIMULATED** delayed409/aborted AJAX; не реальная внешняя интеграция |

Основные [flows](flows.result.txt), [flows2](flows2.result.txt), [role/delete readback](flows3-resume.result.txt), [valid gallery](gallery-finish.result.txt), [Event](editor-finish.result.txt), [Specialist](specialist-valid-finish.result.txt). Новые org33–35 созданные UI в RU/AZ/EN390 завершены declined/draft: fresh final readback PASS3, original flows3 потерял observation array после screenshot timeout; поэтому полный массив промежуточных PAS не восстановлен догадками. PNG сохранены.

215/215 unchanged targeted Django tests PASS,0failures/0errors/0skips,147.499s, native exit0. [Exact argv](tests-command.json), [log](tests.log). Test suites: publication/admin_editors/volunteer_hub/completion_moderation/volunteer_admin/volunteer_dashboard/moderation_sla/place_readiness/admin_candidate_cover/specialist_privacy. Full suite NOT RUN.

## 3. Реальные проблемы

Каждый defect отдельно с role, endpoint, repro, expectation/fact, cause/hypothesis, source, evidence, impact и repair scope. [Finding index](FINDINGS.md).

| ID | Приоритет | Факт | Repair prompt |
|---|---|---|---|
{table}

Классификация: все8 — baseline текущего неизменённого локального source; доказанного regression от этого QA нет. Production applicability UNKNOWN. External font blocks/setup/harness failures — environment/QA, не новые application findings. 2px volunteer edit overflow RU/AZ360 сохранён как manual_review/NOT RUN по видимому ущербу, отдельный defect не назначен. Source-only hardcoded toasts и specialist bulk readiness bypass требуют отдельного product/contract решения, не объявлены подтверждённой потерей данных.

## 4. Tech debt

Shared changelist renderer содержит place-specific whitelist и CSS среди surfaces других моделей. Media comparison строковый вместо typed rendering. Focus selector допускает SVG href. Specialist template смешивает AdminField и underlying BoundField error semantics. Content revisions используют version/content_version/dependencies, Event/Specialist другие admin contracts; нельзя применять один optimistic-lock pipeline по названию «модерация». Legacy review всё ещё wired и полезен для superadmin photo preview; compatibility не является разрешением удалить его.

## 5. Risks

В пределах выполненных native negative tests не подтверждены чужое сохранение/обход роли/private-doc leakage. Это ограниченная выборка endpoints и allowlisted state, не доказательство безопасности всех APIs. Отсутствующий preview повышает риск принять неподходящие фото; missing pagination скрывает часть backlog. Keyboard/navigation issues затрудняют административную работу. UI .mo/fallback environment может влиять на тексты; MOD-QA-06 отдельно подтверждён hardcoded source.

Фонты fonts.googleapis.com намеренно blocked. В main matrix diagnostics666 net::ERR_FAILED от fonts и18 ожидаемых400 invalid-filter console messages; local requestfailed0, других captured JS exceptions там нет. [Диагностика](matrix.result.txt), [SIMULATED failures](supplement.result.txt). Для дополнительных flows нет исчерпывающего единого network HAR; точные captured responses указаны в raw rows. Event flatpickr CDN также blocked; корректные сохранённые даты valid Event2 проверены родной form, внешний SDK не выдаётся за PASS.

## 6. Dead/legacy candidates

Удаление не предлагалось/не выполнялось. Legacy volunteer review действующий, его ACL отличается от hub; удаление без migration/role workflow review недопустимо. Недоступный object assignment API не объявлен dead code: workspace реально опирается на created_by/owner=NULL, роль можно отозвать. Graph orphan/dead analysis не использован для удаления.

## 7. Tests gaps

Authoritative [matrix CSV](matrix.csv)/[JSON](matrix.json), [summary](results-summary.json), [scope gaps](coverage-gaps.json), [excluded attempts](excluded-observations.json). Observations: **{counts}**, всего **{S['observation_count']}**; дополнительно **11 scope NOT RUN**, то есть NOT RUN aggregate включая scope={S['observations'].get('NOT RUN',0)+11}. Это assertion/control observations с повторами, не число независимых полноценных пользовательских путей и не число defects.

| Run | PASS | FAIL | NOT RUN |
|---|---|---|---|
{by_run}

Browser: все18 RU/AZ/EN×360/390/768/1024/1280/1440; headless Chromium, viewport height950. Native PNG **{S['native_png']}**, SHA/dimensions в [manifest](screenshots-manifest.json); включая прозрачно сохранённые harness diagnostic screenshots.21 DERIVED contact sheets [manifest](contacts-manifest.json),18 исходных обзоров399 top viewport crops и3 filter обзора54 frames визуально просмотрены; критические PC/mobile defects дополнительно открыты крупными native кадрами. Contact sheets не заменяют исходные PNG и не доказывают пиксели всех scroll positions. System select popup pixels/screens reader/real touch device NOT RUN.

Loading/error quick actions задерживались/abortились route interception; native server stale409 отдельно проверен. No actual maps/OAuth/SMTP/integrations. Полный cross-product mutations×9roles×18cells NOT RUN; основные complex flows RU390/1440, публичные photos RU/AZ/EN390. Нет parallel batch stress, полного audit event retention/LogEntry UI history, real assignment feature и >page-size pagination данных Event/Specialist. Program/activity/group полный editor lifecycle — scope05, здесь только queues/hub/targeted tests. Event/Specialist VolunteerPlaceRevision candidate/live pipeline неприменим к фактически иной реализации; не помечен PASS по аналогии.

Own failures: malformed initial gallery/string вместо dictionary (правильный server отказ), wrong legacy role403, strict duplicate search/login selector, async photo processing/redirect ожидание старой кнопки, Save confirm auto-dismiss, no initial specialization lookup, hidden mobile nav вместо section-jump, fullpage screenshot timeout, search debounce/Enter retry. Исправлялись только QA scripts/NEW fictional fixtures.{S['excluded_rows']} observation rows исключены/заменены; raw attempts/CLI exit1 сохранены. Неполные первичные Event fixtures не замаскированы под regression. [Commands и exits](commands.md).

## 8. Recommendations

Сначала отдельный согласованный scope MOD-QA-05/01/02, затем responsive/filter rendering MOD-QA-03/08 и sidebar/i18n MOD-QA-04/06. MOD-QA-07 передать владельцу модуля03 с этим fresh evidence. Не менять assertions/права/publication rules ради зелёного; каждому исправлению нужен собственный rendered regression и native save/reload.

В глобальный MASTER_AUDIT выводы этого модуля передать при module13; чужой MASTER сейчас не перезаписывался. Строка08 журнала обновлена, следующий module09. [Готовый текст следующему чату](next-chat.txt), [канонические13 prompts](../module-acceptance-prompts.md).

Сохранность: проверены2784 source files,7161 foreign files вне журнала, active_run,7 foreign HTTP listeners и9 foreign Docker containers; exact final hashes/drift/PIDs/IDs и только row08 diff в [verification](verification.json). Собственный stand08 оставлен для локальной повторной проверки. Production не подключался; foreign stand/data/credentials не использовались.

## 9. P0/P1/P2/P3

P0/P1: подтверждённых findings0. P2:8 OPEN (MOD-QA-01…08), severity обоснована в каждом файле. P3: подтверждённых отдельных findings0;2px manual_review не повышен до defect. Окончательный module verdict **FAIL** по UX/moderation accessibility и отображению, несмотря на215 passing targeted tests. Вывод относится к описанному локальному snapshot и реально выполненным cells.
''')
put('SOURCE-MAP.md','''# Source → реальный контракт → свежая проверка

| Source | Контракт / связь | Evidence |
|---|---|---|
| catalog/domain_admin/volunteer.py:get_urls/moderation_hub_index/detail | admin.site.admin_view, paginator25, detail errors409 и обязательная причина | matrix/ACL/flows |
| catalog/services/moderation_hub.py:reviewer_scopes/query/detail | content через platform place.publish, affiliation через change_placeownershiprequest; свежий actor | acl195 |
| catalog/services/volunteer_proposals.py:review | ревизии идут через publication.apply/return/reject, не прямой UI ORM | nativeflows |
| catalog/services/publication.py | candidate/base_content_version/dependencies vs live; photos/related apply | flows2/gallery-finish, unchangedtests |
| catalog/services/volunteer_places.py + domain_admin/volunteer.py:delete | created_by actor + owner=NULL scope, fresh role/soft delete | acl/role revoke/delete |
| catalog/services/staff_roles.py | preset роли, activate/revoke path staffaccessuser | flows3-resume |
| catalog/domain_admin/place.py:EventAdmin/EventAdminForm + services/event_domain.py | updated_at/organizer lock, действующий organizer required; Event1 badfixture denied, Event2 valid native flow | editor-validation/editor-finish |
| catalog/domain_admin/specialist.py:SpecialistAdminForm/bulk actions | required fields и expected_updated_at в form; bulk status updates отдельны | specialist-save-proof/specialist-valid-finish, tests |
| templates/admin/volunteer/hub_index/detail | таблица без pager, plain string media | MOD-QA-01/02 |
| static/admin/js/kidsmap_notifications.js | SVG href попадает в focusables, warning fallback | MOD-QA-05 |
| static/admin/js/kidsmap_place_changelist.js | real AJAX guards + hardcoded confirmation | supplement/MOD-QA-06 |
| static/admin/css/pages/kidsmap_changelist.css | nowrap/min width + breakpoint при sidebar | MOD-QA-03 |
| templates/admin/catalog/specialist/change_form.html | AdminField.errors iterated as string | MOD-QA-07 |
| templates/admin/catalog/includes/km_changelist_search_panel.html | place-only filter whitelist; primary configs других моделей игнорируются | drawers/filter-contract/MOD-QA-08 |

Paths здесь относительны src/ либо root для static. Graph-first выполнен до широкого source exploration; dynamic ORM/admin registration проверены чтением source. Production UNKNOWN. Это source map, не rendered-browser доказательство; raw browser files выше являются отдельным подтверждением.
''')
journal=R/'docs/qa/module-acceptance-prompts.md';data=journal.read_bytes();entry=(P/'journal-entry.txt').read_bytes()
old=next(line for line in data.decode('utf-8').splitlines() if line.startswith('| 08 |'))
entry_row=next(line for line in entry.decode('utf-8').splitlines() if line.startswith('| 08 |'))
assert data==entry or ('module08-2026-10-10-r1/REPORT.md' in old and data.replace(old.encode('utf-8'),entry_row.encode('utf-8'),1)==entry),'Foreign journal changed; do not overwrite it'
new=f'| 08 | Админка, модерация и волонтёрский кабинет | DONE — FAIL (fresh audit complete; limits NOT RUN) | C:\\kidsmap; task33-progress; {X["head"]}; dirty QA/docs preserved; active_run NONE; runtime WORKTREE + existing .mo | [Отчёт](module08-2026-10-10-r1/REPORT.md), [verification](module08-2026-10-10-r1/verification.json), [matrix](module08-2026-10-10-r1/matrix.csv), [screenshots](module08-2026-10-10-r1/screenshots-manifest.json) | 8 OPEN P2 MOD-QA;215/215 Django PASS;{S["observations"]["PASS"]} PASS/{S["observations"]["FAIL"]} FAIL observations;{S["native_png"]} native PNG;SIMULATED transport/gaps recorded; Далее09; repairs отдельно; [handoff](module08-2026-10-10-r1/next-chat.txt) |'
journal.write_bytes(data.replace(old.encode('utf-8'),new.encode('utf-8'),1))
put('visual-review.json',json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'/root','reviewed_contacts':[x['path'] for x in read('contacts-manifest.json')],'scope':'21 DERIVED overview sheets; top viewport crops. Critical native PC/mobile photos/modal/table/error screenshots additionally opened. Not pixel-level review of every scroll position.'},indent=2))
plan=(P/'PLAN.md').read_text(encoding='utf-8').replace('- [ ]','- [x]');(P/'PLAN.md').write_text(plan+'\nЗавершено как FAIL; NOT RUN границы в REPORT/coverage-gaps, а не полный PASS всех сценариев.\n',encoding='utf-8')
print('Own nine-section report,8 findings/repair prompts, handoff09; only journal row08 updated')
