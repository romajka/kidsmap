# PLAN MOD-QA-03 — approval pending

Дата: 2026-10-15. Фактический checkout `/home/ramin/kidsmap`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`, dirty WORKTREE, active_run NONE. Scope только MOD-QA-03. MOD01/02 LOCAL PASS сохранены. Этот план ещё не одобрен и не применён.

## Подтверждённый баг

Перенос общей панели поиска уже работает: старое переполнение страницы до1162px не воспроизвелось. Не исправлять его повторно.

Остались три части того же responsive-контракта:

- Place, RU1024, раскрытый sidebar: ширина `col_updated` 0px, строки470.34375px. Фиксированная раскладка вместе с заданными ширинами соседних колонок вытесняет дату.
- Place/Event/Specialist: выше768px у `.card-body.table-responsive` задан `overflow:visible!important`. Широкая таблица теряет собственную прокрутку, правые колонки обрезаются внешним контейнером. Например RU1024 expanded Event1325px/viewport634px и Specialist1116px/634px. Отсутствие root overflow не означает доступность колонок.
- Сортировка всех трёх очередей: AZ390 left−19.96875px, EN360 left−10.515625px, EN390 left−34.515625px. Меню шире summary, а выравнивание по правому краю выводит его левую часть за экран.

Свежий baseline: 108 основных сочетаний (3очереди ×RU/AZ/EN ×360/390/768/1024/1280/1440 ×2sidebar), 288 состояний, 1037PASS/84FAIL. Исходные результаты и точечная коррекция ожидания анимации сохранены; assertions не ослаблялись. Это подтверждение OPEN, не приёмка исправления.

## Единственный файл приложения

`/home/ramin/kidsmap/static/admin/css/pages/kidsmap_changelist.css`

Добавить27строк в конец текущего dirty-файла, сохранив все существующие байты:

1. Только у Place/Event/Specialist включить `overflow-x:auto!important; overflow-y:hidden!important` на viewport таблицы.
2. Только Place сохранить fixed layout, задать таблице `min-width:1000px!important`, заголовку даты `width:140px!important`. Недостающую ширину получать локальной прокруткой, без растягивания страницы.
3. Только этим трём очередям при≤580px выровнять `.km-sort-dropdown` по левому краю summary (`left:0;right:auto`). Существующее ограничение ширины меню сохранить.

Точный предлагаемый diff: [proposed.diff](proposed.diff). Полный файл-предложение: [proposed-kidsmap_changelist.css](proposed-kidsmap_changelist.css); исходный/proposed SHA и границы: [proposal-manifest.json](proposal-manifest.json). Предложение не является загруженным CSS приложения.

Файлы для source-сверки, без правок: shared `km_changelist_search_panel.html`, три `change_list.html`, `PlaceAdmin.col_updated`, JS управления popover и колонками, admin layout CSS. Backend/JS/шаблоны/PO/permissions/schema не входят в patch. Toolbar/sidebar не перерабатываются.

## Почему этот вариант

SIMULATED CSS, внедрённый только в собственный браузер, дал Place30 состояний: дата≥140px, строки80.3–80.5px; 21широкая таблица прокручена колесом внутри блока, scroll страницы0. Ещё18mobile sort состояний трёх очередей поместились на экран с видимым keyboard focus; 12Event/Specialist1024 expanded/collapsed прокручены локально. Синтетические данные до/после совпали. Это проверка реализуемости, НЕ postpatch GREEN. Альтернативный auto layout увеличивал таблицу до1440.81px и не выбран.

## После одобрения

1. Повторно сверить HEAD/branch/active_run и SHA точного CSS. Если файл изменился — сохранить новое чужое содержимое и оценить применимость; не заменять его устаревшей копией.
2. Применить только предложенное добавление. Проверить diff и источник CSS работающего собственного профиля, актуальность953source paths и manifest3изолированных MO. Никакого `.env`/production.
3. Повторить целевую native браузерную матрицу 3очереди×3locale×6width×2sidebar с теми же baseline assertions. Ожидать реальную конечную ширину sidebar, не фиксированную задержку. На mobile раскрытый sidebar закрывает фон штатным overlay; меню фона проверять после native закрытия overlay.
4. Проверить локальную горизонтальную прокрутку колесом/клавиатурой и доступность даты/правых actions; root≤1px overflow, читаемые строки, search/filter/sort/column controls и их dropdown не обрезаны. Keyboard Tab/Enter/focus, закрытие меню и повторное открытие. Native GET search→sort→reset→reload и скрытие/возврат колонки; без domain mutation.
5. Проверить row actions/readiness popover после включения overflow, в том числе крайние строки и правый край после scroll. Если потребуется JS/portal либо иная новая причина — зафиксировать и отдельно согласовать расширение до patch.
6. Сохранить console/network, PNG manifest, точные команды/exits/counts, source runtime, data fingerprint и сохранность чужих файлов/стендов. Ошибки внешних шрифтов отдельно отмечать как намеренно заблокированные. Не ослаблять assertions.
7. Создать новый уникальный fix-run/report и обновить статус только при фактическом GREEN. Полный модуль08 — один раз после всех его задач. MOD04–08 не начинать автоматически в рамках этого approval.

Чисто CSS-правка: meaningful regression — текущий rendered-browser RED и последующий native GREEN; зеркальные unit-тесты CSS не добавлять. До approval postpatch, дополнительные функциональные сценарии из пунктов4–5, ACCEPT-08, global acceptance и production остаются NOT RUN.

Требуется отдельное одобрение именно этого однофайлового scope по пользовательскому правилу PLAN / IMPLEMENT-APPROVAL. Одобрения MOD01/02 к нему не относятся.
