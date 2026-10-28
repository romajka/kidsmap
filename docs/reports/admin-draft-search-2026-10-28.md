# Поиск сохранённых черновиков — 28.10.2026

Режим: APPROVED IMPLEMENT, локальное исправление по прямому поручению пользователя. Исходный LOCAL HEAD: `e7bd719f`, исходное дерево чистое. PRODUCTION в этом исправлении не изменялся и не проверялся.

## Исправление

- `PlaceAdmin.get_search_results` сохраняет обычный поиск и исходные фильтры и дополнительно ищет эффективные названия AZ/RU/EN, адрес, телефоны и Instagram в активных `draft/pending/rejected` версиях. Отсутствующий ключ берётся из Place, явно очищенное поле не восстанавливается из основной версии.
- Совпадения по сохранённой версии проходят `has_change_permission` и существующий `publication.authorize`. Произвольные JSON-поля и служебные заметки не участвуют в поиске.
- Выпадающие подсказки используют ту же логику и показывают сохранённые сведения только авторизованному редактору.
- Поиск личных ServerDraft проверяет все три названия, адрес и контакты. Сохранён охват строго текущего автора; совпадение личной копии существующей карточки сохраняет её в результатах общего поиска.
- Схема, миграции, публикация и основные значения Place не менялись.

## Проверки

Добавлены 18 регрессионных тестов в `src/catalog/testcases/test_admin_draft_search.py`. До исправления воспроизведены пропуски адреса, телефонов, локализованных названий, связанной личной копии и подсказок. Проверены фразы в кавычках, сочетания слов, статусы версий, исходные фильтры, отзыв доступа, права только просмотра, закрытые копии другого автора и отсутствие записи в Place/revision при поиске.

Команда итогового прогона:

```sh
python3 .tmp/admin-draft-search-20261028/run_full.py \
  catalog.testcases.test_admin_draft_search \
  catalog.testcases.test_addition_editor_regressions \
  catalog.testcases.test_admin_saved_readiness \
  catalog.testcases.test_place_draft_media.DraftMediaTests \
  catalog.testcases.admin.TestAdminOwnershipModerationUX.test_admin_place_search_suggestions_returns_matching_places \
  catalog.testcases.admin.TestAdminOwnershipModerationUX.test_search_suggestions_do_not_reuse_the_previous_places_owner
```

PASS: 63 теста, 0 ошибок, 0 падений. Код выхода 0. Лог: `.tmp/admin-draft-search-20261028/regression-full.log`.

Профиль очищает наследованное окружение, устанавливает DJANGO_TESTING=1, использует SQLite в памяти, временные media/private/static, LocMem cache/email и блокирует сетевые подключения. Итоговый запуск применяет полный граф миграций. Первоначальный schema-only прогон существующих тестов имел ошибки из-за отсутствующих данных миграций; в итоговом профиле они устранены без изменения утверждений старых тестов.

PASS: `git diff --check`.

Дополнительный release-preflight: те же 63 теста прошли на отдельном PostgreSQL 17, 0 ошибок/падений/пропусков; `scripts/run_isolated_quality.py` с теми же labels, отдельными `--profile-root` и `--socket-dir`, очищенным окружением и network-disabled контейнером. JSON-отчёт подтверждает complete=true и successful=true. Django check и проверка отсутствия миграционного дрейфа прошли.

NOT RUN на момент коммита: отрендеренный браузер, нагрузочные измерения, production, развёртывание. Модель данных и публичный поиск не менялись. Блокировку контентной автоматизации и её журналы не менял: для снятия блока нужна отдельная проверка после развёртывания.
