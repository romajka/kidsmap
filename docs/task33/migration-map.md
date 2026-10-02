# KidsMap №33 — карта совместимого переноса

Этот файл описывает TO-BE правила. Применение переноса ещё не выполнялось; производственные агрегаты неизвестны.

| Источник | Цель | Сохраняется | Основание / ручная сверка |
|---|---|---|---|
| Place | тот же Place; optional Org | PK, URLs, owner, creator, photos, favorites, reviews | сеть только по подтверждённой связи; имя недостаточно |
| Place category/age/class text | Activity/Group либо general Place data | исходное значение и provenance | группировка только по явному соответствию; mixed legacy остаётся совместимым |
| PricingPlan | тот же PK, Place XOR Group target | currency, age, units, fees, conditions, staff verification | не один Group на каждый plan; unsupported combination manual_review |
| Legacy scalar/JSON price | existing fallback либо mapped plan | raw source, rule/fingerprint | no inferred product type/from-price; untouched fallback не очищать |
| OwnerTeamMembership | тот же Place scope | valid explicit access | null-place не активировать; owner FK не all_network |
| VolunteerPlaceRevision | versioned proposal adapter | payload/base/status/author/moderation | stale/schema mismatch на сверку, не auto apply |
| PlaceReview duplicates | typed head + revisions + legacy archive | every PK/text/moderation/reaction | latest approved known account; unknown separate |
| SpecialistReview | тот же typed head + baseline/candidate versions | PK/links/source text | approved visible until candidate approval |
| PlaceReviewReaction | исходный PK + original revision FK | actor identity/values | не суммировать sibling version reactions |
| Specialist PracticeLocation | history/confirmed employment отдельно | old location periods и old links | place_id не bilateral confirmation; online не delete history |
| Event | тот же Event + organizer/snapshots | PK, real dates, address, history | unknown organizer/location manual_review; не past address из текущего Place |
| Existing slug/URL | same URL или explicit same-language redirect | existing incoming links | не redirect самостоятельную historical page только ради единообразия |
| Private/public documents | private storage + gated certificate visibility | files/provenance/approved state | actual production move отдельное release поручение |

## Mapping record

source_type, source_id, rule_version, piece_key, target_type, target_id, source_version/fingerprint, state, reason_code, run/checkpoint. Уникальность по source_type/source_id/rule_version/piece_key. Несколько частей одного source именованы явно. Не сохранять user-level payloads/секреты в Git отчётах.

## Dry-run и apply

Dry-run не вызывает save/signals и не пишет metadata в рабочие данные. Вывод: aggregates, manual_review причины, ожидаемые изменения. Apply только в disposable/local pilot DB в этапах 11/23/28; target changes и checkpoint atomic, source lock/recheck before apply, resumable rerun.

## Сверка

IDs/URLs, tariffs/source scopes, permission sets, moderation versions, review contributions, version reactions, media/favorites/history. Сравнить prior/new rating aggregates до включения. Личные записи не выгружать в отчёт.

## Откат

Feature disable не удаляет новое. Совместимый binary должен читать новые записи. Новые post-switch records проверяются в recovery rehearsal. Не reverse schema после новых writes без доказанного back-conversion; не восстанавливать старый dump поверх нового под видом успешного отката.

## Stage 11 — operational pilot mapping (LOCAL WORKTREE)

`convert_task33_catalog --dry-run --plan /tmp/task33-plan.json` builds a deterministic, versioned plan inside a PostgreSQL read-only transaction. It does not create `ConversionRun`/`ConversionMapping`, save models, emit signals, or modify source metadata. The file contains source IDs, versions, SHA-256 fingerprints, target IDs and reason codes; keep it outside Git. A pre-existing plan file is never overwritten. `--apply --plan ... --batch-size 1..500 [--max-batches N]` is restricted to `DJANGO_TESTING=1` isolated settings. The command does not connect to production in stage 11.

| source_type | piece_key | target | reason_code / treatment |
|---|---|---|---|
| `place` | `identity` | same `Place.pk` | `same_place_id`: retain place, slug/URLs, owner, media, favorites and reviews |
| `place` | `organization` | none | `organization_unconfirmed`: manual review; no name-based network assignment |
| `place` | `legacy_pricing` | none | `legacy_price_requires_classification`: manual review when scalar/JSON price exists without a direct relational plan; old price remains readable |
| `pricing_plan` | `identity` | same `PricingPlan.pk` | `same_plan_id`: preserve existing tariff and target scope |
| `pricing_plan` | `group_assignment` | none | `group_unconfirmed`: manual review for direct plans; no group inferred from tariff text |

All pieces use unique `(source_type, source_id, rule_version, piece_key)`. `ConversionRun` stores plan digest, aggregate baseline, entry count and committed checkpoint; `ConversionMapping` stores fingerprint/version, target, state, reason and run. Each small batch locks run and source rows, compares the full concrete-row fingerprint, writes mapping and checkpoint in one transaction. Changed/missing sources become `changed_source` manual review; a stale run cannot replace a newer mapping. Repeating or resuming the same plan does not create duplicate mappings. Manual pieces do not stop the rest of the catalog.

Reconciliation reports only counts of Place, PricingPlan, PlacePhoto, PlaceLike, PlaceReview and PlaceReviewReaction, mapping states/reasons and checkpoint. A count mismatch means another write occurred after planning and requires a fresh plan/review; it is not silently accepted as a complete source inventory. This conservative first rule version does **not** transform legacy price JSON/scalars, merge reviews, assign organizations/groups/venues, or move media. Those remain on compatible old paths pending verified per-record decisions in later authorized stages; source values are never cleared here. Actual production data and production aggregates remain UNKNOWN.
