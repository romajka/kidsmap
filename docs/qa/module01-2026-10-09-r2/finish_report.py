"""Write only this run's audit deliverables and module 01 journal row."""
from pathlib import Path
P=Path(__file__).resolve().parent
F=P/'findings';F.mkdir(exist_ok=True)
items=[
('01','P2','Причина отказа не показана владельцу','PRE-EXISTING BASELINE','owner','/ru/account/places/1/edit/; /ru/account/places/2/edit/',
'Создать и отправить место через кабинет. Модератор отклоняет с вымышленной причиной. Открыть редактор владельца, reload, выполнить новый вход.',
'Владелец видит сохранённую причину и может исправить заявку.','Статус отказа виден, текст причины отсутствует во всех трёх повторных проверках; revision.review_note заполнен.',
'rejection-recheck.result.txt; branch-lifecycle-stable.result.txt; screenshots/owner-rejection-390.png; diagnostic.json',
'src/catalog/templates/pages/includes/owner_place_continuous.html:7; views.py:_place_revision_context; publication.py:review. Контекст revision передаётся, review_note сохраняется, continuous template не выводит причину. Уверенность высокая.',
'Ограниченный сбой обратной связи мешает исправить заявку; потеря самой причины в DB не обнаружена.',
'Owner continuous template, локализация и regression проверки отказа. Зависимость: действующая ACL и revision context.',
'Покажи владельцу последнюю причину отказа в continuous редакторе места, с безопасным экранированием и корректными RU/AZ/EN подписями. Сохрани ACL и жизненный цикл revision. Проверь отказ → reload → logout/login → исправление → повторная отправка в реальном браузере; добавь проверку сохранённой причины. Не меняй остальные экраны.'),
('02','P2','Кнопки карты владельца молчат без SDK','PRE-EXISTING BASELINE','owner','/ru/account/places/1/edit/',
'Открыть карту без внешнего SDK. Ввести вручную 40.4093 / 49.8671. Нажать очистку и определение местоположения.',
'Очистка работает без провайдера; недоступность геолокации/SDK получает понятную обратную связь.',
'Оба действия оставляют координаты и статус без изменения. Две свежие проверки FAIL.',
'map-recheck.result.txt; owner-coordinate-roundtrip.effective.result.txt; deep-matrix.result.txt',
'static/js/owner_place_map_picker.js:initMapPicker и provider initializers. В unavailable fallback отключается поиск, но обработчики clear/locate остаются внутри provider initialization. Уверенность высокая.',
'Ручной сценарий зависит от внешнего SDK, хотя координаты уже введены; ограниченное нарушение управления формой.',
'Owner map picker; общий контракт location resolution. Зависимость: серверная проверка координат.',
'Сделай очистку ручных координат и понятный ответ на запрос геолокации независимыми от SDK карты. Сохрани серверные ограничения географии и не подставляй 0/0. Проверь отсутствие/позднюю загрузку SDK, отказ и отсутствие geolocation, ручную точку → clear → reload, видимый статус и сохранность других полей.'),
('03','P1','Смешанная правка опубликованного места блокирует одобрение','PRE-EXISTING BASELINE','owner → moderator','/ru/account/places/1/edit/ → moderator revision review (точный URL в review-inspect.result.txt)',
'Одобрить место. В одной сессии изменить название/адрес и цену с 15 на 18, сохранить, отправить candidate. Открыть эту revision модератором без второго редактора.',
'Цена по действующему immediate контракту меняется сразу; candidate identity/address остаётся пригодным к одобрению, если конкурентных изменений не было.',
'Review сообщает «Карточка изменилась после отправки…» и не даёт одобрить. У candidate base старые price_from/price_to, live уже 18.00. Исправленные identity/address не могут пройти этот путь.',
'published.result.txt; resubmit-diagnose.result.txt; review-inspect.result.txt; candidate-diagnostic.json; screenshots/review-published-error-1440.png',
'publication.py:_immediate/propose (base обновляется по immediate keys); pricing_plans.py:sync_legacy_price_fields; volunteer_places.py:revision_base_matches. Производные price_from/price_to меняются вместе с pricing, но остаются устаревшими в candidate base. _apply уже вызывает refresh_from_db: отсутствие refresh не является причиной. Уверенность высокая для воспроизведённого mixed edit.',
'Блокирует ключевой контракт одобрения опубликованной карточки при конкретном обычном trigger. Не утверждается блокировка всех заявок или production.',
'Publication/revision rebasing и pricing projections; зависит от optimistic concurrency и атомарности.',
'Исправь PLACE-QA-03: после допустимой immediate правки pricing синхронизируй связанные производные поля candidate base атомарно, сохранив обнаружение настоящих конкурентных изменений. Не отключай revision_base_matches/CAS и не расширяй поля immediate без согласованного контракта. Сначала воспроизведи mixed name/address + price edit, затем проверь UI submit → moderator approve → live identity, отдельную цену, повторную правку, две вкладки и настоящего второго редактора. Existing assertions не ослаблять.'),
('04','P2','Район остаётся disabled после очистки точки','PRE-EXISTING BASELINE','owner','/ru/account/places/1/edit/',
'На свежей форме ввести ручную точку, очистить lat/lng, выбрать регион Baku. Осмотреть district.',
'При ручном выборе региона доступен предусмотренный формой выбор района.',
'Регион baku выбран, lat/lng пусты, district.disabled=true. Выбрать район нельзя.',
'district-enable.effective.result.txt; manual-roundtrip.effective.result.txt',
'static/js/location_resolution.js:38–45 и привязки continuous owner form. Пустые координаты отключают district; согласованного пересчёта при ручной смене региона в этом пути не обнаружено. Уверенность высокая по поведению, причинная связь подтверждена source.',
'Ограниченная недоступность обязательной географии после изменения режима ввода.',
'Location state machine и owner form bindings; зависит от server geographic policy.',
'Исправь переход ручная точка → очистка → ручной регион/район в continuous редакторе. Определи единый пересчёт доступности district по актуальным координатам и региону; не обходи серверную проверку простым снятием disabled. Проверь Baku/другой регион, пустую/неполную/неверную точку и reload с сохранённым районом.'),
('05','P2','Открытый select категории выходит за экран 360 px','PRE-EXISTING BASELINE','moderator/admin editor','/admin/catalog/place/3/change/ (django_language RU/AZ/EN)',
'В Chromium viewport 360 px открыть выпадающий выбор категории административного редактора, повторить RU/AZ/EN.',
'Открытый список целиком укладывается в viewport, доступен с клавиатуры.',
'Ширина document scroll становится 373 px при viewport 360; воспроизведено во всех трёх языках. Другие проверенные ширины этого дефекта не показали.',
'deep-matrix.result.txt; contact-sheets/deep-moderator-open-control.jpg; screenshots/deep-moderator-open-control-ru-360.png',
'static/admin/css/pages/kidsmap_place_form.css:1104–1109: min-width 320 плюс позиционирование. Уверенность высокая по rendered geometry; размеры native popup вне DOM не оценивались.',
'Обязательная мобильная ширина получает горизонтальную прокрутку при выборе категории.',
'Admin category popup responsive CSS; зависит от trigger position и длинных labels.',
'Ограничь ширину и позицию открытого category popup административного редактора доступным viewport без обрезки вариантов. Проверь RU/AZ/EN × 360/390/768/1024/1280/1440, длинные значения, Tab/Shift+Tab/Enter/Escape и фокус после закрытия. Подтверди свежими screenshots и scrollWidth; не делай общий редизайн.'),
('06','P2','Скомпилированные переводы этого WORKTREE устарели','ENVIRONMENT FAILURE — GENERATED ARTIFACT STALENESS','admin editor','/admin/catalog/place/3/change/ (django_language AZ/EN)',
'Запустить свежую isolated DB с текущими locale/*.mo. Открыть AZ/EN административный редактор; сравнить targeted GNUTranslations lookup с соответствующими .po.',
'Запущенные каталоги соответствуют текущему переводному source: Description/Təsvir для описания, перевод сообщения карты.',
'html lang правильный, но label описания Cədvəl/Schedule, сообщение карты русское. В .po нужные значения уже правильные; игнорируемые .mo содержат старые значения/не содержат ключ предупреждения.',
'compiled-translations.json; localization.result.txt; screenshots/localization-admin-az-390.png; screenshots/localization-admin-en-390.png; snapshot.json',
'locale/az/LC_MESSAGES/django.mo, locale/en/LC_MESSAGES/django.mo; config LOCALE_PATHS. Подтверждены GNUTranslations lookup, source .po и git ignore. Уверенность высокая; это не доказательство дефекта текущих .po или production.',
'Локальная сборка неверно подписывает поле и смешивает языки; граница finding ограничена фактически работающими compiled assets.',
'Локальная build/stand preparation для переводов. Зависимость: gettext tooling и manifest compiled assets.',
'В отдельном согласованном запуске подготовь актуальные compiled каталоги из текущих .po в изолированном стенде, зафиксируй source/asset hashes и повтори PLACE-QA-06 в реальном RU/AZ/EN браузере. Определи воспроизводимый build шаг, предотвращающий stale .mo. Не переписывай правильные .po, не меняй чужие compiled assets и не выполняй production/deploy.'),
('07','P3','Тип места остаётся русским в AZ/EN','PRE-EXISTING BASELINE — SOURCE TRANSLATION GAP','owner','/az/account/places/1/edit/; /en/account/places/1/edit/',
'Открыть выбор типа места в AZ/EN кабинете владельца, прочитать варианты business/public space; сверить gettext ключи в source каталогах.',
'UI choices переведены на выбранный язык; enum значения неизменны.',
'В обоих языках варианты «Бизнес» и «Общественное место». В RU корректно. Для этих msgid нет записей в AZ/EN .po и .mo.',
'edge-cases.result.txt; compiled-translations.json',
'src/catalog/forms.py:1042–1044 gettext choices, locale AZ/EN .po. В отличие от 06, простой rebuild не добавит отсутствующий source перевод. Уверенность высокая.',
'Небольшая локализационная несогласованность, не блокирует сохранение.',
'AZ/EN gettext entries для nature choices; зависит от согласованного rebuild каталога.',
'Добавь корректные AZ/EN переводы двух nature choices «Бизнес» и «Общественное место», сохрани enum и бизнес-логику. В изолированном стенде собери каталоги и проверь реальные select варианты RU/AZ/EN, сохранение и reload; не заменяй значения enum переводными строками.')
]
for n,sev,title,kind,role,url,steps,expect,actual,evidence,cause,priority,scope,prompt in items:
    links='; '.join(f'[{x}](../{x})' for x in evidence.split('; '))
    (F/f'PLACE-QA-{n}.md').write_text(f'''# PLACE-QA-{n} — {title}

OPEN · {sev} · {kind} · local module01-20261009-r2, 2026-10-09. Исправление не выполнено.

**Роль:** {role}. **URL/endpoint:** `{url}` (origin `http://localhost:8813`).

**Шаги:** {steps}

**Ожидание:** {expect}

**Факт:** {actual}

**Свежие доказательства:** {links}.

**Первопричина / уверенность:** {cause}

**Почему {sev}:** {priority}

**Область исправления / зависимости:** {scope}

## Самостоятельный промпт исправления

```text
Работай в фактическом checkout KidsMap. Прочитай AGENTS.md, канонические .agents и docs/qa/module01-2026-10-09-r2/findings/PLACE-QA-{n}.md. Сначала проверь актуальные HEAD/WORKTREE/active_run; сохрани чужие изменения и стенды. Историческое evidence используй как repro checklist, повтори на свежем DJANGO_TESTING=1 стенде с отдельными DB/cache/media/private-media/email и вымышленными данными. Без production credentials, внешних интеграций, commit/push/deploy.

{prompt}

Подготовь конкретный план и согласуй scope реализации до изменения приложения согласно каноническим инструкциям. После согласования выполни только этот finding, meaningful regression проверки и rendered browser сохранение/reload. Сохрани новый отчёт, точные команды/exit codes, screenshots и ограничения NOT RUN. Не считай этот audit разрешением на реализацию.
```
''',encoding='utf-8')

(F/'README.md').write_text('# Отдельные findings и готовые repair prompts\n\n'+ '\n'.join(f'- [PLACE-QA-{n}: {title} — {sev}](PLACE-QA-{n}.md)' for n,sev,title,*_ in items)+'\n\n01–05, 07: текущий baseline приложения; 06: отдельная локальная проблема generated assets. Regression от изменений приложения этого запуска отсутствует: приложение не менялось.\n',encoding='utf-8')

(P/'visual-review.md').write_text('''# Свежий визуальный просмотр r2

Реальный Chromium, screenshot capture после выполнения DOM/UI действий. Все 18 locale/width cells присутствуют в матрице. Автоматически измерены document/viewport geometry, состояния открытых контролов, сохранения, network/pageerrors. Это не заявление об индивидуальном просмотре каждого пикселя всех 381 PNG.

Лично просмотрены текущие contact sheets: guest-public, deep-moderator-open-control, deep-owner-errors-long, moderator-filled, deep-moderator-errors-long; отдельные owner-rejection-390 и review-published-error-1440. Финальный просмотр: state-owner-offline-az-1024 (видимый фокус, сохранённый текст, сообщение отсутствия сети), guest-public overview (18 cells), public-final-2-en-360 и modal-admin-ru-360. Геометрия подтверждает overflow категории только при 360; остальные измеренные cells без такого overflow. Полный keyboard/screenreader audit NOT RUN.

Некоторые ранние public screenshots сняты при восстановленном scroll. Финальные public-final-* сняты в начале страницы; актуальность фото отдельно проверена decoded pixel comparison с editor, включая reload и гостевой новый context. Палитра фикстур вымышленная, однотонные изображения намеренные. Нельзя выводить качество реальной фотографии по этим фикстурам.
''',encoding='utf-8')

(P/'next-chat.txt').write_text('''Продолжаем KidsMap. Работай в фактическом checkout; на этом ПК он C:\\kidsmap. Прочитай AGENTS.md, канонические .agents и docs/qa/module-acceptance-prompts.md целиком. По журналу 01 и 02 завершены с FAIL; первый незавершённый модуль — 03 «Специалисты и приватные документы». Выполни только его полный промпт до нового отчёта. Модуль 13 после 01–12.

Проверь заново HEAD/branch/dirty WORKTREE/active_run. Последний module01 r2: HEAD 8d188b316f800fbedf0b1e376905dfd4924cb1b6, task33-progress, active_run NONE. Это исторический snapshot, не новое доказательство. Отчёт docs/qa/module01-2026-10-09-r2/REPORT.md: 6 findings приложения + отдельный stale compiled locale finding, без исправлений.

AUDIT ONLY: сохрани чужие изменения, отчёты и стенды. Существующие 8811/8812 и module01 r2 8813/DB 55433 не присваивай и не останавливай. Создай новый изолированный DJANGO_TESTING=1 стенд с отдельными DB/cache/media/private-media/email, вымышленными данными и без внешних credentials/transport. Проверяй running source/compiled asset hashes против WORKTREE; stale .mo на этом ПК учитывать отдельно. Не считать прежние PASS свежим evidence.

Приложение, правила, миграции и existing assertions не исправляй. Сохрани уникальный module03/date/run report, evidence, PC/mobile screenshots, отдельные findings и копируемые repair prompts. Недоступное оставь NOT RUN. Обнови только строку 03 журнала и дай следующий handoff. Без commit/push/deploy/production.
''',encoding='utf-8')

(P/'REPORT.md').write_text('''# Модуль 01: постоянные места — свежая приёмка r2

**FAIL в выполненном scope.** Аудит завершён; 6 подтверждённых проблем приложения и 1 отдельная проблема compiled assets. Недоступные части остаются NOT RUN. Дата запуска: 2026-10-09, завершение оформления: 2026-10-10, Asia/Baku. Роль: lead `/root`, направления Django/integration/browser выполнены последовательно одним исполнителем, без заявления независимой проверки. Definition: `.agents/agents/kidsmap-orchestrator/agent.md`. Режим AUDIT ONLY; production не подключался.

## 1. Состояние области и snapshot

Checkout `C:\\kidsmap`; branch `task33-progress`; HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`; active_run `NONE`, файл сохранён. На входе уже были изменённый журнал и untracked module01-r1/module02-r1; это чужая работа. Новый run `module01-20261009-r2`. Свежие материалы: [snapshot](snapshot.json), [изоляция](isolation.json), [финальная проверка](verification.json), [matrix CSV](matrix.csv), [matrix JSON](matrix.json), [commands/exit codes](command-ledger.jsonl), [inventory с hash raw attempts](results-inventory.json).

Стенд `http://localhost:8813`, собственный PID 40932; PostgreSQL17-alpine контейнер `kidsmap-module01-20261009-r2`, порт55433, fresh DB, 175 применённых миграций. Python3.12.15, Django6.0.2, Chromium Playwright1243. Прежние серверы8811/PID6112 и8812/PID40848, PG55431/55432 сохранены. Это Windows checkout с Linux PostgreSQL через WSL, а не перенесённая сессия исходного ПК. Стенд r2 оставлен для просмотра.

`/qa/version/` отдаёт текущие HEAD, testing=true и manifest digest `589c2d398f3d24d62af28b72e47bbfaeb1c68f8767a080fd83be3a5a5a96b684`. 2776 файлов src/static/config/locale сверены до/после; изменений нет. Запущены исходники этого WORKTREE с QA-only settings/URL configuration, без monkeypatch бизнес-функций. В manifest включены существующие ignored locale .mo: стенд соответствует AS-IS WORKTREE, включая stale assets, а не чистой пересборке HEAD. Именно поэтому finding06 отнесён к environment.

Прочитаны AGENTS.md, canonical README/registry/orchestrator, architecture/source-of-truth/current-snapshot, audit/engineering/orchestration/testing contracts, `content-entry-audit-2026-10-06.md`, `admin-place-map-fix-2026-10-09.md` и промпт01. Обязательные документы доступны; отсутствующие обязательные документы не обнаружены. План: [PLAN](PLAN.md). Codebase-memory C-kidsmap: ready, 77124 nodes/163927 edges, 74 partial parses; индекс generation 2026-10-09T19:09:23Z. Частичная/недоступная coverage критических файлов не принималась за полноту: переходы и dynamic ORM связи сверены с source. Graph cache в evidence не скопирован.

Изоляция: DJANGO_TESTING=1, отдельные DB/LocMem cache/mail/media/private-media/cookies. `.env` не загружался; внешние ключи пусты; socket guard и browser route блокируют внешний transport. Credentials вымышленных пользователей остаются в ignored scratch и не записаны в deliverables. ORM использован для начальных fixture identities/organization и read-only диагностики; проверяемые переходы создания/черновика/модерации/публикации/изменения выполнены UI, не ORM save.

### Выполненные сценарии

| Scope | Результат | Свежий evidence |
|---|---|---|
| Самостоятельное место: partial → draft → reload → login → error → correction → submit → rejection → resubmit → approve → public | Переходы PASS; причина отказа FAIL | lifecycle, moderation, rejection-recheck `.result.txt` |
| Филиал вымышленной организации, смена category/subcategory, повторный вход через UI | PASS; причина отказа FAIL | branch-fill-stable, branch-lifecycle-stable, final-branch-roundtrip |
| Названия/описания AZ/RU/EN, blank EN и public fallback | PASS content/fallback; UI labels FAIL отдельно | lifecycle, public-smoke, localization, edge-cases |
| Возраст/контакты/адрес, region/district, manual coords | Валидация и roundtrip PASS; district/owner no-SDK FAIL | coordinates, owner-coordinate-roundtrip.effective, manual-roundtrip.effective, map-recheck, district-enable.effective |
| Admin map recheck: no point, invalid range/half pair/0/0, clear; denied/unavailable geolocation | PASS выполненные; физический SDK/GPS NOT RUN | admin-create, edge-cases, geolocation |
| Free/paid/event pricing, 8 owner и 12 admin переключений | PASS без зависания; mixed published candidate FAIL | branch-fill-stable, admin-create, published, review-inspect |
| Place hours 09:00 отдельно от lesson14:00 | PASS public в трёх языках | branch-lifecycle-stable |
| Main/gallery/upload/reorder/remove/replace/promote → reload → public | PASS финальный roundtrip; invalid/corrupt/empty/oversize file ошибки PASS | media-awaited первые4, file-errors, final-branch-roundtrip, public-smoke |
| Foreign ID/rights/double save/two tabs/offline/input retention | PASS выполненные, реальный409 и сохранённый ввод | negative, state-matrix |
| Опубликованное: candidate identity отдельно от live; price/schedule immediate | PASS разделение; FAIL способность approve mixed price candidate | published, candidate-diagnostic, review-inspect |

Точные IDs/role/language/width/status находятся в matrix. У функциональных сценариев с несколькими viewport указан mixed и соответствующий script; мутационный lifecycle преимущественно RU. Нельзя трактовать display matrix как повторение полного lifecycle на каждом языке и ширине.

Контракт по source `src/catalog/services/publication.py:305` / `propose`: при explicit_save расписание (`schedule`, `schedule_mode`, structured schedule и notes) может применяться сразу; суммы legacy price fields и amount-only pricing_plans — сразу, если условия не менялись и в pending нет pricing/condition blockers. Остальные name/description, адрес/география, категория, фото/галерея и изменённые условия остаются candidate до review. Это условный контракт, а не обещание immediate для любой цены. Browser подтвердил live name/address неизменными до одобрения, schedule/amount immediate и photos после approval. Candidate payload/base/live сверены read-only диагностикой.

Реальный browser display/state matrix: RU/AZ/EN × 360/390/768/1024/1280/1440. 342 проверки состояний/geometry: 339 PASS, 3 FAIL (category popup360 в каждом языке). Включены empty/filled, map/gallery/open controls, long errors, loading/offline/conflict и modal keyboard. Дополнительно functional/localization rows дают итог454: **431 PASS / 17 FAIL / 6 NOT RUN**. Это строки наблюдений, а не454 независимых транзакции или17 разных дефектов.

381 свежий PNG, [manifest с SHA256](screenshots-manifest.json), 16 contact sheets; [визуальный просмотр и границы](visual-review.md). Ключевые: [PC review blocker](screenshots/review-published-error-1440.png), [mobile rejection](screenshots/owner-rejection-390.png), [mobile public](screenshots/public-final-2-en-360.png), [mobile modal](screenshots/modal-admin-ru-360.png), [offline/focus](screenshots/state-owner-offline-az-1024.png). Screenshot capture сделан настоящим Chromium после UI действий; source inspection/jsdom/HTTP200 не использовались как его замена.

## 2. Сильные стороны

Сохранение частичного черновика, reload и повторный вход удерживают данные. Age/coordinate/file validation не уничтожает ввод и saved photo. Unauthorized ID не раскрывает чужой draft, two-tab конфликт защищает более новые данные, offline состояние сообщает о несохранении. Филиал проходит отказ/повторную отправку/одобрение. Public RU/EN явные переводы соответствуют сохранённым полям, blank EN остаётся blank в storage и показывается fallback с соответствующей подсказкой. Финальные фото сверены с editor по decoded pixels и reload. Место и занятия имеют отдельные часы.

## 3. Реальные проблемы

Все findings OPEN, исправлений нет; у каждого собственные repro, факт/ожидание, evidence, причина/уверенность, severity rationale, scope/dependencies и копируемый repair prompt: [полный список](findings/README.md).

| ID | Severity | Классификация | Проблема |
|---|---|---|---|
| [PLACE-QA-01](findings/PLACE-QA-01.md) | P2 | pre-existing baseline | Owner не видит сохранённую причину отказа |
| [PLACE-QA-02](findings/PLACE-QA-02.md) | P2 | pre-existing baseline | Clear/locate молчат без SDK |
| [PLACE-QA-03](findings/PLACE-QA-03.md) | P1 | pre-existing baseline | Mixed identity+pricing edit создаёт stale candidate base и блокирует approve |
| [PLACE-QA-04](findings/PLACE-QA-04.md) | P2 | pre-existing baseline | Район disabled после перехода point→manual region |
| [PLACE-QA-05](findings/PLACE-QA-05.md) | P2 | pre-existing baseline | Admin category popup overflow360 |
| [PLACE-QA-06](findings/PLACE-QA-06.md) | P2 | environment/generated assets | Stale ignored .mo искажают description/map labels |
| [PLACE-QA-07](findings/PLACE-QA-07.md) | P3 | baseline source translation gap | Nature choices русские в AZ/EN |

Предыдущие reports не использовались как evidence. App исходники в этом запуске не менялись, поэтому новые regression от его app изменений отсутствуют; слово baseline означает воспроизведено на текущем snapshot, а не историю появления или production статус.

## 4. Tech debt

Candidate base зависит от производных legacy price projections; coupling подтвержден03. Map provider initialization связывает доступность базовых form actions с SDK02. Generated gettext assets могут отставать от source06. Это конкретные области для отдельного плана, не разрешение на рефакторинг всего редактора.

## 5. Risks и simulated integrations

Главный риск выполненного пути — невозможность одобрить mixed published edit без отклонения/повторного исправления. Реальные Google Maps, external network/API, физический GPS не запускались. Denied/unsupported geolocation и coordinates заданы browser simulation; loading создан задержкой native autosave response, offline через Chromium offline. Реальный server409 проверен. Эти сценарии явно SIMULATED integrations, не доказательство работы провайдера.

Console/network собраны в raw results. Uncaught pageerrors в display/state matrices не обнаружены; network не объявляется полностью чистым: ожидаемые422/409, invalid upload responses, blocked external requests и temporary thumbnail404 при раннем draft отдельно видны в raw evidence. Общий native CLI exit0 не означает PASS каждой row.

## 6. Dead/legacy candidates

Удаление не предлагается. Legacy price fields участвуют в действующем publication contract, статус ACTIVE/CANNOT DELETE по этому scope. Наличие старых reports и duplicated QA helper scripts не доказывает dead application code. Database/data deletion audit NOT RUN.

## 7. Tests gaps, точные команды и exit codes

Выполнено заново: 84 существующих Django tests, OK, native exit0, 53.978s: [log](backend-repeat.txt), [result](backend-result.json).

```powershell
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r2/test_driver.py
# Native command inside driver:
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r2/run.py test catalog.testcases.place_readiness catalog.testcases.test_admin_candidate_cover catalog.testcases.test_task33_place_continuous catalog.testcases.photo_workflow catalog.testcases.test_place_json_and_pricing_modes
$env:KIDSMAP_JSDOM='C:\\kidsmap\\.tmp\\phone-dom\\node_modules\\jsdom'
node --test scripts/test_location_resolution.cjs
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r2/drive.py lifecycle.js
# Each actual browser scenario command, duration and CLI exit: command-ledger.jsonl
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r2/package.py
git diff --check
```

Native node result7/7 PASS exit0: [log](location-js-tests.txt), [result](location-js-result.json). First JS attempt lacked historical jsdom directory: environment failure, rerun used existing supported KIDSMAP_JSDOM override. A Windows CP1251 wrapper print error occurred after native output/result were saved; native test result remains exit0. Expected mocked storage failure traces in tests are not app failure. Existing assertions не изменялись.

Fresh stand commands:

```powershell
wsl -- docker run -d --name kidsmap-module01-20261009-r2 --label kidsmap.qa.owner=module01-20261009-r2 -e POSTGRES_DB=module01 -e POSTGRES_USER=module01 -e POSTGRES_HOST_AUTH_METHOD=trust -p 127.0.0.1:55433:5432 postgres:17-alpine
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r2/run.py snapshot
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r2/run.py migrate
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r2/run.py seed
.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r2/run.py serve
```

Serve — длительно работающий процесс; отсутствие terminal exit не выдаётся за успешно завершённый command. Runtime endpoint и source hash verification подтверждают старт. Fixture password не включён в команды отчёта. Для browser bootstrap и технических операций см. PLAN/scripts и ledger; copied helper source не означает выполненный сценарий.

Harness setbacks не выданы за app findings: старый selector published-save, race saved-state waits, lazy image decode до scrollIntoView, неверное ожидание orange fixture вместо blue, сравнение '0' vs '0.000000', ошибочное ожидаемое AZ название. Первичные attempts сохранены, итоговая выборка в package.py исключает superseded rows. 0/0 draft retention/admin refusal проверены, но isolated owner0/0 publication после harness stop остаётся NOT RUN.

NOT RUN: full backend/JS suites; полный mutation lifecycle во всех18 language/width cells; настоящий SDK/GPS/external integration; exhaustive keyboard всех контролов, screenreader, Firefox/Safari и физические устройства; owner0/0 isolated submit; production. Enter/Tab/Shift+Tab/Escape modal и часть form controls проверены; Space для всех widgets и полная accessible focus traversal не подтверждены. Продолжение независимых проверок выполнено несмотря на harness/environment stops.

## 8. Recommendations и handoff

Сначала отдельно согласовать scope03 (publication), затем01/02/04/05. Для06 — воспроизводимый isolated compiled catalog build; source gap07 проверить отдельно после rebuild. Промпты исправления самостоятельны, но не авторизуют реализацию. Аудит не делает commit/push/deploy и не меняет приложение/правила/миграции/assertions.

Из journal следует, что02 уже DONE; повтор module01 выполнен по последнему явному заданию пользователя. Следующий незавершённый модуль03;13 после остальных. [Текст следующего чата](next-chat.txt). Обновлена только строка01; чужая строка02 и остальной текст сохранены побайтно. Финальная проверка2776 source files и888 ранее существовавших files, active_run и secret scan — в verification.json.

## 9. P0/P1/P2/P3

P0:0. P1:1 (03). P2:5 (01/02/04/05 application +06 environment). P3:1 (07). Итого6 app findings +1 environment finding. Вывод FAIL ограничен выполненными local сценариями; «всё работает» и production readiness не заявляются.
''',encoding='utf-8')

J=P.parents[0]/'module-acceptance-prompts.md'
b=J.read_bytes();old=next(line for line in b.splitlines() if line.startswith(b'| 01 |'))
new='| 01 | Постоянные места | DONE — FAIL (fresh audit r2; limits NOT RUN) | C:\\kidsmap; task33-progress; 8d188b316f800fbedf0b1e376905dfd4924cb1b6; entry QA-only dirty; active_run NONE unchanged; runtime WORKTREE + existing .mo | [Отчёт r2](module01-2026-10-09-r2/REPORT.md), [evidence](module01-2026-10-09-r2/verification.json), [matrix](module01-2026-10-09-r2/matrix.csv), [screenshots](module01-2026-10-09-r2/screenshots-manifest.json); [история r1](module01-2026-10-09-r1/REPORT.md) | 6 app OPEN + 1 environment PLACE-QA; 84 Django + 7 JS OK; 381 PNG; SDK/GPS/full suites/exhaustive mutation matrix NOT RUN; Далее 03 (02 DONE); repair отдельным scope; [handoff](module01-2026-10-09-r2/next-chat.txt) |'
J.write_bytes(b.replace(old,new.encode('utf-8'),1))
print('Report, seven separate findings/prompts, visual review, handoff and only journal row01 written.')
