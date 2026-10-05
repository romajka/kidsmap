"""Individual current failure inventory, conservative causal classification."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];OUT=ROOT/'docs/task33/final-audit'
fresh=json.loads((OUT/'full-results.json').read_text(encoding='utf-8'))
previous=json.loads((ROOT/'docs/task33/reports/28-full-results.json').read_text(encoding='utf-8'))
old={p['id']:p for p in previous['classification']['remaining_problem_entries']}
observations=json.loads((OUT/'domain-results.json').read_text(encoding='utf-8'))['domain-observations.json']
CAUSE={
'catalog.testcases.admin.TestAdminOwnershipModerationUX.test_admin_can_approve_request_with_direct_button_url':('CONFIRMED_ACCEPTED_CONTRACT_EXPECTATION_DEBT','legacy_claim','Управление одобрено, owner изменён; активация карточки не является действием claim. D02/D06.'),
'catalog.testcases.admin.TestAdminOwnershipModerationUX.test_place_admin_can_unpublish_place_from_change_form':('CONFIRMED_PAYLOAD_VERSION_DEBT','legacy_unpublish','Старый POST не содержит unpublish_version. Повтор с единственным добавлением текущей версии даёт302/draft/inactive.'),
'catalog.testcases.admin.TestPlaceRatingsAdmin.test_changelist_pagination_preserves_filters_search_and_sorting':('CONFIRMED_DISTRICT_FIXTURE_QUERY_DEBT','legacy_pagination','Созданные5 fixtures имеют baku_narimanov, query=baku даёт0. Замена только querydistrict возвращает3 корректные страницы с сохранёнными фильтрами.'),
'catalog.testcases.admin.TestAdminOwnershipModerationUX.test_failed_publish_keeps_published_card_active_and_shows_all_issues':('PARTIAL_SOURCE_CONTRACT_MISMATCH_FULL_CAUSE_NOT_PROVEN',None,'Assertion требует coords/photo blocking, которые08 сделал optional, и прежнюю message. Старый payload безpublication_token. Complete currentprotocol action не воспроизведён: не объявляется безвредным целиком.'),
'catalog.testcases.test_task33_ownership.OwnershipConcurrencyTests.test_transfer_racing_confirmation_never_grants_stale_network_right':('FAILED_CURRENT_NONDETERMINISTIC_CONCURRENCY_NOT_DISMISSED',None,'Fresh rootfull+security aggregate fail; focusedsecurity causal6PASS не отменяет повтора. Отдельный новый approved/retry structural conflict fixture PASS. Нужны trace/outcome каждого actor, user-visible conflict/retry contract; no demonstrated foreign-access claim.')}
entries=[]
for index,p in enumerate(fresh['suite-results.json']['problems']):
    status,key,reason=CAUSE.get(p['id'],('UNRESOLVED_CURRENT_FAILURE_CAUSAL_REVIEW_REQUIRED',None,
        'Старый group label не является доказательством: нужен точный assertion, актуальный payload/fixture и причинный replay. Не classified harmless и не автоматически genuineAPPbug.'))
    historical=old.get(p['id'],{})
    entries.append({**p,'entry':index+1,'status':status,'reason':reason,
        'old_label_hint_only':historical.get('reason_code',historical.get('classification',historical.get('group'))),
        'old_verdict_adopted':False,'evidence':'domain-results.json:'+key if key else ('full-results.json; source review; security-causal.json' if 'ConcurrencyTests' in p['id'] else 'full-results.json; source review'),
        'observation':observations.get(key) if key else None})
result={'metadata':{'role':'django-reviewer','snapshot':'current V3/dirty WORKTREE','production':'NOT_CONTACTED','source':'fresh /root full-results.json','entries':len(entries),'unique_ids':len({p['id'] for p in entries})},
        'entries':entries,'note':'Every unresolved current failure remains visible. SIGNED_CANDIDATE35/OPTIONAL28 historical buckets are not blanket harmless.'}
(OUT/'domain-failure-classification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result['metadata']))
