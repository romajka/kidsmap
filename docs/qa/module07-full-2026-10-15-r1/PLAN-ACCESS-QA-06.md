# PLAN ACCESS-QA-06 — сохранить точную фразу при обработке формы

Статус: **OPEN, реализация не одобрена и не выполнена**. Это новый finding полной ACCEPT-07, отдельный от исправленных переводов ACCESS-QA-05.

Путь плана: `/home/ramin/kidsmap/docs/qa/module07-full-2026-10-15-r1/PLAN-ACCESS-QA-06.md`.

## Баг и подтверждение

Обычный пользователь вводит правильный код из собственного письма и показанную фразу с дополнительными пробелами по краям. Форма молча обрезает пробелы и отключает аккаунт. Ожидается400 с ошибкой точной фразы и сохранение активного аккаунта.

Подсказка `account_deletion_confirm.html:33` требует точного ввода, включая пробелы/регистр. Сервис `account_deletion.py:421` сравнивает строку буквально; существующий `test_confirmation_phrase_rejects_leading_or_trailing_whitespace` уже закрепляет этот контракт. Однако `AccountDeletionConfirmForm.typed_confirmation` в `forms.py:904` использует default strip=True, а view передаёт cleaned_data вместо исходной строки. Граница HTTP обходит строгую проверку сервиса.

Свежие [native36observations](whitespace-recheck-r2.js.result.json):30control PASS /6source FAIL, RU/AZ/EN ×390/1440. Шесть отдельных аккаунтов реально зарегистрированы и подтверждены через собственные локальные письма. Browser отправляет неповреждённую строку с лишними пробелами (wire_equals_raw=true); ответ302, SCHEDULED, account inactive. Другой неверный текст отклоняется400. [Form proof](whitespace-form-proof.json) показывает strip=True и raw≠exact → cleaned=exact. PNG before/result не содержат рабочих кодов/токенов.

[Предложенные regression tests](access06_proposed_tests.py) уже запущены в отдельной собственной test DB:4метода,24ожидаемых subtest FAIL,0ERROR; два положительных метода работают. Ошибка воспроизводится для leading/trailing/both/NBSP в трёх языках. [Exit/output](access06-proposed-RED.status.json). Никакие existing assertions не ослаблялись.

P3: нарушен существующий контракт дополнительного подтверждения. Авторизация и правильный email-код всё равно обязательны; доступ к чужому аккаунту/утечка этим не подтверждены.

Параметр сверен через Context7 с [официальной документацией Django6.0](https://docs.djangoproject.com/en/6.0/ref/forms/fields/#django.forms.CharField.strip): default strip=True удаляет крайние пробелы; выбор strip=False не отменяет отдельные required/max_length validators. Runtime Django6.0.2.

## Точные application-файлы и diff

1. `src/catalog/forms.py`: **единственная строка** `strip=False` у `AccountDeletionConfirmForm.typed_confirmation`.
2. Новый `src/catalog/testcases/test_access_qa06_deletion_phrase.py`:4метода из [готового файла](proposed-test_access_qa06_deletion_phrase.py). Тело совпадает с наблюдавшимся RED-прототипом, отличается только docstring. Проверяются сохранение raw input, HTTP-отказ padded phrase без расхода кода/деактивации, прежний отказ неверного кода и успех точной фразы с завершением сессии.

[Полный готовый diff](proposed-ACCESS-QA-06.diff), `git apply --check` exit0. [SHA исходника/diff и отсутствие нового app-файла](access06-plan-source.json). Diff не применён. Existing dirty изменения forms.py и ранее одобренные PO сохраняются. Не менять сервис/словарь фраз, сообщения/PO/MO, session/retention policy, views/templates/JS/CSS, CI/schema и existing tests.

## После отдельного одобрения

1. Зафиксировать новый unique fix-run и snapshot; проверить SHA плана, точный context и исходный forms.py. Применить только показанный diff. Снятие одной строки должно возвращать entry-байты forms.py; остальные файлы/старые отчёты сохраняются.
2. Новый собственный DJANGO_TESTING=1 профиль PG/DB/cache/media/private-media/email, чистый env без .env/production credentials. Учесть текущие pinned dependencies, включая pypdf==6.20.1, в собственном каталоге, без изменения shared .venv. Только явно SIMULATED TEST_POLICY; app default inactive policy не включать. Внешние интеграции отключены.
3. Свежие RU/AZ/EN PO → собственные MO через scripts/build_isolated_locales.py, verify manifest и sole LOCALE_PATHS до setup. Показать source/PID/argv/cwd/template/dependency origins и actual opened own MO.
4. Запустить **те же4метода без изменения expected** —24RED должны стать GREEN; запускать копию из нового app test-file. Плюс прежние7целевых deletion методов ACCESS05: сервисная strict phrase, whitespace, session invalidation, cancel/reset requirement, private status/foreign-user boundaries. Существующие assertions не менять. Новый код поля не затрагивает другие формы.
5. Реальный браузер RU/AZ/EN ×360/390/768/1024/1280/1440: свои native signup/verification или initial fictional verified fixture; deletion request и код только из своего локального письма. С валидным кодом проверить leading/trailing/both/NBSP:400/typed_confirmation error, raw input сохранён, account active/CONFIRMATION_SENT, код не израсходован. Затем неверный код при точной фразе остаётся400/code error; корректный код + ровно показанная фраза дают302/SCHEDULED, account inactive, старые сессии недоступны. Проверить Tab/Shift+Tab/Enter, ошибки RU/AZ/EN, console/network, геометрию и PNG mobile/desktop.
6. Рабочий код/письмо/status token не включать в артефакты. До PNG подтвердить сохранение значения приватно, затем очистить поле пользовательским действием или маскировать только поле кода нативной screenshot mask. Не менять DOM/CSS ради результатов.
7. После целевых GREEN — новая сводная ACCEPT-07 с source provenance: существующий полный корпус уже выполнен один раз;338неизменённых методов повторно целиком не гонять. Переоценить только затронутую границу формы и новые4метода, связать retained module evidence по hashes, закрыть06 только после фактической проверки. Если выявится иная причина/понадобятся дополнительные application-файлы — отдельный план/одобрение.

## Риски / остановки

Исправление делает web-путь таким же строгим, как текущий сервис: пользователю придётся убрать лишние крайние пробелы. Внутренние пробелы, регистр и все символы фразы не нормализуются. Required/max_length и обработка кода остаются. Не массово отключать strip у других полей. Не обрезать raw input в новых tests ради GREEN.

Текущий scope одобрения относится только к ACCESS05/four PO entries. По пользовательскому правилу и AGENTS новый forms.py scope требует отдельного одобрения. Без commit/push/deploy/production/reset/clean/stash/active_run assignment. Module08 автоматически не начинать.
