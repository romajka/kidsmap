# Переводы управления разделами — исправлено локально

Пользователь одобрил исправления, исключив мобильную версию админки. SECTIONS-02 исправлен; SECTIONS-01 оставлен без изменений по прямому указанию пользователя. Общая готовность сайта к production этим отчётом не подтверждается.

## Изменения

- `locale/az/LC_MESSAGES/django.po` и `locale/en/LC_MESSAGES/django.po`: 7 новых переводов switches/help/instruction, исправлены 2 fuzzy перевода («Публичное избранное», «В настройки сайта»).
- `locale/ru/LC_MESSAGES/django.po`: 7 явных русских переводов этих строк, чтобы fallback на default AZ не подменял русские подписи после добавления AZ.
- Обновлены 3 соответствующих `.mo` штатным `msgfmt --check-format`.
- Удалена одна устаревшая `#~` запись «Перед отправкой» в AZ и EN: обе исходные `.po` до изменения уже не компилировались из-за её конфликта с действующей записью. Действующий перевод сохранён.
- `src/catalog/testcases/test_public_section_switches.py`: regression test реальной admin response для RU/AZ/EN, проверяет подписи и отсутствие RU fallback в AZ/EN.
- Metadata и все остальные записи переводов сохранены; точные scoped изменения и итоговые hashes в `translation-changes.json`. CSS, шаблоны, permissions, feature flags и бизнес-логика не менялись.

## Проверки

RED: isolated test `PublicSectionSwitchTests.test_admin_section_controls_follow_selected_language` упал на отсутствующих EN/AZ подписях. `/tmp/kidsmap-section-i18n-20261009/red`.

Промежуточный запуск `green` оказался преждевременным и прочитал старые translations — 2 failures; после компиляции выполнены свежие успешные запуски:

```sh
PATH="$PATH:/snap/bin" python3 docs/task33/qa04/run.py --output /tmp/kidsmap-section-i18n-20261009/green-final --label catalog.testcases.test_public_section_switches --label catalog.testcases.events_feature --label catalog.testcases.test_organization_directory --label catalog.testcases.test_task33_public_details
PATH="$PATH:/snap/bin" python3 docs/task33/qa04/run.py --output /tmp/kidsmap-section-i18n-20261009/final-scope --label catalog.testcases.test_public_section_switches
```

29 PASS за 17.430s; финальные текущие 5 PASS за 6.223s. Изолированный PostgreSQL, network none, DJANGO_TESTING=1; production credentials не использовались. Ранее обнаруженное несоответствие старого specialist owner redirect test не менялось и в эти targeted labels не включено; весь проект NOT RUN.

Реальный браузер desktop 1280: RU/AZ/EN поля, инструкции и save labels соответствуют выбранному языку. AZ: выключить организации → Save → reload → public directory 404; включить → Save → directory снова 200. EN и RU: реальный Save/reload, флаги сохраняются. Финально все три раздела включены; favorites false, minimum empty, язык RU — исходные значения. Переполнения desktop нет (scrollWidth 1265 при viewport 1280).

Локальный 8792 перезапущен с обновлёнными `.mo`, сохранены прежние синтетические DB/media/session. Runtime digest `b152b2f0fb6ad3e405f854a90a017337752a227366b31ba80d9f9ba4d152745a`, 2779 source files, все текущие runtime hashes совпадают с WORKTREE. Production/release/commit/push NOT RUN.

Снимки: [AZ](az.jpg), [EN](en.jpg). Evidence: `verification.json`, `translation-changes.json`, `scripts/runtime-source.json`. Локальные изменяемые server log/PID оставлены в `.tmp/place-acceptance-20261009-8792/sections-i18n-*`; исторические acceptance manifests не переписывались.
