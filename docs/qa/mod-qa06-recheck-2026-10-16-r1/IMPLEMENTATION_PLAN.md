# MOD-QA-06 — перевод подтверждения снятия места с публикации

**PLAN COMPLETE / CONFIRMED OPEN. Требуется отдельное одобрение этого scope.** Одобрение MOD05 на него не распространяется. Приложение не изменено; candidate находится только внутри QA bundle.

## Подтверждённый ID и причина

Только **MOD-QA-06**. Свежий native browser RU/AZ/EN×390/1440:4source FAIL AZ/EN,2RU control PASS;6focus/name controls и1domain check PASS. [Raw result](native-recheck.js.result.json),6PNG. Все окна отменены. Это source cause: title/message/confirm/cancel захардкожены в `kidsmap_place_changelist.js`; свежие MO сами это не исправляют. Пользовательское имя уже локализовано и должно остаться неизменным.

Граф использован как подсказка: проект `home-ramin-kidsmap`, фактический root `/home/ramin/kidsmap`, generation2026-10-16T06:57:54Z. JS metadata changed после MOD05, HTML и AZ/EN PO partial; выводы проверены непосредственным чтением текущих файлов и rendered browser. Граф/его cache не копировались в репозиторий. Роли frontend-admin/Django выполняет один lead последовательно, без независимой сверки специалистом.

## Точные файлы:6

1. `static/admin/js/kidsmap_place_changelist.js` — только unpublish confirmation и его native `window.confirm` fallback. Получать5labels из существующего `km-changelist-i18n.dataset`; сохранять русский fallback при отсутствии атрибутов. В body/fallback подставлять `%(name)s` через callback replace, чтобы `$&` и другие символы имени не интерпретировались. Общий kmModal использует textContent для message; HTML не добавлять. Сохранить однострочный MOD05 focus patch.
2. `src/catalog/templates/admin/catalog/place/change_list.html` — добавить5translated data attributes в существующий hidden i18n node: `data-unpublish-title/message/confirm/cancel/fallback`. Пользовательские названия сюда не переносить.
3. `locale/ru/LC_MESSAGES/django.po` —4new active msgid для title/body/confirm/fallback, RU→RU.
4. `locale/az/LC_MESSAGES/django.po` —те же4keys с AZ переводом.
5. `locale/en/LC_MESSAGES/django.po` —те же4keys с EN переводом. Для отмены во всех языках использовать уже существующий `Отмена`→`Отмена/Ləğv et/Cancel`. Без общего makemessages и массового PO reformat.
6. **NEW** `src/catalog/testcases/test_mod06_unpublish_localization.py` — маленькая regression группа: actual authenticated changelist response с выбранным locale/prefix, HTMLParser извлекает data labels; проверить точные5значений/placeholder в RU/AZ/EN, а также cookie-selected AZ unprefixed. Сначала meaningful RED на текущем исходнике, затем GREEN на свежих изолированных MO. Existing tests/assertions не менять.

[Готовый пятифайловый diff](proposed.diff), [source/candidate SHA256](proposal-manifest.json). Шестой файл — только перечисленные поведенческие backend tests, без изменения existing assertions. Candidate не подключён к работающему приложению. Переводы:

| Элемент | RU | AZ | EN |
|---|---|---|---|
| Заголовок | Снять с публикации? | Nəşrdən çıxarılsın? | Unpublish? |
| Подтвердить | Да, снять | Bəli, nəşrdən çıxar | Yes, unpublish |
| Отмена | Отмена | Ləğv et | Cancel |

Body/fallback с именованным placeholder полностью приведены в diff. Название места не переводить заново, не записывать перевод в модель.

## Выполнение после одобрения

- Проверить checkout/HEAD/branch/dirty/active_run, source hashes, принадлежность/изоляцию собственного профиля; сохранить все чужие изменения/стенды. Новые QA artifacts в уникальном fix-run. DJANGO_TESTING=1, собственные DB/testDB/cache/media/private-media/email, fictional data, без checkout.env/productioncredentials; внешние обращения blocked либо явно SIMULATED. Если reused ownPG — сверить ID/ports/DB/source, не reseed существующий стенд. Для мутационных сценариев нужен отдельный собственный fixture/DB, не общий старый dataset.
- Написать новый тест, получить RED missing/untranslated labels; повторить только MOD06 browser failing subset. Не запускать весь старый корпус. Source/candidate drift проверять до patch.
- Применить только6перечисленных файлов. Собрать текущие RU/AZ/EN PO через scripts/build_isolated_locales.py в новый свой каталог, verify manifest **до django.setup**, единственный LOCALE_PATHS. ОбщиеMO не трогать. Сверить live PID/root/source/template/module origins и реально открытые ownMO.
- Targeted backend: только новая regression группа; shared sample — выбранный locale endpoint/prefix test из test_admin_i18n.py, без полного набора админки/модуля.
- Native GREEN RU/AZ/EN×360/390/768/1024/1280/1440: настоящий language switch, more→unpublish; точные title/body/buttons, неизменное fictional имя; visible warning icon, отсутствие overflow/обрезанных кнопок; Cancel и representative Escape, возврат фокуса MOD05. Console/network/PNG. Не повторять полную матрицу MOD04 sidebar/search/sort/columns.
- Дополнительные **явно SIMULATED** representative cases: временно недоступный kmModal→native window.confirm, локализованный body, dismiss; отсутствующие data labels→русский fallback, отменить. Не выдавать их за обычный primary flow. Имя с `<>&"'$&` проверить как текст, без новых DOM элементов/искажений. Все временные client substitutions удалять/reload.
- В primary сценарии все подтверждения отменяются: AJAX/loading/error/success notifications не выполняются, это явно NOT RUN, не считать их переведёнными. Hardcoded post-submit toasts и delete-confirmation — вне текущего подтверждённого ID; новые причины отдельно. Не менять публикационные endpoints/проверки/права/loading/undo.
- Domain fingerprint до/после, source↔MO manifest, node syntax/git diff check, semantic JSON gate, PNG manifest, exactcommands/exits/counts и preservation. Закрывать только MOD06 в проверенном scope. Полный module08 **один раз после всех его задач**, global отдельно; MOD07–08 отдельные планы, module09 не начинать. Без commit/push/deploy/production.

## Риски и границы

Главный риск — потеря/искажение имени при подстановке или неправильное HTML escaping атрибута; callback replace и textContent сохраняют строку, browser case с особыми символами это проверит. Отсутствующие gettext keys/флаги fuzzy выявляются compiled-catalog gate и exact rendered labels. Новые библиотеки/schema/API/CSS/общий modal engine не нужны. Текущий план не обещает локализацию всей очереди, всех уведомлений или delete modal.

Application patch/postpatch tests/full18cell GREEN пока **NOT RUN**. Одобрение нужно только на этот конкретный новый scope по требованию user/guide PLAN→IMPLEMENT-APPROVAL.
