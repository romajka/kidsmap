# MOD-QA-03: дополнительный scope меню — approval pending

Дата 2026-10-15. CSS-план уже одобрен и применён точно:27строк в `static/admin/css/pages/kidsmap_changelist.css`. Повторное согласование CSS не требуется. Этот документ касается новой причины и пока НЕ применённого JS.

## Причина

Нативная проверка меню крайних строк дала7PASS/5FAIL:

- Place390, последняя строка: фиксированное меню действий открывается только вниз, top930.55/bottom1059.80 при viewport950px. Последние пункты за экраном.
- Event390/1024, первая и последняя строки: `.km-admin-action-menu__panel` находится внутри таблицы; `position:absolute` и clipping предков делают меню недоступным для hit-test, даже когда прямоугольник находится на экране.

[Результаты реального patched CSS](native-menu-safety.js.result.json). В контролируемом браузерном replay **точного CSS до patch** получены те же5FAIL, [replay result](native-prepatch-menu-replay.js.result.json). SHA256 replay `990a376f7944aa801af6b5c306540fd724c7836c85cb500e9741ee20aae2a171` совпадает с approved prepatch manifest. Только response CSS был заменён в собственном браузере; JS/fixtures текущие и неизменённые. Это SIMULATED baseline replay, не новый запуск старого checkout. По сравнению до/после причина существовала до CSS-патча.

## Единственный дополнительный файл приложения

`/home/ramin/kidsmap/static/admin/js/kidsmap_place_changelist.js`

Этот файл подключён уже сейчас в Place/Event/Specialist. Предложение ограничивает новый portal обработчик Event-очередью, а позиционирование существующего меню — его текущим Place trigger. Backend, HTML, permissions, payload действий, URL, labels/переводы и уже одобренный CSS не менять.

Точный [MENU_SUPPLEMENT_V2.diff](MENU_SUPPLEMENT_V2.diff), [полный предложенный JS](proposed-menu-v2-kidsmap_place_changelist.js), [SHA manifest](menu-supplement-v2-manifest.json). Исходный JS SHA `c187eda8361fdc96b7c4cc0409c09640cc9cd09bc0abc39325202af3eea24c65`; proposed SHA `f51eac64f50ce6bd2f5430956d8e19b6eb17f147e10d7a319a5f1e706e00d767`.

1. Общая небольшая функция для координат меню: измерить после открытия, ограничить края viewport, при нехватке места снизу открывать выше; для очень низкого viewport ограничить высоту с внутренней прокруткой.
2. Вместо прежних5строк фиксированного открытия Place вниз вызвать эту функцию.
3. У открытого native Event `<details>` временно переносить **тот же** panel в `document.body`, позиционировать fixed, сохраняя исходный parent/style/ссылки. При закрытии вернуть исходный узел и style. Не клонировать actions и не добавлять новые backend-запросы.
4. Первый пункт Event получает фокус без scroll; Escape закрывает меню и возвращает фокус на summary/trigger. Закрытие снаружи, при уходе фокуса Event, scroll/resize. Пункты действий сохраняют прежние обработчики и href.

## До approval выполнено

Приложение использует исходный JS. `node --check` предложенного файла exit0. Предложенные JS bytes внедрялись только через response routing в собственном браузере, SHA совпадает с manifest. [SIMULATED prototype v2-r3](native-menu-prototype-v2-r3.js.result.json):20PASS/0FAIL —12геометрических проверок Place/Event×390/1024×первая/последняя строка, включая readiness, плюс8Escape/focus. Это feasibility, не postpatch GREEN или полная приёмка.

Предыдущие попытки retained: v1 locator оставался привязан к строке после portal; v1-r2/v2 полностраничный screenshot менял состояние перед Escape. При viewport PNG с тем же JS и теми же assertions20PASS. Все исходные FAIL/результаты/PNG сохранены, они не выдаются за GREEN.

## После approval

- Сверить свежие path/HEAD/branch/dirty/active_run, SHA JS и текущего CSS. Применить только exact JS diff; сохранить чужие байты. Запустить только собственный подтверждённый профиль с новой фиксацией source/3MO.
- Повторить targeted native меню Place/Event на RU/AZ/EN×360/390/768/1024/1280/1440, раскрытый/свёрнутый sidebar, первая/последняя строка, локальная прокрутка к actions. На mobile overlay не взаимодействовать с фоном до закрытия overlay.
- Проверить click и keyboard Enter/Tab/Escape/focus, выход фокуса, outside click, scroll/resize, закрытие/повторное открытие, восстановление того же panel/style и отсутствие оставшихся body panels. Popup PNG снимать без изменения viewport, отдельно проверять поведение на resize.
- Убедиться, что readiness, сортировка, фильтры и поддерживаемые переключения колонок работают; проверить безопасные href/disabled actions без domain writes. Функциональные failures поиска/sort из текущего отчёта не считать закрытыми этим JS-патчем.
- Проверить console/network, неизменность синтетических данных, исходники фактического процесса, PNG hashes, preservation с честной NOT VERIFIED границей8утраченных HTTP процессов. Повторять полный модуль08 только после всех его задач; уже прошедшую1121CSS матрицу целиком без новой причины не повторять.
- Новый scope/причина — отдельно согласовать. MOD-QA-03 не закрывать до фактического выполнения его acceptance. MOD04/module09/production/commit/push/deploy сюда не входят.

Approval нужен именно на этот дополнительный JS-файл: первоначальный approved scope разрешал только27строк CSS и требовал отдельно согласовать JS/portal при обнаружении новой причины.

Уточнение baseline replay:5PASS/5FAIL/**2NOTRUN**, все5идентичностей FAIL совпадают с actual-source menu run7PASS/5FAIL. Два prepatch readiness control завершились timeout; они не объявлены PASS. Первый metadata gate ошибочно требовал7controlPASS и для replay; retained в verification-gate-r1.json, проверка исправлена на точные raw counts без изменения browser assertions.
