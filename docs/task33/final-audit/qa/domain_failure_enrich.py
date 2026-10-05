import json,collections
from pathlib import Path
ROOT=Path('/mnt/c/kidsmap');OUT=ROOT/'docs/task33/final-audit'
traces=json.loads(Path('/root/task33-evidence/final-audit-domain-cross-stage-20261004/failure-source-traces.json').read_text())
byid=collections.defaultdict(list)
for t in traces:byid[t['id']].append(t)
report=json.loads((OUT/'domain-failure-classification.json').read_text());seen=collections.Counter()
for entry in report['entries']:
    id=entry['id'];rows=byid[id]
    if not rows:continue
    offset=seen[id];seen[id]+=1;t=rows[min(offset,len(rows)-1)]
    if t['old_hint'] not in ('OPTIONAL_MEDIA_COORDS_CONTACT','SIGNED_CANDIDATE'):
        continue
    entry['actual_first_assertion']=t['assert_source'];entry['observed_exception']=t['observed_exception'];entry['subtest']=t['subtest']
    entry['old_label_hint_only']=t['old_hint'];entry['confidence']='HIGH_SOURCE_AND_RETAINED_RUNTIME_FIRST_FAILURE'
    e=t['observed_exception'];statement=t['assert_source']['statement'] or '';name=id.split('.')[-1]
    if t['old_hint']=='OPTIONAL_MEDIA_COORDS_CONTACT':
        if ('!= 12' in e or '!= 11' in e or '!= 10' in e or 'data-total=' in statement or 'len(codes)' in statement or 'completed_count' in statement or 'required_count' in statement):
            cause='NUMERICAL_READINESS_EXPECTATION_DEBT'
            reason=f"Точный первый failure: {statement}; наблюдение {e}. place_readiness.py удаляет photo/coordinates из requirements, осталось10 вместо12. Для этого subtest счётчик старый; дальнейшие assertions отдельного requirement после него не выполнены и не объявлены проверенными."
        elif 'location' in name:
            cause='READINESS_LOCATION_SHAPE_EXPECTATION_DEBT';reason=f"Первый failure {statement}: {e}. Location requirements теперь region/address/phone/schedule безcoordinates; старое ожидаемое число/список содержитcoordinates."
        elif 'instagram_and_website' in name:
            cause='ACCEPTED_CONTACT_ALTERNATIVE_EXPECTATION_DEBT';reason='Тест требует phone issue даже при website; D06/08 допускает business phone/WhatsApp/website. Текущий _check_phone использует other_contact; observe issues[] против старого[phone]. Не означает принятие Instagram как достаточного контакта.'
        elif 'publish_is_refused' in name:
            cause='MULTIPLE_SOURCE_PROTOCOL_AND_COUNT_MISMATCH';reason='Первый assertion требует summary9из12; реально missing signed token плюс текущие9из10 иphone issue. Это точная совместная причина, не доказательство правильного currentprotocol publish UX.'
        else:
            cause='OPTIONAL_FIELD_EXPECTATION_MISMATCH'
            reason=f"Первый failure {statement}: {e}. Фото/координаты по08 не обязательны. Конкретная проверка требует прежнюю ошибку/issue/required field; другие действительные errors (price/subcategory/region) остаются и не отменены этим диагнозом."
        entry['status']='SOURCE_DIAGNOSED_EXPECTATION_DEBT_PARTIAL_FEATURE_COVERAGE';entry['reason']=reason
        entry['contract_refs']=['docs/task33/decisions.md:D06','docs/task33/prompts/08.md:R08-05','src/catalog/services/place_readiness.py:PLACE_READINESS_REQUIREMENTS/evaluate_readiness']
    else:
        if 'Publication source token missing/invalid' in e:
            cause='EXPLICIT_SIGNED_TOKEN_FIRST_FAILURE';reason=f"Fresh trace прямо показывает missing/invalid publication token перед ожидаемой проверкой: {statement}. source_version требует signed source/schema/snapshot/dependencies. Старый helper/payload token не передаёт. Feature за этой границей не проверена этим failedcase; validtoken replay NOT_RUN."
        elif 'can_save_an_empty_new_place' in name:
            cause='NO_INVENTED_DRAFT_NAME_EXPECTATION';reason='Сохранение302 произошло, firstfailure ожидает invented name Черновикбезназвания, actual name пустой.09 допускает незавершённый draft без выдуманного name. Остальные assertions после старого name lookup не выполнены.'
        elif name=='test_place_make_published_action':
            cause='OBSOLETE_MOCK_AND_INCOMPLETE_PUBLICATION_FIXTURE';reason='mark_published теперь вызывает publication.publish/evaluate_place_readiness, не patched place_quality_check. create_quality_place без with_subcategory/with_pricing_plan не ready; второйPlace остаётсяdraft. ПервыйrealreadyPlace проходит. Signedtoken label здесь неверен: bulk action не formtoken.'
        elif 'manager_can_create_place' in name or 'can_save_and_exit_create' in name or 'manager_can_save_incomplete' in name or 'manager_create_place' in name:
            cause='CANDIDATE_FIELDS_LOOKED_UP_IN_LIVE_ROW';reason=f"POST сначалаredirected, firstfailure ищет submittedname_az/name_ru вPlace approved projection: {statement}. create_from_form создаёт base(name/category/owner,draft), переводы/остальное publication.propose хранитвcandidate. Source показывает другуюпроекцию; candidatecontent именноэтогоfixture runtimeнепроверен, неclaimполностьюharmless."
        elif name in {'test_edit_preserves_translations_legacy_and_staff_data','test_failed_resubmission_does_not_save_changes_or_delete_photo'}:
            cause='UNAPPROVED_CREATE_TARIFF_EXPECTATION';reason=f"Fixture create() не выполняетreview; create_from_form кладётpricing вcandidate. Первыйfailure ожидаетужеlive PricingPlan: {statement}; observe{e}. Поэтому coreedit/rollbackfeature не достигнута. Validapprovedsetup replay NOT_RUN."
        elif name in {'test_cannot_set_staff_fields','test_on_request_can_be_submitted_and_becomes_visible_after_approval','test_owner_can_resubmit_published_place_for_moderation'}:
            cause='PUBLICATION_CURRENT_CANDIDATE_STATE_EXPECTATION';reason=f"Firstfailure {statement}: {e}. Pending находитсявVolunteerPlaceRevision; newPlacebase остаётсяdraft, publishedcurrent не заменяетсяpending. Sourcepublication.propose поддерживает current/candidate. Массовыеполя/staffsecurityдальнейшихassertions этимfailureнепроверены."
        elif name=='test_staff_with_change_place_permission_can_publish_after_approval':
            cause='CLAIM_NOT_PUBLICATION_EXPECTATION';reason='Старый сценарий ожидаетis_active послеownershipapproval; _decide_claim/_change_owner меняет управление, не publication. Тот же boundary воспроизведён отдельным legacy_claimprobe. Реальныйpublishдляэтойstaffроли не доказан этимcase.'
        elif name=='test_owner_edit_creates_place_change_audit':
            cause='LEGACY_AUDIT_READER_NOT_UPDATED_OR_REQUEST_BLOCKED';reason='Наблюдениеaudits0; currentcontroller сохраняет publicationcandidate, прежняя ветка legacyPlaceChangeAudit послеsave отсутствует. Старый payloadбезtoken такжеможетостанавливатьsave. Требуетсяtokenreplay/сопоставлениеrevisionauditсобещанием; sourceчастичный, возможныйauditUXдолг, неharmlessverdict.'
        else:
            cause='SOURCE_TOKEN_OR_APPROVED_PROJECTION_FEATURE_PREEMPTION';reason=f"Точныйfailure {statement}: {e}. Этотстарыйedit/savepayload сформированбезpublicationtoken (helper/data); source_version обязателен. Кромеэтогоname/coords/photo изменяютсяcandidate, невlive; schedule/amount отдельныйexplicitpath. Corefeatureварианта{ name } сvalidtoken/approveнепроверенаэтимfailure, требуетсяcausalreplay."
        entry['status']='SOURCE_DIAGNOSED_PROTOCOL_OR_PROJECTION_PARTIAL_CAUSAL';entry['reason']=reason
        entry['contract_refs']=['src/catalog/services/publication_forms.py:source_version/create_from_form/save_form','src/catalog/services/publication.py:propose/review','docs/task33/prompts/08.md']
    entry['cause']=cause;entry['remaining_boundary']='Source diagnosis plus retained firstfailure; no assertion weakened, no complete unique-feature currentpayload replay except three separately recorded admin probes.'
report['diagnosed_signed_optional_entries']=sum(bool(e.get('cause')) for e in report['entries'])
(OUT/'domain-failure-classification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'signed_optional_entries':report['diagnosed_signed_optional_entries'],'causes':dict(collections.Counter(e.get('cause','OTHER') for e in report['entries']))}))
