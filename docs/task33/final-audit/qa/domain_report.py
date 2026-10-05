"""Conservative domain evidence map. Never converts a test name into a PASS."""
import json,hashlib,collections,ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT/'docs/task33/final-audit'
data=json.loads((OUT/'domain-inputs.json').read_text(encoding='utf-8'))
# Each row is an authored review conclusion, not a generated acceptance verdict.
S={
1:('Согласовать границы и очередь 28 работ','Пакет заданий, решения D01–D15 и журнал задают последовательность. Исторические согласования сохраняются.', ['docs/task33/README.md','docs/task33/decisions.md','docs/task33/architecture.md'],[], 'Историческое согласование нельзя повторно доказать текущим backend тестом.'),
2:('Согласовать вид каталога и кабинета','Принятые макеты служат входом реализации; текущие шаблоны проверяет отдельный browser reviewer.', ['docs/task33/prompts/02.md','docs/task33/architecture.md'],[], 'Согласование макета и совпадение живого интерфейса — разные доказательства.'),
3:('Согласовать вид админки и проверки предложений','Единый admin shell и review workflow реализованы позже в15–16.', ['docs/task33/prompts/03.md','src/catalog/domain_admin/place.py'],[], 'Текущий визуальный результат относится к browser report, а не к source review.'),
4:('Зафиксировать безопасный исходный baseline','QA04 создаёт отдельный PostgreSQL/cache/media/email и проверяет сеть/libpq; исходные assertions сохранены.', ['qa04/run.py','qa04/isolation.py','docs/task33/reports/04.md'],[], 'Baseline исторический; итоговый полный suite по-прежнему содержит ошибки и не объявляется зелёным.'),
5:('Добавить структуру без потери прежних мест','Org→Program и Place→Activity→Group добавлены рядом с Place; FK, версии и запрет каскадной потери поддерживают сохранение личности карточки.', ['src/catalog/models/catalog_structure.py','src/catalog/models/place.py'],['test_hierarchy_protects_old_place_from_cascade','test_legacy_place_without_org_keeps_public_identity_and_unknown_facts'],'Часть межстрочных условий защищена сервисом/ORM, а не SQL trigger; bulk/raw writes не равнозначны нормальному save.'),
6:('Отделить управление от принадлежности к сети','Claim не публикует; join требует обе стороны; transfer отзывает прежние grants; detach сохраняет утверждённые местные данные.', ['src/catalog/services/organization_ownership.py'],['test_management_claim_approval_does_not_publish','test_detach_pending_program_retains_approved_snapshot_ids_and_visibility'],'Синтетическое владение не доказывает юридическое владение реальным бизнесом.'),
7:('Дать команде ограниченные полномочия','Business team grants и selected/all_network проверяются заново на сохранении; Program edit отделён от Place edit.', ['src/catalog/services/business_team.py','src/catalog/services/place_access.py'],['test_create_and_edit_program_has_separate_right_and_pending_impact'],'Source ACL не заменяет проверку всех прямых URL; независимый security report закрывает свою матрицу.'),
8:('Сохранять публичную версию при проверке правки','Один publication pipeline хранит patch/schema/base/version и проверяет свежие зависимости; цена/расписание имеют явные узкие immediate paths.', ['src/catalog/services/publication.py','src/catalog/services/publication_forms.py','src/catalog/services/place_readiness.py'],['test_pending_and_rejected_keep_approved_live','test_dependent_price_conditions_bundle_wholly_gated','test_overlapping_live_change_refuses_stale_approval'],'Старые payload без signed version и прежние обязательные фото/coords не соответствуют принятому контракту; каждое падение требует отдельного разбора.'),
9:('Восстанавливать незавершённую работу без публикации','ServerDraft имеет actor/object/schema/source/version; приватные фото не становятся public автоматически; create материализуется один раз.', ['src/catalog/services/server_drafts.py','src/catalog/controllers/draft_controller.py'],['test_foreign_actor_cannot_read_or_update','test_create_materialize_missing_name_then_idempotent','test_two_devices_with_same_version_only_one_writes'],'Offline/reload/device UX отдельно от HTTP shape; nested working copy проверяется при final form, не полностью на autosave.'),
10:('Сохранить тарифы и правильно назвать итоговую цену','PricingPlan XOR place/group, scope IDs, versioned nested writer и единый summary; trial не превращает платное занятие в бесплатное.', ['src/catalog/models/pricing_plan.py','src/catalog/services/pricing_plans.py'],[], 'Все consumers/CSV/JSON нельзя считать проверенными одним round-trip; соответствующие test cases и browser evidence должны сопоставляться отдельно.'),
11:('Переносить данные явно, повторяемо и без догадок','Ledger/fingerprint/checkpoint и атомарные пакеты; unknown очередь manual review; dry-run не сохраняет модель.', ['src/catalog/services/data_conversion.py','docs/task33/migration-map.md'],['test_populated_dry_run_preserves_all_database_rows','test_failed_batch_rolls_back_mapping_and_checkpoint_together','test_repeat_and_resume_do_not_duplicate_mappings'],'Репетиция синтетическая; реальный состав production UNKNOWN. Мой прежний DB отчёт не является независимым self-review.'),
12:('Дать владельцу понятный кабинет организации','Organization workspace использует общий navigation, ownership services и scoped team; Org может быть без филиалов.', ['src/catalog/controllers/organization_workspace.py','src/templates/account/organization_form.html'],[], 'Backend route tests не доказывают focus/responsive/accepted design; отдельная fresh browser matrix.'),
13:('Создавать место одной непрерывной формой','Owner form continuous mode с четырьмя разделами, draft transport и явным submit; standalone без Org допустим.', ['src/catalog/forms.py','src/catalog/controllers/owner_places_controller.py'],[], 'Пробел standalone taxonomy проявляется после создания занятия: category+age не находит новый объект;14/19.'),
14:('Разделить общую программу и местные группы','Program editor имеет отдельное право/impact confirmation; approved snapshot общей части и local supplement, группы и тарифы сохраняются.', ['src/catalog/controllers/program_workspace.py','src/catalog/services/pricing_plans.py','src/catalog/services/organization_ownership.py'],['test_create_and_edit_program_has_separate_right_and_pending_impact','test_group_conditions_date_changes_only_on_explicit_current_owner_action'],'Частично: standalone writer не задаёт category; Program writer задаёт category, но не subcategory. D04 не обещает отдельное поле subcategory Program, однако19 обещает комбинированный поиск.'),
15:('Редактировать новую структуру в общей админке','Domain admin отделяет draft/submit/approve/unpublish и скрытые carryover values; версия обязательна для снятия публикации.', ['src/catalog/domain_admin/place.py','src/catalog/domain_admin/catalog_structure.py'],['test_place_admin_unpublish_skips_form_save','test_stale_concealed_place_value_cannot_overwrite_fresh_live_value'],'Admin legacy suite не зелёный: два причинных probes объясняют старые expectations; остальные failures не списываются группой.'),
16:('Проверять предложения в одном hub','Volunteer предложение остаётся отдельным от владения; review показывает current/candidate, version/impact и counters.', ['src/catalog/services/volunteer_places.py','src/catalog/controllers/volunteer_controller.py'],[], 'Все GET/POST/AJAX substitution сценарии требуют точной security matrix; UI focus/diff — browser scope.'),
17:('Сохранять уведомление даже при сбое почты','Transactional inbox/outbox, event/entity/version/recipient dedupe, свежие права и bounded retry; runner не настраивает production cron.', ['src/catalog/services/workflow_notifications.py'],['test_emit_is_transactional_and_dedupes_event_entity_version_recipient','test_smtp_failure_keeps_inbox_and_retry_sends_once','test_join_detach_transfer_and_access_disable_emit_once_for_each_recipient'],'PARTIAL17-03: SMTP success перед DB commit оставляет crash window для повторной физической отправки. Тест normal retry не доказывает exactly-once mail; внешний SMTP NOT_RUN.'),
18:('Показать честные страницы организации, места и занятия','Public resolver берёт только approved/current, местные overrides и свежую связь; Org без общего рейтинга; detach отключает inherited contacts.', ['src/catalog/services/public_presentation.py','src/catalog/controllers/public_details_controller.py'],['test_active_contacts_fallback_and_detach_remove_live_org_sources','test_detail_routes_empty_org_and_standalone_place','test_hidden_parent_or_activity_returns_404_without_public_payload'],'Новые browser Org/Activity contexts выполняет другой reviewer; ORM display fixture не выдаётся за end-to-end publication.'),
19:('Находить место по одному подходящему занятию','matching_groups делает conjunction в одной Group, дедуплицирует Place, matched prices отдельно; legacy unknown не получает ложного exact match.', ['src/catalog/services/catalog_search.py','src/catalog/services/filtering.py'],['test_category_age_must_match_one_group','test_subcategory_needs_approved_offer_mapping','test_batch_queries_do_not_grow_per_card'],'CONFIRMED P2: реальные новые standalone занятия находятся по возрасту, но теряются при category+age. Subcategory reader работает лишь при готовом snapshot, которого текущие writers не создают. Passing reader fixtures внедряют snapshot напрямую.'),
20:('Показать одну площадку с независимыми бизнесами','Map payload группирует только confirmed venue, применяет те же filters; no coords остаётся в list, близость не создаёт Org.', ['src/catalog/services/map_payload.py','src/catalog/services/public_presentation.py'],[], 'Maps transport stubs не доказывают внешний provider; source payload не является rendered popup keyboard evidence.'),
21:('Сохранить языки, адреса страниц и честную индексацию','AZ fallback маркируется, canonical/hreflang/sitemap по содержательному переводу; старые Place IDs/paths и typed JSON-LD.', ['src/catalog/services/public_localization.py','src/catalog/sitemaps.py'],[], 'Timezone lastmod legacy assertion имеет UTC/local disagreement; отдельно классифицировано, не blanket regression. Search product gap влияет и на обнаружение карточек.'),
22:('Сохранить историю отзывов и один видимый вклад','Typed heads/revisions Place/Activity/Specialist/Event; current approved сохраняется при pending, reactions привязаны к revision, unknown authors не объединяются.', ['src/catalog/services/review_versions.py','src/catalog/models/review.py'],['test_pending_edit_keeps_approved_projection_and_one_rating','test_unknown_sources_remain_independent','test_reaction_ids_and_original_revision_are_preserved','test_retention_clears_all_labels_and_pending_candidate'],'Compatibility trusted legacy save — отдельный путь; historical migration + deletion hooks надо оценивать вместе. Org не имеет общего балла.'),
23:('Подготовить локальный R1 с сохранением новых данных','R1 cohort fail-closed и конверсия/recovery package; synthetic fixtures не реальные участники пилота.', ['docs/task33/reports/23.md','qa23/rehearsal.py'],[], 'Исторический R1 snapshot не итоговый R2 PASS. Прежняя моя DB работа не независимый повторный аудит. Реальный пилот/production запуск NOT_RUN.'),
24:('Проверить личность специалиста и приватные документы','KidsMap claim назначает аккаунт человека; employment bilateral/history; identity evidence private, certificate approved+person opt-in.', ['src/catalog/services/specialist_domain.py','src/catalog/services/specialist_documents.py'],[], 'Не существует автоматического доказательства личности; private production media transition остаётся отдельной операцией. Upload suffix/size не равно полному MIME анализу.'),
25:('Дать человеку и организации разные экраны специалиста','Person workspace, claim/employment/certificate flows; Org не получает biography/docs через Place ACL.', ['src/catalog/controllers/specialist_workspace.py','src/catalog/services/specialist_documents.py'],[], 'Public certificate требует всех текущих условий одновременно. История и private practice не должны выглядеть текущей работой; fresh browser evidence отдельно.'),
26:('Дать событию своего организатора и неизменную историю','Один Org или verified Specialist организатор, venue отдельно; aware Baku интервалы, snapshot при approval, cancellation/reschedule append history.', ['src/catalog/services/event_domain.py','src/catalog/services/event_queries.py'],['test_venue_owner_cannot_edit_organizers_event','test_publication_snapshot_stays_at_original_venue_after_move','test_past_occurrence_cannot_be_reused_under_same_id'],'V3 precision fix сохраняет секунды лишь для неизменившегося отображённого времени, изменение минуты остаётся защищено. История сервисная/ORM, не неуязвимый raw SQL audit log.'),
27:('Показывать один список и полный календарь событий','List/calendar используют общие query filters и Baku half-open boundaries; month не ограничен list pagination; реальные Event IDs без generated occurrences.', ['src/catalog/services/events_calendar.py','src/catalog/controllers/place_controller.py'],['test_month_fourteen_records_not_list_page_and_no_fabricated_ids','test_navigation_urls_preserve_filters_and_discard_page_tracking_redirect','test_calendar_gets_do_not_create_occurrences_or_mutate_event'],'Accepted preservation q делает прежний calendar assertion устаревшим. Keyboard/responsive фактически проверяет browser reviewer, feature flag production off.'),
28:('Подготовить проверяемый локальный R2 без запуска production','Exact V3 archive/image/source/schema/media/cohort, frozen compatible reader и native restore с новыми данными; root повторяет полный suite и роли.', ['docs/task33/reports/28-artifact-refresh3.json','docs/task33/final-audit/recovery-results.json'],[], 'NOT GREEN full suite, P2 taxonomy product gap, external OAuth/Maps/SMTP/pilot NOT_RUN. Локальная проверка не разрешает production. Авторство прежнего DB/image followup раскрыто.')
}
ALIASES={'qa04/run.py':'docs/task33/qa04/run.py','qa04/isolation.py':'docs/task33/qa04/guard.py',
'src/catalog/controllers/draft_controller.py':'src/catalog/controllers/server_draft_api.py',
'src/catalog/services/data_conversion.py':'src/catalog/services/catalog_conversion.py',
'src/templates/account/organization_form.html':'src/catalog/templates/pages/organization_workspace.html',
'src/catalog/domain_admin/catalog_structure.py':'src/catalog/domain_admin/business.py',
'src/catalog/controllers/volunteer_controller.py':'src/catalog/services/volunteer_editor.py',
'src/catalog/controllers/public_details_controller.py':'src/catalog/controllers/public_details.py',
'src/catalog/services/public_localization.py':'src/catalog/services/public_languages.py',
'qa23/rehearsal.py':'docs/task33/qa23/rehearsal.py','src/catalog/services/events_calendar.py':'src/catalog/services/event_calendar.py'}
S={n:(a,b,[ALIASES.get(p,p) for p in refs],tests,gap) for n,(a,b,refs,tests,gap) in S.items()}
MORE={7:['test_selected_all_current_does_not_include_future_branch','test_all_network_includes_future_branch_but_not_org_or_program_actions'],
10:['test_xor_is_enforced_by_postgresql_and_group_resolves_place','test_target_scoped_roundtrip_and_foreign_ids','test_trial_fee_and_membership_preserve_regular_headline'],
12:['test_empty_account_creates_organization_without_address_or_branch','test_manager_sees_selected_branch_only_and_direct_url_does_not_expand_scope'],
13:['test_create_uses_four_visible_sections_and_server_draft_transport','test_new_group_with_three_tariffs_stays_candidate_until_place_approval'],
16:['test_volunteer_a_cannot_read_or_mutate_b_candidate_by_direct_id','test_informational_approval_without_business_grant','test_owner_handover_schema_and_stale_source_block_approval'],
20:['test_verified_venue_one_point_two_independent_cards','test_filtered_members_and_matched_prices','test_address_edit_detaches_only_changed_place_and_preserves_event'],
21:['test_complete_ru_translation_is_reciprocal_without_en','test_entity_sitemaps_only_offer_substantive_approved_languages','test_script_termination_text_remains_data_in_entity_schema'],
24:['test_claim_assigns_verified_person_and_records_legacy_manager','test_organization_invitation_or_proposal_is_not_person_confirmation','test_online_switch_preserves_historical_location_and_primary'],
25:['test_person_profile_and_business_denial','test_certificate_http_consent_moderation_and_revocation','test_history_is_distinct_from_current_cooperation'],
28:['test_disabled_cohort_blocks_http_write_without_deleting_post_switch_rows','test_unchanged_rendered_minutes_preserve_approved_seconds','test_owner_changed_minute_still_requires_recorded_change']}
for n,names in MORE.items():
    a,b,refs,oldnames,gap=S[n];S[n]=(a,b,refs,oldnames+names,gap)
fresh=json.loads((OUT/'full-results.json').read_text(encoding='utf-8'))
suite=fresh['suite-results.json'];executed=set(suite['executed_ids'])
failed={p['id'] for p in suite['problems']}
def runtime(testid):
    return 'FAILED_CURRENT_ROOT_FULL' if testid in failed else ('PASSED_CURRENT_ROOT_FULL_ATTRIBUTED' if testid in executed else 'NOT_RUN_CURRENT_ROOT_FULL')
tests={t['id'].split('.')[-1]:t for t in data['tests']}
def selected(names):
    result=[]
    for name in names:
        candidates=[t for t in data['tests'] if t['id'].endswith('.'+name)]
        if len(candidates)!=1:raise ValueError((name,len(candidates)))
        result.append(candidates[0])
    return result
def assertion_evidence(t):
    lines=(ROOT/t['path']).read_text(encoding='utf-8').splitlines()
    body='\n'.join(lines[t['line']-1:t['end_line']])
    # Source excerpts describe concrete assertions; names are not a PASS proxy.
    return [line.strip() for line in body.splitlines() if 'self.assert' in line][:10]
rows=[]
for old in data['stages']:
    n=old['stage'];promise,impl,refs,names,gap=S[n];matched=selected(names)
    rows.append({'stage':n,'title':old['title'],'promise':promise,'implementation':impl,
        'status':'HISTORICAL_ACCEPTANCE' if n<=4 or n==23 else 'PARTIAL',
        'dependencies':old['dependencies'],'source_refs':refs,
        'test_ids':[t['id'] for t in matched], 'test_results':{t['id']:runtime(t['id']) for t in matched},
        'test_evidence_kind':'ASSERTION_SOURCE_REVIEW + current full-results.json runtime attributed to /root',
        'gaps':[gap],'user_value':promise,'prompt_sha256':old['prompt_sha256']})
meta={'role':'django-reviewer','executor':'retained stage28_database sequential role transition','mode':'AUDIT_ONLY',
    'head':'015d031d8eb17114bd860159dde805b38df3c13c','snapshot':'dirty WORKTREE V3; not LOCAL HEAD deployment',
    'active_run':'final-audit-20261004-080525Z','production':'UNKNOWN_NOT_CONTACTED','old_generic_status_adopted':False,
    'authorship':'Earlier stage28 DB/recovery/image evidence was authored by this same executor: no independent self-review claim.',
    'test_names_are_not_pass':True,'requirements_count':306,
    'fresh_root_full':{'tests':1817,'failures':109,'errors':11,'skipped':0,'task33':'579/580; ownership race failure'},
    'runtime_source':'docs/task33/final-audit/full-results.json; /root execution, not my independent runtime'}
(OUT/'stage-map.json').write_text(json.dumps({'metadata':meta,'stages':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Explicitly narrow mappings. Remaining rows are individually unverified, never blanket PASS.
EXACT={
'R06-01':['test_new_org_has_management_not_business_verification_or_publication'],
'R08-01':['test_pending_and_rejected_keep_approved_live'],
'R08-02':['test_dependent_price_conditions_bundle_wholly_gated'],
'R08-03':['test_overlapping_live_change_refuses_stale_approval'],
'R08-04':['test_program_propagates_only_common_active_links'],
'R08-05':['test_optional_photos_coordinates_and_business_website','test_public_space_without_contacts_is_ready'],
'R08-07':['test_confirmed_closure_keeps_detail_and_excludes_catalog','test_old_inactive_is_not_exposed_by_closure'],
'R08-08':['test_pending_and_rejected_keep_approved_live'],
'R09-03':['test_foreign_actor_cannot_read_or_update','test_edit_draft_never_writes_live_and_stale_version_preserves_input'],
'R09-04':['test_create_materialize_missing_name_then_idempotent'],
'R09-07':['test_two_devices_with_same_version_only_one_writes','test_simultaneous_first_retry_one_draft'],
'R09-08':['test_revocation_stops_update_and_list_hides_draft','test_500_response_keeps_submitted_text'],
'R09-09':['test_materialize_keeps_uploaded_photo_outside_public_media'],
'R11-01':['test_populated_dry_run_preserves_all_database_rows'],
'R11-03':['test_failed_batch_rolls_back_mapping_and_checkpoint_together'],
'R11-07':['test_repeat_and_resume_do_not_duplicate_mappings'],
'R11-08':['test_old_plan_never_overwrites_changed_source'],
'R11-11':['test_populated_dry_run_preserves_all_database_rows'],
'R14-04':['test_create_and_edit_program_has_separate_right_and_pending_impact'],
'R14-01':['test_create_and_edit_program_has_separate_right_and_pending_impact'],
'R14-02':['test_linked_activity_uses_approved_program_and_keeps_local_group'],
'R14-06':['test_group_conditions_date_changes_only_on_explicit_current_owner_action'],
'R15-07':['test_stale_concealed_place_value_cannot_overwrite_fresh_live_value'],
'R17-01':['test_emit_is_transactional_and_dedupes_event_entity_version_recipient'],
'R17-02':['test_join_detach_transfer_and_access_disable_emit_once_for_each_recipient'],
'R17-03':['test_emit_is_transactional_and_dedupes_event_entity_version_recipient','test_smtp_failure_keeps_inbox_and_retry_sends_once'],
'R17-04':['test_smtp_failure_keeps_inbox_and_retry_sends_once'],
'R17-07':['test_smtp_failure_keeps_inbox_and_retry_sends_once'],
'R18-07':['test_detail_routes_empty_org_and_standalone_place'],
'R18-08':['test_active_contacts_fallback_and_detach_remove_live_org_sources','test_hidden_parent_or_activity_returns_404_without_public_payload'],
'R19-01':['test_category_age_must_match_one_group','test_groups_of_one_activity_cannot_cross_age_conditions'],
'R19-02':['test_double_reader_and_multiple_matching_groups_one_place','test_matched_card_groups_and_prices_only'],
'R19-03':['test_unknown_legacy_not_exact_but_general_and_detail_remain'],
'R19-04':['test_obsolete_prices_are_ignored_and_removed_from_selected'],
'R19-05':['test_org_name_only_current_published_affiliations'],
'R19-07':['test_category_age_must_match_one_group'],
'R19-08':['test_matched_card_groups_and_prices_only'],
'R19-09':['test_batch_queries_do_not_grow_per_card'],
'R19-10':['test_subcategory_needs_approved_offer_mapping'],
'R22-02':['test_latest_approved_effective_timestamp_and_archive_preserved','test_unknown_sources_remain_independent'],
'R22-04':['test_pending_edit_keeps_approved_projection_and_one_rating'],
'R22-05':['test_reaction_ids_and_original_revision_are_preserved'],
'R22-09':['test_retention_clears_all_labels_and_pending_candidate'],
'R26-03':['test_publication_snapshot_stays_at_original_venue_after_move'],
'R26-07':['test_venue_owner_cannot_edit_organizers_event'],
'R26-08':['test_confirmed_online_person_needs_no_geography'],
'R27-07':['test_month_fourteen_records_not_list_page_and_no_fabricated_ids'],
'R27-09':['test_calendar_gets_do_not_create_occurrences_or_mutate_event']}
EXACT.update({
'R07-01':['test_selected_all_current_does_not_include_future_branch','test_all_network_includes_future_branch_but_not_org_or_program_actions'],
'R10-01':['test_xor_is_enforced_by_postgresql_and_group_resolves_place'],
'R10-02':['test_target_scoped_roundtrip_and_foreign_ids'],
'R10-03':['test_group_save_delete_signals_update_scalar_projection'],
'R10-05':['test_trial_fee_and_membership_preserve_regular_headline','test_group_age_conflict_and_currency_are_not_silently_coerced'],
'R10-06':['test_json_ui_validator_distinguishes_v1_from_nested_v2','test_versioned_json_export_keeps_v1_direct_only'],
'R10-07':['test_target_scoped_roundtrip_and_foreign_ids'],
'R10-08':['test_trial_fee_and_membership_preserve_regular_headline'],
'R10-09':['test_trial_fee_and_membership_preserve_regular_headline'],
'R10-11':['test_csv_normalization_never_infers_or_removes_group_plans','test_json_ui_validator_distinguishes_v1_from_nested_v2'],
'R12-01':['test_empty_account_creates_organization_without_address_or_branch'],
'R12-07':['test_standalone_places_are_visible_beside_zero_org_state'],
'R12-08':['test_manager_sees_selected_branch_only_and_direct_url_does_not_expand_scope'],
'R12-09':['test_organization_draft_reappears_on_reload_and_never_changes_live_name'],
'R13-01':['test_create_uses_four_visible_sections_and_server_draft_transport'],
'R13-05':['test_explicit_place_save_consumes_matching_server_draft'],
'R13-06':['test_public_live_place_is_not_hidden_by_incomplete_server_draft'],
'R13-07':['test_public_space_can_submit_without_organization_photo_coordinates_or_contact'],
'R13-08':['test_business_needs_one_allowed_contact_and_does_not_need_translation'],
'R16-02':['test_volunteer_a_cannot_read_or_mutate_b_candidate_by_direct_id'],
'R16-03':['test_informational_approval_without_business_grant'],
'R16-04':['test_hub_filters_and_counts_include_all_content_and_links','test_hub_program_preview_lists_affected_branches'],
'R16-07':['test_volunteer_a_cannot_read_or_mutate_b_candidate_by_direct_id'],
'R16-08':['test_volunteer_org_and_program_publish_without_business_grant'],
'R16-09':['test_return_keeps_candidate_and_final_reject_records_reason','test_schema_conflict_and_stale_field_do_not_apply_candidate'],
'R20-01':['test_verified_venue_one_point_two_independent_cards'],
'R20-02':['test_filtered_members_and_matched_prices'],
'R20-03':['test_nearby_or_identical_coordinates_do_not_assert_shared_identity'],
'R20-04':['test_no_coordinates_remains_visible_with_clear_card_marker','test_invalid_coordinates_rejected'],
'R20-05':['test_address_edit_detaches_only_changed_place_and_preserves_event'],
'R20-07':['test_verified_venue_one_point_two_independent_cards'],
'R20-08':['test_filtered_members_and_matched_prices'],
'R20-09':['test_publication_snapshot_stays_at_original_venue_after_move'],
'R21-01':['test_new_publication_requires_az_and_does_not_require_ru_en'],
'R21-02':['test_complete_ru_translation_is_reciprocal_without_en','test_az_only_place_is_canonical_az_and_has_only_az_alternate'],
'R21-03':['test_old_identifier_and_wrong_slug_redirect_to_same_language_without_chain'],
'R21-04':['test_organization_has_factual_schema_and_az_fallback','test_complete_activity_translation_has_own_canonical_and_course_facts'],
'R21-05':['test_closed_historical_place_has_200_notice_and_no_current_offers'],
'R21-07':['test_mixed_translation_labels_each_field_with_its_actual_language'],
'R21-08':['test_locale_does_not_change_currency_country_or_class_language'],
'R24-01':['test_claim_assigns_verified_person_and_records_legacy_manager','test_form_proposal_records_author_without_person_ownership'],
'R24-02':['test_organization_invitation_or_proposal_is_not_person_confirmation','test_same_account_two_roles_still_need_two_explicit_confirmations'],
'R24-03':['test_online_switch_preserves_historical_location_and_primary','test_cancel_keeps_employment_period_location_and_review_history'],
'R24-08':['test_document_nested_id_and_identity_publication_denied'],
'R24-09':['test_concurrent_claimants_cannot_both_own_one_person','test_changed_location_retires_old_row_without_overwriting_history'],
'R25-03':['test_org_invitation_does_not_auto_confirm_and_person_accepts'],
'R25-07':['test_person_profile_and_business_denial'],
'R25-08':['test_history_is_distinct_from_current_cooperation'],
'R25-09':['test_certificate_http_consent_moderation_and_revocation'],
'R26-02':['test_past_occurrence_cannot_be_reused_under_same_id','test_cancel_keeps_approved_publication_and_append_only_period'],
'R26-09':['test_full_http_archive_keeps_baku_date_and_snapshot_district'],
'R27-03':['test_navigation_urls_preserve_filters_and_discard_page_tracking_redirect'],
'R27-04':['test_month_fourteen_records_not_list_page_and_no_fabricated_ids'],
'R28-08':['test_disabled_cohort_blocks_http_write_without_deleting_post_switch_rows']})
from domain_requirement_extra import EXTRA
EXACT.update(EXTRA)
reqs=[]
for r in data['requirements']:
    stage=rows[r['stage']-1];mapped=selected(EXACT.get(r['id'],[]))
    status='PARTIAL_CURRENT_LOCAL_EVIDENCE' if mapped else 'NOT_INDIVIDUALLY_VERIFIED'
    if r['stage']<=4 or r['stage']==23:status='HISTORICAL_SCOPE_NOT_CURRENT_PASS'
    if r['id']=='R19-10':status='PARTIAL_CONFIRMED_PRODUCT_GAP'
    if r['id']=='R17-03':status='PARTIAL_CRASH_WINDOW_NOT_TESTED'
    if r['id']=='R28-07':status='PARTIAL_FULL_SUITE_FAILURES_AND_PRODUCT_GAP'
    evidence=[{'kind':'SOURCE_CONTEXT_NOT_ACCEPTANCE_PROOF','ref':p} for p in stage['source_refs']]
    evidence += [{'kind':'MEANINGFUL_ASSERTION_SOURCE_AND_ROOT_RUNTIME','id':t['id'],'ref':t['path']+':'+str(t['line']),'runtime':runtime(t['id']),'actual_assertions':assertion_evidence(t)} for t in mapped]
    if any(runtime(t['id'])=='FAILED_CURRENT_ROOT_FULL' for t in mapped):status='FAILED_CURRENT_SUBCLAUSE_WITH_OTHER_LOCAL_EVIDENCE'
    limitation=('Именно этот составной пункт не имеет отдельно установленного полного runtime доказательства в данном review; соседний тест не превращает его в PASS.' if not mapped else 'Указанный assertion проверяет конкретную часть пункта. Фактический runtime следует подтверждать свежим root suite по этому ID; UI/внешние/составные части не покрываются автоматически.')
    reqs.append({'id':r['id'],'stage':r['stage'],'section':r['section'],'text':r['text'],'status':status,
        'evidence':evidence,
        'covered_subclauses':[{'case':t['id'],'scope':t['id'].split('.')[-1].removeprefix('test_').replace('_',' '),'status':runtime(t['id'])} for t in mapped],
        'uncovered_subclauses':['Только перечисленные assertion scopes доказаны; другие части исходного текста, включая rendered UI/внешние системы, не приняты автоматически.'],
        'limitations':[limitation,stage['gaps'][0]]})
from domain_noncase import NONCASE
for r in reqs:
    if r['id'] not in NONCASE:continue
    status,ref,note=NONCASE[r['id']]
    r['status']=status;r['evidence'].append({'kind':'EXACT_NON_CASE_SCOPE_EVIDENCE','ref':ref,'observed_scope':note})
    r['covered_subclauses']=[{'scope':note,'status':status}]
    r['uncovered_subclauses']=[note]
    r['limitations']=[note]
probe=json.loads((OUT/'domain-results.json').read_text(encoding='utf-8'))
for r in reqs:
    if r['id'] not in {'R14-01','R14-02','R19-10'}:continue
    r['evidence'].append({'kind':'OWN_GUARDED_REAL_WRITER_PROBE','ref':'domain-results.json:domain-observations.json',
        'observations':{k:probe['domain-observations.json'][k] for k in ('standalone_search','program_search')},
        'interpretation':'Program category works; no separate Program.subcategory promise invented. Stage14 writer→19 search connection remains product partial for standalone/category-age and offer subcategory.'})
    if r['id']=='R19-10':
        r['uncovered_subclauses']=['Доступный writer подтверждённой category standalone и subcategory offer отсутствует; reader fixtures внедряютsnapshot черезORM. Пользовательский writer→combinedsearch сценарий не реализован полностью.']
counts=dict(collections.Counter(r['status'] for r in reqs))
(OUT/'requirements-review.json').write_text(json.dumps({'metadata':meta,'status_counts':counts,'requirements':reqs},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for row in rows for p in row['source_refs'] if (ROOT/p).is_file()}
(OUT/'domain-source.json').write_text(json.dumps({'metadata':meta,'sha256':hashes,'missing_refs':sorted({p for row in rows for p in row['source_refs'] if not (ROOT/p).is_file()})},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'stages':len(rows),'requirements':len(reqs),'status_counts':counts,'missing_refs':[p for row in rows for p in row['source_refs'] if not (ROOT/p).is_file()]}))
