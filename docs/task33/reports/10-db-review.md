# Этап 10 — независимая проверка БД и совместимости

Роль: `database-reviewer` (`.agents/agents/database-reviewer/agent.md`), исполнитель `/root/stage10_db_review`, режим AUDIT. Авторизация: stage10 APPROVED IMPLEMENT у lead; этот исполнитель менял только данный отчёт. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e`; проверен dirty WORKTREE этапа 10. PRODUCTION UNKNOWN, подключений к нему не было. Исходные изменения lead сохранены в `/tmp/kidsmap-task33-stage10-20260930-080319Z` (сообщение lead); самостоятельно содержимое snapshot не копировал.

## Вывод

Проверены модель, миграция 0123, writer, сигналы, scalar fallback, v1/v2 JSON и CSV. После расширения candidate-flow был выявлен P1 и исправлен lead. Финальный независимый targeted и SHA-сверка подтвердили исправление; открытых P0/P1/P2 в проверенной области нет. Ранее найденные несоответствия были исправлены:

- SEO сначала читал только direct `Place.pricing_plan_records`; теперь `services/seo.py:place_pricing_records` учитывает опубликованные группы, исключает бесплатное пробное из основного Offer и описывает период/обязательную доплату.
- Архивация Activity/OfferingGroup и publication `_apply()` обходили post_save signals, оставляя устаревшую scalar цену. Теперь `ArchivedEntity.archive()` синхронизирует projection атомарно, `_apply()` синхронизирует после status/archive update.
- Writer блокировал лишь существующие plan rows: пустая цель допускала конкурентное объединение двух замен. Теперь блокирует owning Place, затем OfferingGroup до чтения rows.
- JSON/UI validator не проверял возраст на реальной группе до HTTP 200. Теперь вызывает `PricingPlan.full_clean()` с group. Возрастные изменения OfferingGroup проверяются через `validate_group_plan_ages` в model.save и publication `_apply()`.

## Найденный и закрытый finding

- **DB10-01 / P1 → CLOSED / dirty WORKTREE / высокий confidence**: до исправления повторное открытие admin формы с pending `nested_pricing` и сохранение другого поля стирало ожидающий одобрения тариф без изменения живой записи. Причина была в том, что `publication_forms.save_form()` строил полный `snapshot(candidate)`, а `candidate_from_payload()` восстанавливал только direct `pricing_plans` и `PlaceAdminForm.__init__` не задавал initial hidden `nested_pricing`. В `publication.propose()` live nested tree переписывает pending и отфильтровывается как равный base. Trigger: import v2 90→100 как draft/pending, повторное сохранение формы, затем approval; 100 теряется. Owner: django-reviewer; acceptance: pending остаётся 100 после unrelated save, live остаётся 90 до approval, затем становится 100 при approval. Исправление в текущем source: `candidate_from_payload` сохраняет pending nested, admin form задаёт hidden initial, `save_form` переносит pending nested при пустом поле. Source сверка и независимый isolated regression test выполнены; `test_pending_nested_tariff_survives_reopening_and_other_draft_save` проверяет hidden initial, сохранение candidate 100 и live 90 до approval. SHA до/после независимого прогона совпали.

## Evidence

- `src/catalog/migrations/0123_task33_group_pricing.py`: nullable Place FK, nullable OfferingGroup FK, `pricing_exactly_one_target`, индекс групп. Существующие direct rows остаются с Place; migration не выполняет data rewrite.
- `src/catalog/models/pricing_plan.py:PricingPlan.clean/save/target_place_id`: XOR на уровне модели, resolver group→activity→place, age intersection; signal direct/group projection.
- `src/catalog/services/pricing_plans.py:replace_target_pricing_plans`: target-scoped ID/fingerprint/omission/delete, parent locks. `validate_nested_pricing` требует schema version 2, проверяет group ownership и ID; `serialize_nested_pricing` сохраняет дерево Activity→OfferingGroup→plans. `place_pricing_records` выбирает только опубликованные неархивные группы для public; `build_public_price_summary` сохраняет scalar-only fallback и исключает trial/required fees из regular headline.
- `src/catalog/models/place.py:pricing_plans`: v1 editor видит direct rows; grouped rows не подменяются legacy JSON. `src/catalog/domain_admin/place.py:validate_pricing_import_view/export_place_json_view/save_model`: v1 direct, явный `nested_pricing` v2, scoped replacement. `static/admin/js/kidsmap_place_json_import.js` передаёт nested payload в форму. CSV `src/catalog/management/commands/import_places.py` не пишет nested plans.
- `src/catalog/models/catalog_structure.py:ArchivedEntity.archive/OfferingGroup.save`, `src/catalog/services/publication.py:snapshot/_validate_patch/propose/review/_apply`, `src/catalog/services/publication_forms.py:save_form`, `src/catalog/services/volunteer_places.py:candidate_from_payload` и `src/catalog/services/seo.py:build_place_seo_payload` проверены после исправлений. `nested_pricing` остаётся в candidate до approval; `propose` не включает его в immediate writes.
- `src/catalog/services/pricing_plans.py:prefetch_place_pricing_records` использует один query direct+published nonarchived group с `select_related` и раскладывает строки по owning Place; map (`controllers/place_controller.py:_serialize_map_places`), suggestions (`views.py:catalog_search_suggestions`) и SEO landing aggregates вызывают batch reader. Source parity с одиночным `place_pricing_records` проверена; benchmark/EXPLAIN не выполнялись.
- Codebase Memory project `home-ramin-kidsmap`, root `/home/ramin/kidsmap`, index ready, 14684 nodes / 52982 edges, best-effort coverage `no_recorded_issue` на pricing model/service/migration/admin/JS. Выводы сверены с actual dirty source; graph не принят за доказательство deployed state.

## Проверки

Финальная независимая команда: `python3 docs/task33/qa04/run.py --mode all --label catalog.testcases.test_task33_pricing --output /tmp/task33-stage10-db-review-final15-20260930-0930`. Exit 0; **15 tests, 0 failures/errors/skips**; Django check и makemigrations check PASS. Одноразовая PostgreSQL: `network=none`, ports none, data tmpfs, checkout не монтировался, cleanup PASS; `run_root_removed=true`, `socket_root_removed=true`. Покрыты DB XOR, target IDs/stable IDs, scoped omission, age/currency/modes, scalar-only, save/delete/archive/publication signals, JSON/UI v1/v2, pending nested candidate, CSV isolation, SEO/detail/card, concurrency empty target. Batch reader сверялся по source; отдельного equivalence test нет. `git diff --check` exit 0.

Хеши 10 ключевых source artifacts до и после этого теста совпали: `pricing_plan.py=a1850607`, `catalog_structure.py=6baf0721`, `pricing_plans.py=bbe99d2d`, `publication.py=6ba89aca`, `publication_forms.py=92098555`, `volunteer_places.py=fd4f3fa6`, `seo.py=50030797`, `domain_admin/place.py=07319629`, `test_task33_pricing.py=389ec96c`, migration0123=`27217003` (sha256, первые 8 символов; полный manifest lead). LOCAL HEAD остался `c52b871ce5c18656a9eaf9854e66255c2629364e`. Все 10 reviewed SHA совпали с actual WORKTREE и `docs/task33/reports/10-source-manifest.json` (25 stage10 artifacts; cross-check 10/10 MATCH).

Промежуточные независимые прогоны: `/tmp/task33-stage10-db-review-20260930-0840` 8/8 PASS; `/tmp/task33-stage10-db-review-final-20260930-0845` 11/11 PASS, оба cleanup PASS. Они не заменяют финальный 15-test результат.

NOT RUN этим reviewer: полный suite, migration rollback, production schema/data/EXPLAIN, rendered browser, external integrations, deployment. Lead выполняет полный suite и browser QA отдельно; их результаты этим отчётом не приписываются reviewer.

## Остаточные ограничения и handoff

Прямые `QuerySet.update()` вне проверенных lifecycle путей обходят Django model validation/signals; новым writer и publication/admin flow пользоваться через service. Межтабличное age intersection не выражено PostgreSQL CHECK, поэтому защиту дают application entrypoints; raw SQL и непроверенные сторонние writers не охвачены. Production migration state/legacy aggregates остаются UNKNOWN. Этап 11 и production этим review не запускались.

Следующий: `django-reviewer` lead — сверить окончательный SHA после browser/full QA, сохранить manifest и закрыть `reports/10.md`/журнал по критериям. `integration-reviewer` — только если lead обнаружит новые regressions в полном suite.
