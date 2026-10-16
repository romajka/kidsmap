# PLAN ACCESS-QA-05 — четыре перевода ошибок удаления

Статус: PLAN готов; ACCESS-QA-05 OPEN; реализация требует отдельного одобрения этого scope.
Фактический путь: `/home/ramin/kidsmap/docs/qa/access-qa05-recheck-2026-10-15-r1/IMPLEMENTATION_PLAN.md`.

## Подтверждённая причина

На текущем dirty WORKTREE, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`, active_run NONE: две ошибки в AZ и EN остаются русскими. Свежие изолированные MO, runtime gettext и настоящий Chromium подтверждают это на 18 сочетаниях RU/AZ/EN ×360/390/768/1024/1280/1440. 24 языковых FAIL относятся только к ACCESS-QA-05; 228 проверок формы/отказа/клавиатуры/геометрии PASS. Exact-wording oracle: 8 ожидаемых RED (runtime + MO).

В четырёх PO-записях стоит fuzzy. Перевод фразы ошибочно говорит «код отправлен», перевод неверного кода — «ввести код». GNU msgfmt исключает fuzzy, runtime возвращает русский msgid. `views._account_deletion_error_message` используется и подтверждением, и отменой удаления; код неверного подтверждения — общий потребитель. Порядок проверки exact phrase → code, счётчик попыток и запрет деактивации при ошибке работают.

## Единственные application-файлы

| Файл | Точная область |
|---|---|
| `locale/az/LC_MESSAGES/django.po` | msgid «Введите фразу подтверждения точно так, как она показана.» и «Неверный код подтверждения.»; нынешние строки17791/17797 |
| `locale/en/LC_MESSAGES/django.po` | те же два msgid; нынешние строки17683/17689 |

Точный review-only diff: [proposed.diff](proposed.diff). Он ещё не применён. Удалить fuzzy и устаревший previous-msgid только у этих четырёх записей; заменить только их msgstr:

| Ошибка | AZ | EN |
|---|---|---|
| Неверный код | Yanlış təsdiq kodu. | Invalid confirmation code. |
| Неточная фраза | Təsdiq ifadəsini göstərildiyi kimi dəqiq daxil edin. | Enter the confirmation phrase exactly as shown. |

Остальные записи, включая соседние fuzzy, сохраняются побайтно. RU PO, shared MO, Python/HTML/JS/CSS, schema, CI, existing assertions и production configuration вне scope. Нет inline overrides, массового удаления fuzzy или обновления всех ссылок PO. Existing dirty изменения обоих PO сохраняются. Возврат при необходимости — только четырёх записей к entry-байтам, без reset/clean/stash.

## Реализация и целевая проверка после одобрения

1. Проверить SHA плана/diff и четыре исходных блока, применить только [proposed.diff](proposed.diff), проверить, что обратный diff возвращает entry-хеши обоих PO. При drift остановиться и пересогласовать существенное изменение.
2. Новый уникальный fix-run/изолированный профиль: DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/filebased email; вымышленные пользователи. Чистое окружение, без checkout .env; egress запрещён. TEST_POLICY только SIMULATED в собственном QA settings; default inactive policy приложения не менять. Письма, реальные коды и signed status tokens остаются только в закрытом ignored scratch; не помещать их в отчёт, PNG, CLI transcript или public artifacts.
3. Собрать текущие RU/AZ/EN через `scripts/build_isolated_locales.py build --output .tmp/<новый-fix-run>/locales --locales ru az en --compiler native`; verify manifest. Единственный LOCALE_PATHS до django.setup. Подтвердить PID/argv/cwd, импортированные views/service, template SHA и реальные открытые MO. Проверить точное содержимое четырёх переводов в runtime и MO: прежний oracle должен стать 8/8 GREEN без изменения expected. RU сохранить.
4. Настоящий браузер: RU/AZ/EN ×6 ширин, собственные отдельные пользователи/запросы без обхода TTL/attempt guards. Request → локальное письмо с проверкой recipient и code-hash → неверный код при точной фразе → неточная фраза → исправление полей → подтверждение; отдельные/продолженные пользовательские переходы отмены. Проверить поле ошибки, смысл и точный язык, сохранение введённых значений, Tab/Shift+Tab/Enter и доступность элементов, console/network. В конце read-only DB подтверждает деактивацию только после корректного ввода и отмену только по собственному локальному коду. На UI-кнопке Cancel перед подтверждением также проверить возврат к settings без деактивации. Верный код не фотографировать; для кадров обеих ошибок использовать заведомо неверное тестовое значение (phrase проверяется раньше code). Status URL с token не сохранять в public diagnostics.
5. Общий затронутый сценарий: неверный код при отмене удаления на AZ/EN, затем исправление и успешная отмена на RU/AZ/EN mobile/desktop. Проверить, что доступ восстановлен с требованием reset password, old code не подходит повторно, старые сессии не восстановлены; требования exact phrase/retention policy не менялись. Это целевая проверка общего msgid, не повтор всех auth suites.
6. Существующие тесты без изменений assertions: `catalog.testcases.test_account_deletion.AccountDeletionWorkflowTests.test_confirmation_requires_exact_phrase_and_valid_code`, `test_confirmation_phrase_rejects_leading_or_trailing_whitespace`, `test_confirmation_invalidates_all_existing_sessions`, `test_cancel_before_deadline_restores_access_but_requires_password_reset` (все под тем же полным class prefix); `catalog.testcases.test_account_deletion.AccountDeletionWebTests.test_request_and_double_confirmation_sign_out_to_private_status`, `test_anonymous_and_other_user_cannot_access_confirmation`, `test_status_requires_a_valid_signed_token` (также полный class prefix). Запуск через собственный cleared-env runtime test и отдельную test DB. Семь targeted методов, без неизменившихся полных наборов. Семантическая локализация дополнительно проверяется точным oracle и browser; HTTP400/exit0 сами по себе не GREEN.
7. Отчёт fix-run: команды/exits/counts, RED→GREEN, PNG manifest, snapshot/source/runtime, shared MO/чужой WORKTREE/active_run/stands preservation, NOT RUN. Статус ACCESS05 закрывать только по выполненным проверкам. ACCEPT-07 — отдельный один полный прогон после всех задач; этот план его не заменяет. Module08 не начинать.

## Зависимости и риски

Текущая default retention policy inactive: локальный SIMULATED профиль не доказывает production readiness. Риск — неверный смысл перевода или случайный массовый PO diff; защищают точные четыре блока/ожидаемые строки/inverse hashes. Общий invalid-code msgid затрагивает отмену, поэтому её проверить целево. Все новые причины и существенное расширение application scope требуют отдельного одобрения. Коммит/push/deploy/production запрещены.

Recheck evidence и границы: [REPORT.md](REPORT.md), [observations.json](observations.json), [locale-regression-red.json](locale-regression-red.json), [readback-final.json](readback-final.json). Текущий запуск выполняет только PLAN; successful confirm/cancel, GREEN и backend suites ещё NOT RUN.
