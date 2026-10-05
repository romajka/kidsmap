"""Map only executed rendered scopes, never all acceptance from context counts."""
import json,collections
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]
browser=json.loads((OUT/'domain-browser-evidence.json').read_text(encoding='utf-8'))
spec={
'R12-10':('r1',['network_owner','selected_manager','all_network'],['keyboard_focus','organization_last_tab_keyboard','future_branch_acl'],'Не проверены каждым locale/width browser stale join и savefailure; конкретные backend stale cases указаны отдельно.'),
'R13-11':('r1',['standalone_owner'],['keyboard_focus'],'Renderedcontinuousforms/focus есть; весь shared volunteer wizard regression/всеformerrors не доказаны screenshot matrix.'),
'R14-11':('targeted',['program'],['focus','tab','impact_confirmation_required_native_POST','program_native_owner_edit_candidate_only','program_stale_edit_denied','program_manage_POST_scope_denied_valid_CSRF'],'Только390/1280 ×AZRUEN, не7widths; long/mobiletariffinteractivecoverage отдельнонеполная. Viewtransitionpageerror сохраняется.'),
'R15-11':('event',['admin','admin_add'],['focus','tab','admin_actual_publication','admin_actual_save_online'],'Eventadmin7widths; R1 moderatorreadalsoесть. Это не всеOrg/Activity/Group admineditflows поtablet/mobile. Targetedpageerror неignored.'),
'R16-11':('r1',['volunteer','moderator'],['keyboard_focus'],'Render/focus основных hubscreens, не каждое diff/error/return/conflict состояние.'),
'R18-11':('targeted',['organization','activity'],['focus','tab','pending_program_not_public','private_entity_closed'],'Org/Activity18contexts390/1280; R1Place7widths. Initialapproveddisplayfixtures ORM, неполныйcreation→approvalUI. InvalidStateErrorstrictgateFAIL.'),
'R19-11':('r1',['catalog'],['public_focus','public_tab'],'Catalog21contexts; resize/back/locale everyfiltercombination неexhaustive. Rootquery/timecomparison отдельнонеравноускорению.'),
'R20-11':('r1',['map'],['rendered_map_open','rendered_map_close','local_map_api','public_focus','public_tab'],'Localpopup/API/keyboardпроверены; внешниеMapsstubsNOTrealprovider. Полныйunavailableprovider/failureinteraction отдельнонеподтверждён.'),
'R25-10':('specialist',['public','person','claims','certificates','invitations','org','review'],['focus','tab','real_private_certificate_upload','invalid_upload_rendered_error_preserves_state','organization_invitation_is_pending','person_explicit_confirmation','dedicated_claim_review_verifies_person','approved_person_optin_public'],'7widths×AZRUEN иконкретныеactions; всеcurrent/historicaltransferstates/browserlongtextnotexhaustive, nativeconversionотдельно.'),
'R27-08':('event',['calendar','list'],['native_day_keyboard_focus','selected_mobile_day_and_multiday','focus','tab'],'Mobile/keyboard7widths; longtitle robustness вboundedfixture, не произвольныеtexts.'),
'R27-11':('event',['create','edit','calendar','list','admin','admin_add','online','cancelled','rescheduled'],['real_online_draft_save','admin_actual_publication','owner_previously_approved_draft_ordinary_edit','published_admin_ordinary_edit_precision','stale_edit_denied','mode_keeps_filters_whole_month'],'27UI/HTTPflowspassed; approveddesignjudgement bounded, exhaustiveworkflows/realexternalsnotverified.')}
req=json.loads((OUT/'requirements-review.json').read_text(encoding='utf-8'))
families={f['family']:f for f in browser['families']}
for r in req['requirements']:
    if r['id'] not in spec:continue
    family,screens,names,remaining=spec[r['id']];f=families[family]
    selected=[c for c in f['checks'] if c.get('check') in names]
    found={c['check'] for c in selected}
    if found!=set(names):raise ValueError((r['id'],set(names)-found))
    r['status']='PARTIAL_FRESH_RENDERED_EVIDENCE_STRICT_BROWSER_GATE_FAIL'
    r['evidence'].append({'kind':'CURRENT_INDEPENDENT_BROWSER_EXECUTION_ATTRIBUTED','executor':'/root/stage26_public',
        'ref':'domain-browser-evidence.json; browser-results.json','family':family,
        'screens':{s:f['screens'][s] for s in screens},'exact_check_ids':names,
        'selected_check_count':len(selected),'all_selected_passed':all(c.get('pass',False) for c in selected),
        'strict_browser_gate':'FAIL','unexpected_pageerror':'InvalidStateError ViewTransition in targeted family, causalphaseprobe pending'})
    r['covered_subclauses']=[{'scope':n,'status':'PASSED_FRESH_RENDERED_ATTRIBUTED'} for n in names]
    r['uncovered_subclauses']=[remaining]
    r['limitations']=[remaining,'1724/1724 business/DOM checks do not cancel strictbrowserFAIL1pageerror; 816contexts boundedcurrentV3.']
req['status_counts']=dict(collections.Counter(r['status'] for r in req['requirements']))
(OUT/'requirements-review.json').write_text(json.dumps(req,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
stages=json.loads((OUT/'stage-map.json').read_text(encoding='utf-8'))
for stage in stages['stages']:
    scopes=[{'requirement':id,'family':s[0],'screens':s[1],'exact_check_ids':s[2]} for id,s in spec.items() if int(id[1:3])==stage['stage']]
    if scopes:stage['rendered_evidence']={'ref':'domain-browser-evidence.json; browser-results.json','scopes':scopes,'gate':'FAIL pageerror retained'}
    if stage['stage'] in {14,19}:stage['own_probe_ids']=['domain_probe.DomainCrossStageTests.test_new_standalone_writer_offer_disappears_on_category_age','domain_probe.DomainCrossStageTests.test_program_category_writer_works_but_subcategory_has_no_writer']
    if stage['stage']==28:
        stage['source_refs']+=['docs/task33/final-audit/full-results.json','docs/task33/final-audit/browser-results.json','docs/task33/final-audit/release-gates.json','docs/task33/final-audit/security-causal.json','docs/task33/final-audit/image-full-comparison.json']
        stage['current_runtime_gates']={'host_full':'1817/109F11E;Task33579/580','native':'PASS98tables/25public+2private/exact2794reader/cleanup',
            'browser':'816contexts/1724businessDOMPASS;strictFAIL1targetedInvalidStateError','image_full':'Initial125F28E withharnessstubs/pathfaults; corrected29preflightPASS attributedrelease; currentrepeatRUNNING (no prematurePASS)',
            'production':'NOT_CONTACTED;externalmanualgatesopen'}
(OUT/'stage-map.json').write_text(json.dumps(stages,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'browser_requirements':len(spec),'exact_assertion_rows':sum(len(r.get('covered_subclauses',[])) for r in req['requirements']),'status_counts':req['status_counts']}))
