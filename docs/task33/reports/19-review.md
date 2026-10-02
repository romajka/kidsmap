# Этап19 — независимая integration review

Исполнитель `/root/stage19_review`, canonical `.agents/agents/integration-reviewer/agent.md`, 2026-10-02. READ-ONLY REVIEW внутри разрешённого stage19 APPROVED IMPLEMENT. Владение: этот отчёт и временные synthetic probes в `/tmp`; application source не менял. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e`; evidence относится к dirty WORKTREE, не HEAD/production. Dependency18 DONE, accepted designs и active_run root/stage19 проверены.

**Результат: final bounded review PASS, independent6 31/31.** Найденные REV19-01/02 закрыты source review и повторными meaningful tests. Решение DONE по всей приёмке принимает lead после browser/смежных checks.

## Проверенные границы

- `catalog_search:matching_groups/apply_offer_matching`: correlated Exists проверяет category/subcategory и возраст на одном published Activity/unarchived Group; несколько групп не дублируют Place. Admission имеет отдельную подтверждённую Place semantics. Unknown legacy/standalone taxonomy не получает ложного category+age mapping, остаётся general/direct discoverable.
- `catalog_search:current_org_q` и `public_presentation:organization_matches`: published/approved/unarchived Org, допустимый affiliation type и обе ownership versions; stale/unpublished Org не даёт чужие branches, published Org без branches имеет direct discovery link.
- `public_presentation:prepare_cards`: fresh batch Place/Org/groups/plans; scoped matched groups/цены; request-local trust flags удаляются в finally. Direct visibility/affiliation resolver сохраняет свежие проверки. Shared home/favorites/catalog/template consumers подключены в actual source.
- `catalog_search:taxonomy_counts/public_filter_options`: категории из реального snapshot Activity учитываются, distinct Place counts сохраняются при нескольких groups. `views:catalog_search_suggestions` потребляет batch presentation и matched age, поддерживает localized URLs. `/new` timeline template теперь использует matched groups/price data и скрывает aggregate возраст при exact filter.

## Findings и закрытие

**REV19-01, P2, LOCAL WORKTREE, price pill leakage — CLOSED.** Q-only English4–6 карточка показывала `30–120 ₼`, включая Drawing8–12; admission-only с пустым matched_offers также оставлял unrelated Group цены. Независимый q probe и lead negative tests воспроизвели дефект. Исправление `prepare_cards` ограничивает cache совпавшими plans для q/offer filters, admission-only оставляет direct Place plans и очищает несовместимые scalars/custom badges. Independent3/4/5 price negatives PASS.

**REV19-02, P2, LOCAL WORKTREE, age/timeline consumer gap — CLOSED.** Source review выявил aggregate Place4–12 age в suggestion JSON при matched English4–6; clients visibly render age (`place_list.html`, `home_map.js`). Custom `/new` timeline также обходил matched groups. Lead исправил consumers; independent5 включает canonical suggestion-age/timeline tests и собственный endpoint probe: совпавший age4–6, aggregate4–12 отсутствует. Собственный RED endpoint для этого finding не заявляется; lead consumers RED evidence имеет отдельную attribution.

**Schema boundary сохранена:** Activity не имеет category/subcategory FK; Program имеет category, `approved_program_data` копирует только category_id. Standalone без approved taxonomy snapshot и subcategory без подтверждённого mapping исключаются из соответствующего exact filter. Synthetic mapped-subcategory test проверяет reader, не наличие нового owner/admin mapping writer. Новую schema/authoring область stage19 review не добавлял. Консервативное exclusion соответствует отсутствию подтверждённого mapping; полноту authoring всех taxonomy cases не заявляем.

Codebase Memory `list_projects/index_status/get_architecture` callable и выполнены; root совпадает, index ready. Freshness текущих edits UNKNOWN, templates parse_partial; критические выводы перепроверены actual source. Graph absence не используется как доказательство.

## Exact checks

Все команды из `/home/ramin/kidsmap`, одинаковая форма с указанным output:

```bash
./.venv/bin/python /tmp/task33-stage19-review-run.py --mode all --label catalog.testcases.test_task33_search --output /tmp/kidsmap-task33-stage19-independent5
```

Temporary runner — QA04 launcher с original ROOT/HERE и import `/tmp/task33-stage19-review-probes.py`: добавляет synthetic methods к canonical TestCase. Clean settings, disposable PostgreSQL17/network none/tmpfs, DJANGO_TESTING=1, separate cache/media/locmem email, production credentials absent. QA04 safety/transport guards/discovery/container ownership и cleanup не ослаблены.

| Output `/tmp/kidsmap-task33-stage19-` | Exit | Tests | Результат |
|---|---:|---:|---|
| independent1 | 2 | safety7 | OS socket PermissionError до DB; ENVIRONMENT_FAILURE, scratch removed |
| independent2 | 6 | 19 | 5F1E: real price failures; lead301 route fixture; мой invalid PARK fixture assertion+teardown FK error, исправлен на existing EDU |
| independent3 | 1 | 22 | 21PASS/1F: только lead301 route fixture; все6 private probes PASS |
| independent4 | 0 | 24 | 24PASS,0F0E0skip; count/suggestion-price deltas included |
| independent5 | 0 | 27 | **27PASS,0F0E0skip,11.001s**:20 canonical +7 independent probes, including final suggestion age/timeline |

Independent5 `check` и `makemigrations --check --dry-run` PASS, PostgreSQL161 applied/0 pending, cleanup PASS. Independent2–4 cleanup также PASS. Root assertions не менял. Частный invalid fixture — reviewer error, не application defect.

Seven private probes: admission-only price scope, q-only price scope, hidden Place/Org, actual template query budget, stale Place ownership/unpublished Org, unknown local Activity taxonomy, suggestion matched age. Actual rendered `place_card` SQL: **1 card=9,4 cards=9**. Reader comparison на одинаковых fixtures: old1=6/old8=41, batch1=batch8=8; seconds0.069527/0.146410 vs0.070588/0.079989. Это synthetic single samples, не production/load benchmark.

14 relevant source/test artifacts SHA сверены после independent5, изменений во время final run0. `/tmp/task33-stage19-review-source-sha.json` SHA256 `0eb49a24bf66b9ccc1b5de51838b5a4e8865bd8ed65f46c4b8dacb53af8bb826`; includes search/filtering/presentation/filter options/views/three controllers/tag/two templates/stage19 tests/two adapted old suites. Report itself не хешируется.

Adapted test review: `test_public_filter_consistency` age parser fixtures теперь explicitly approved admission, existing unknown/zero/open/conjunction assertions сохранены. `pricing_plans_relational` compared against stage19 entry snapshot: только obsolete-budget test changed to authorized ignore-params contract с новыми sort/selected checks; USD exact assertions уже были на входе, сохранены. Это изменение договорённого требования, не ослабление неизменённого контракта.

## NOT RUN / risks / handoff

Production, full suite, реальные внешние SMTP/analytics и rendered browser этим исполнителем NOT RUN; browser evidence принадлежит отдельному reviewer. Source/template inspection не является browser acceptance.

`taxonomy_counts` materializes public IDs/snapshots into Python sets per request: query count bounded, large-catalog latency/memory NOT MEASURED. Это performance limit evidence, не наблюдавшийся production incident. Изолированная schema unchanged.

Next: `/root` / django-reviewer сверяет final source SHA, своё targeted/adjacent evidence и browser delta, затем обновляет stage19 report/journal и освобождает собственный active_run. Новых confirmed blockers в bounded scope нет. Stage20/production не запускать без отдельного поручения.

## Reopened final delta

После independent5 browser обнаружил `/new` age bounds removal через `CleanPublicQueryMiddleware` whitelist и force_new normalizer; предыдущий timeline test использовал другую category у older group, поэтому не доказывал сохранение возраста. Lead усиливает fixture same-category older group и redirect preservation. Reviewer добавил восьмой независимый private probe для selected/redirect/query_without_page bounds и negative older group. `public_urls.py`, `PlaceController` normalized params и SEO price-promise removal будут проверены final rerun; предыдущее PASS не переносится автоматически на новую source delta.

## Final query/SEO delta — CLOSED

```bash
./.venv/bin/python /tmp/task33-stage19-review-run.py --mode all --label catalog.testcases.test_task33_search --output /tmp/kidsmap-task33-stage19-independent6
```

**exit0,31/31 PASS,0 failures/errors/skips,17.908s**:22 canonical stage19 +9 independent temporary probes. `check`, `makemigrations --check --dry-run` PASS; PostgreSQL161 applied/0 pending; cleanup PASS. The two added private checks validate same-category older Group rejection with explicit age_from/to5 on `/new`, selected/redirect/normalized-query preservation, and legacy `age=5` with foreign-param clean redirect on both `/catalog/` and `/catalog/new/`.

`public_urls:PUBLIC_QUERY_PARAMS` now preserves supported age legacy and bounds, `/new` subcategory/metro; `PlaceController:_build_normalized_query_params` keeps bounds and metro for new-page pagination/locale and never reconstructs retired budgets. `seo:build_catalog_seo_payload` default description AZ/RU/EN no longer promises price filtering. Meaningful canonical same-category/unknown-legacy negative fixture and metadata tests pass. Earlier timeline assertion alone was insufficient; final stronger checks supersede it.

No source changed during final independent6:16/16 source/test SHA matched `/tmp/task33-stage19-review-source-sha-finaldelta.json`, SHA256 `8000c3b9aafbb717c80926c246b343272ba936f01277f63afea250f465fdb2d9`. This adds public_urls/seo to previous14-source review scope. CSS/rendered-overflow delta remains browser reviewer evidence; no claim of personal rendered QA.

Final actual rendered-card SQL budget1=9/four=9; previous reader1=6/eight=41, batch1=eight=8. Observed seconds0.066997/0.201064 vs0.069069/0.102221. No additional confirmed blocker in bounded Python/template integration scope. Named handoff remains `/root` / django-reviewer for aggregate acceptance/journal; stage20/production not run.
