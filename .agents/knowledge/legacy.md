# Legacy: классификация без удаления

Срез2026-09-06. LOCAL `main`/`df6fef3` + dirty/untracked; PRODUCTION clean `86a0b8c`, `readiness-legacy-migration`, catalog0100. Строки кода ниже — LOCAL. Новые production агрегаты: [E3](../../docs/agent-audits/PRODUCTION_READ_ONLY.md) подтверждает266Place со scalar prices без relational plans,2с nonempty legacy JSON,3с text schedule;0temporary Place/Event/team rows. Пометки UNKNOWN в отдельных строках означают отсутствие полного semantic/retirement доказательства, а не отсутствие этого aggregate audit. Отсутствие примеров в локальной БД не доказывает отсутствие использования.

## Значения статуса

| Статус | Значение |
|---|---|
| ACTIVE | Реальный текущий контракт, включая нужные compatibility entrypoints. |
| LEGACY-IN-USE | Старое представление всё ещё читается/пишется или поддерживает публичное поведение. |
| MIGRATED-BUT-RETAINED | Перенос предусмотрен/выполнен для части данных, исходное представление сохранено; полноту подтверждает БД. |
| DEPRECATED | Есть явное решение не развивать путь; это ещё не разрешение удалить. |
| CANDIDATE-FOR-REMOVAL | Найден аргумент для cleanup, нужны impact analysis, проверки и отдельное разрешение. |
| UNKNOWN | Недостаточно совместных свидетельств кода, миграций, БД и UI. |

## Реестр

| Item | Классификация | Код / миграции | DB usage и риск | Рекомендация |
|---|---|---|---|---|
| `Place.pricing_plans_legacy` / колонка `pricing_plans` | LEGACY-IN-USE | `src/catalog/models/place.py:142`, property `:360`; migration0084 `SeparateDatabaseAndState` | Production occupancy UNKNOWN; property возвращает JSON при отсутствии реляционных тарифов | Считать непустые JSON и связанные планы раздельно; не удалять fallback. |
| Scalar `price_from/to`, `price_per_*` | LEGACY-IN-USE / projection | `models/place.py:156`; `services/pricing_plans.py:345`; signal `models/pricing_plan.py:247` | Читаются публичным фильтром/summary и обновляются из тарифов; occupancy UNKNOWN | Отделить scalar-only от проекции уже мигрированных тарифов. |
| `Place.schedule` | LEGACY-IN-USE | `models/place.py:128`; `services/place_readiness.py:276`; `place_schedule.py:514` | Публичный SQL принимает текст; новая readiness требует дни | Перенос только полностью разобранного текста с проверкой часов. |
| `cover_photo` | LEGACY-IN-USE | `models/place.py:124`; `place_readiness.py:295`, advice `:443` | Используется compatibility проверки и отображения; occupancy UNKNOWN | Сверить main/cover/gallery в public/admin прежде чем менять. |
| `Place.is_temporary`, `temporary_start/end` | ACTIVE, retirement UNKNOWN | `models/place.py:143`; `content_quality.py:273`; `Event` отдельно `models/place.py:698` | Существуют оба пути; количество legacy временных мест UNKNOWN | Не заменять Event и временный Place механически. |
| Null-place team membership/invitation | MIGRATED-BUT-RETAINED | migrations0092/0093; `services/owner_place_use_cases.py:61` | Не даёт прав; неоднозначные владельцы оставлены намеренно, количество UNKNOWN | `report_legacy_team_access`; решение пользователя по конкретной области доступа. |
| Старые UserProfile role/overrides | Удалены в текущей схеме; исторические миграции ACTIVE | migration0097; `models/user.py:19` | Production catalog0100 включает0097; не восстанавливать поля по старым docs | Обновлять знания о правах, сохранять историю миграций. |
| Root `config/*` | ACTIVE compatibility | `config/settings.py:3` → `src.config.settings`; аналогичные wrappers | Точки импорта/запуска; БД неприменима | Не заводить второй источник настроек. |
| `catalog/admin.py` | ACTIVE compatibility | `src/catalog/admin.py:4` импортирует `domain_admin` | Django autodiscovery; БД неприменима | Admin менять в доменных модулях. |
| Owner-named route/import aliases | ACTIVE compatibility | `services/owner_place_use_cases.py:22/:85`; `views.py:737/:752`; `urls.py` | Старые URL и импорты поддерживаются | Сохранять redirects и обратимость URL. |
| Proxy apps users/content/system | UNKNOWN | `src/catalog/proxy_apps/`; icon config `src/config/settings.py:262–280` | Файлы есть, в INSTALLED_APPS обнаружен moderation proxy; dynamic usage требует сверки | Не объявлять dead только по отсутствию в INSTALLED_APPS. |
| Повторные MultipleFileInput/MultipleFileField | CANDIDATE-FOR-REMOVAL | `src/catalog/forms.py:72/:76` и `:353/:362` | Вторые определения затеняют первые; импорты/наследники требуют проверки | Cleanup после isolated tests и разрешения; сейчас не удалять. |
| `AI_HANDOFF.md` | ACTIVE исторический контекст, отдельные утверждения DEPRECATED | Global owner role и старый локальный путь не соответствуют текущим моделям | БД неприменима | Читать вместе с knowledge/source-of-truth.md. |
| Untracked field matrix | UNKNOWN как контракт, подтверждённый documentation drift | `docs/PERMANENT_PLACE_FIELD_MATRIX.md` | Нет price_mode/readiness и 4 режима — опровергаются текущим кодом | Не использовать эти утверждения как AS-IS; актуализировать отдельной задачей. |

## Инструменты перехода

- `src/catalog/management/commands/migrate_pricing_plans.py`: перенос JSON в реляционные PricingPlan; сначала читать флаги и режим записи, не запускать автоматически.
- `migrate_legacy_prices.py`: перенос определённых scalar продуктов; диапазон без вида продукта неоднозначен. Сам текст help не заменяет проверку signals/побочных записей.
- `migrate_legacy_schedules.py:32`: по умолчанию план; `--apply` включает изменения. Неизвестные строки остаются для ручного решения, старый текст сохраняется.
- `report_legacy_team_access.py`: диагностика непривязанных scopes, не разрешение выдавать доступ всем местам владельца.
- `database_inventory.py`, `migrate_legacy_database.py`, `verify_database_transfer.py`, `cleanup_migration_junk.py`: разные назначения; наличие слова audit/migration не гарантирует read-only. Перед запуском проверять handle, SQL и флаги.
- `src/config/settings.py:379` содержит опциональную legacy database alias; наличие alias не доказывает наличие/доступность второй БД в production.

## Правила принятия решения

1. Сначала установить конкретную версию кода и migration state. LOCAL dirty feature нельзя считать deployed feature.
2. Найти прямые и динамические чтения/записи, serializers, templates, admin actions, signals, management commands, redirects.
3. В PostgreSQL read-only сверить occupancy, отношения, дубли/orphans, JSON shape, constraints и частичность миграции. В отчёт только агрегаты без пользовательских данных.
4. Проверить публичное и административное поведение отдельно; совместимость live карточек может быть намеренной.
5. Отметить confidence и unknowns. «Graph не видит» и «назван legacy» недостаточно.
6. Предложение добавить в `cleanup-candidates.md`; не удалять исходники, migration history, данные, media или aliases в аудитном запуске.

## Известные расхождения, не cleanup

LOCAL owner wizard `forms.py:1469` использует untracked `permanent_place_rules.py`; admin — tracked `place_readiness.py`. Это интеграционный дефект/незавершённая работа, а не повод выбрать один файл и удалить другой без плана. Google OAuth и migration0101 также находятся в LOCAL untracked изменениях и не должны смешиваться с catalog0100 production.
