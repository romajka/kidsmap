# PLACE-QA-08 — RU placeholder района остаётся на AZ

Alias существующего **CROSS-QA-03**, одна причина, не новый дублирующий тикет. P3: wrong-language подпись пустого поля, без доказанной потери данных или блокировки публикации. Роль owner; URL `http://localhost:8841/ru/account/places/2/edit/`, selector `select#id_district option[value=""]`. Environment — snapshot/runtime REPORT.md, fresh isolated compiled locales, synthetic data.

Шаги: войти вымышленным owner → открыть RU editor → прочитать пустой district option; для видимого состояния native выбрать пустой пункт в отдельном контексте, блокируя non-GET после логина → повторить 360/390/768/1024/1280/1440.

Ожидание: RU «Выберите район». Факт: «Rayon seçin» на всех шести ширинах. [DOM + screenshot references](residual.result.txt), [mobile screenshot](screenshots/residual-ru-district-390.png), [desktop screenshot](screenshots/residual-ru-district-1440.png). Пустой выбор в screenshots — SIMULATED unsaved state; исходный district code baku_yasamal записан, server save/transition не выполнялись.

Подтверждённая первопричина: `src/catalog/services/locations.py:561` использует gettext «Выберите район»; `locale/ru/LC_MESSAGES/django.po:18354` содержит только obsolete `#~ msgid`. Новая RU MO не имеет активного ключа, AZ MO имеет Rayon seçin. [Свежий compiled proof](compiled-locales-proof.json). Пересборка неизменного PO не восстанавливает obsolete entry. Уверенность высокая, regression attribution UNKNOWN: clean-HEAD comparison не выполнялся.

Область исправления: активный RU перевод этого ключа и воспроизводимая локальная сборка; сохранить районные коды, validation, request locale и candidate/live данные. Зависимость — existing isolated-locale helper/launcher для свежего rendered acceptance. Owner handoff: frontend-reviewer + integration-reviewer. [Самостоятельный prompt](PLACE-QA-08-repair.txt). Код не исправлен.
