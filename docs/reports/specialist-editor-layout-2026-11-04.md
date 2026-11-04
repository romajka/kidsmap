# Отдельная страница анкеты специалиста — 4 ноября 2026

LOCAL WORKTREE, HEAD b7659e79. Реализация по прямой просьбе пользователя: освободить место от меню кабинета и вернуть постоянно видимую боковую навигацию анкеты. Другие dirty изменения сохранены. Production, commit/push/deploy не затронуты.

Форма создания, продолжение черновика и редактирование подтверждённого специалиста теперь используют base.html, как permanent_place_form.html. Ссылка «В кабинет» сохранена; обзор, документы и приглашения по-прежнему используют account shell. URL/сохранение/валидация/права не менялись.

На ширине от 1024px слева sticky-колонка300px с единственным индикатором готовности и шестью разделами. Длинные названия переносятся; для низкого окна у колонки доступна внутренняя прокрутка. На меньших экранах блок расположен над формой, навигация свёрнута и открывается клавиатурой/кликом. Выбор раздела закрывает список и переносит фокус к разделу. Desktop-список остаётся открытым. При проверке найдено и исправлено переполнение кнопок сохранения/отправки на RU1024: группа теперь переносится под пояснение.

## Проверки

- RED: обновлённые требования к оболочке дали2 ожидаемых failures в9 Django tests. JS mobile/desktop navigation:2 ожидаемых failures; фокус после закрытия меню:1 ожидаемый failure.
- GREEN:22 Django tests PASS (self-onboarding, onboarding inputs, specialist screens),3.668s. SQLite на собственном стенде: ожидаемое предупреждение W047 о неподдерживаемом nulls-distinct constraint; PostgreSQL constraints в этой визуальной правке не проверялись и не менялись.
- GREEN:15 Node tests PASS (12 owner form +3 documents),1.668s; node --check и scoped git diff --check PASS.
- Chromium: RU/AZ/EN ×390/768/1024/1280/1440 +RU320 =16 состояний. После исправления:0 overflow,0 page errors,0 неожиданных локальных HTTP>=400. Desktop после перехода к контактам sidebar top100px и виден весь список, активен правильный раздел; mobile список закрыт.
- Редактирование подтверждённого владельца:390/1024/1440, HTTP200, документы на месте, один индикатор, нет overflow/account sidebar.
- Реальное сохранение неполного synthetic-черновика → отдельный UUID URL → reload: имя сохранено. Отправка неполной анкеты даёт ожидаемый HTTP400 с ошибками и сохраняет введённые данные. Мобильный переход передаёт focus в km-sec-basic.
- Скриншоты desktop, scrolled1024/1440 и320 просмотрены. Physical devices/Safari/Firefox/production NOT RUN.

Команды:

```bash
.venv/bin/python .tmp/specialist-e2e-20261104/run.py test catalog.testcases.test_specialist_self_onboarding catalog.testcases.test_specialist_onboarding_inputs catalog.testcases.test_task33_specialist_screens --settings=qa_settings --noinput
KIDSMAP_JSDOM=/home/ramin/kidsmap/.tmp/coordinate-location/dom/node_modules/jsdom node --test scripts/tests/specialist_owner_form.test.cjs scripts/tests/specialist_documents.test.cjs
node --check static/js/specialists.js
```

DJANGO_TESTING=1; runner очищает окружение, собственные SQLite/cache/media/filemail, внешние интеграции выключены. Логи, baseline copies, scoped.patch: .tmp/specialist-editor-20261104/. Screenshots: output/playwright/specialist-editor-*.png. Это новый срез поверх предыдущей приёмки specialist-onboarding-fixes; прежний final-source.json намеренно больше не совпадает с изменёнными файлами. Для этой правки отдельный final-source.json.

Собственные browser session и runserver остановлены. Финальная сверка5source hashes: изменений после проверенного среза нет.
