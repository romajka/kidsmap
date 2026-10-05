import json,collections
from pathlib import Path
ROOT=Path('/mnt/c/kidsmap');OUT=ROOT/'docs/task33/final-audit'
traces=json.loads(Path('/root/task33-evidence/final-audit-domain-cross-stage-20261004/failure-source-traces.json').read_text())
byid=collections.defaultdict(list)
for t in traces:byid[t['id']].append(t)
data=json.loads((OUT/'domain-failure-classification.json').read_text());seen=collections.Counter()
GROUP={
'EVENT_ORGANIZER_INTERVAL_CONTRACT':('SOURCE_DIAGNOSED_INVALID_EVENT_PUBLICATION_FIXTURE','src/catalog/services/event_domain.py:_organizer/_validate/publish_event','Fixture Event не имеет конкретного Org/verifiedperson organizer и точного interval. Current bulk использует publish_event и не применяет bypass quality mock. Originaldraft сохраняется; это accepted26 guard, не signedtoken issue.'),
'REVIEW_REVISION_PROTOCOL':('SOURCE_DIAGNOSED_REMOVED_LEGACY_REVIEW_MODERATION_ENTRY','src/catalog/domain_admin/review_versions.py:VersionedReviewAdminMixin.get_actions/approve_view','Старый action approve/hide/reject или прямойlegacyURL удалён/403; currentversionedworkflowlink требуетcandidate revision. Старыйhead не меняется, рейтинг0 ожидаем дляpending. Это не проверка работоспособности новогоaction: её выполняют Task33 typedreview cases.'),
'CURRENT_ADMIN_HIERARCHY':('SOURCE_DIAGNOSED_NAVIGATION_EXPECTATION_CHANGE','src/catalog/domain_admin/business.py; docs/task33/prompts/15.md','Assertion запрещаетвидимый navigation Группы;15требуетgroups/pricing внутриActivity и регистрация hierarchy проверена новымtest. Точное место списка/UX не принято однимsourceвердиктом.'),
'EVENT_ADMIN_LEGACY_PAYLOAD':('SOURCE_DIAGNOSED_REQUIRED_FORMAT_PAYLOAD_DEBT','src/catalog/domain_admin/place.py:EventAdminForm; docs/task33/reports/28-legacy-draft-diagnostic.json','Старый _admin_event_change_payload не передаёт required event_format. Root causal completepayload replay даёт302 дляdraft послеV3 precision fix; publishfixture дополнительно должен иметьвалидныйorganizer/dates. First200 сампо себе неfullproofpublishflow.'),
'CREATE_CAP_REMOVED':('SOURCE_DIAGNOSED_ACCEPTED_CREATE_LIMIT_REMOVAL','src/catalog/services/organization_ownership.py:create_place; docs/task33/prompts/06.md','06убираетfixed10limit. OriginalassertищетLimitdolub,11-еPlaceдопускается; конкретныйpositive новыйcase test_eleventh_place_form_is_available rootPASS.'),
'CONTINUOUS_FORM':('SOURCE_DIAGNOSED_SUPERSEDED_WIZARD_SELECTOR_FIRST_FAILURE','src/catalog/templates/pages/owner_place_create.html; docs/task33/prompts/13.md','Firstassert требуетpw-step/sidebar/7steps/permanent_place_wizard.js.13заменилowner flow наcontinuous4sections/отдельныйJS. Последующиеуникальныеphoto/map/pricingassertions заэтимfirstfailure не выполнены; shared volunteer selectors должныпроверятьсяотдельно.'),
'BUSINESS_REVIEW_DENIED':('SOURCE_DIAGNOSED_ACCEPTED_BUSINESS_MODERATION_DENIAL','src/catalog/services/business_team.py; src/catalog/services/review_versions.py:business_can_respond/moderate_candidate','Старый бизнесgrant place.reviews.moderate/ownerapprove запрещёнD02/22. Currentreply/reporttargetscopeразрешён отдельно; old403/absence не означаетпотерюнужногобизнесуreply/report.'),
'EVENT_IMMUTABLE_SNAPSHOT':('SOURCE_DIAGNOSED_LIVE_ADDRESS_MUTATED_AFTER_SNAPSHOT','src/catalog/services/event_domain.py:capture_venue_snapshot; src/catalog/models/event.py','Fixture меняет Event.address послесозданияapproved snapshot; public26читаетimmutablevenue_snapshot, не новый address. Localized snapshot сама должнапроверятьсяотдельно; старыймутабельныйsourceнеисточникпрошлогоEvent.'),
'EVENT_CALENDAR_FILTER_CONTRACT':('SOURCE_DIAGNOSED_ACCEPTED_FILTERS_PRESENT','src/catalog/services/event_calendar.py; docs/task33/prompts/27.md','27требуетq/category/age/format preserving list/calendar. OldassertNotContainsname=q прямо противоположен принятому27.'),
'D08_SPECIALIST_PERSON_CONSENT':('SOURCE_DIAGNOSED_PERSON_AND_CERTIFICATE_CONSENT_FIXTURE','src/catalog/services/specialist_domain.py:propose_person/review_claim; src/catalog/services/specialist_documents.py:is_person/is_public_document','Авторпредложениянеownerperson; oldqueryowner=self.owner не находитperson. Legacy diploma is_published+approved безverifiedperson/optedinby/at неpubliccertificate. Нужныclaim/личноеconsent; старыйmanagementдоступбизнесанеpersonpermission.'),
'SUPERSEDED QUERY BUDGET':('OBSERVED_FIXED_QUERY_OVERHEAD_INCREASE_NOT_DISMISSED','src/catalog/services/map_payload.py; full-results.json:stage19-query-comparison.json','Actual9queries вместоold4. Это реальноеувеличениеfixedoverhead наэтомfixture; новоеmatched/venuepresentationдобавляетработу, ноaccepted4budgetнеустановлен. Scalingtestsиотдельный41→8comparison неотменяютэтотfailure. Timing/perfacceptanceчастичная.'),
'LOCATION_FIXTURE':('SOURCE_DIAGNOSED_GEOGRAPHY_FIXTURE_OR_ERROR_FIELD_CHANGE','src/catalog/services/location_assignment.py; src/catalog/forms.py','Retainedtrace даёт actualcoordinate/region mismatch либо inferredregion либо errorattachedlatвместоlng. Defaultdata имеетBaku40.4/49.8; testcaseoutsideGanjaсохраняетих. Exactsubtest boundary ниже; нельзясчитатьвсягеографияправильной по одномуlabel.'),
'INVALID GEOGRAPHY FIXTURE / OLD QUERY BUDGET':('SOURCE_DIAGNOSED_CANONICAL_DISTRICT_FIXTURE_PARTIAL','src/catalog/testcases/utils.py:create_quality_place; src/catalog/services/location_assignment.py','Fixtureписалdesired district приодинаковыхBakucoords; normalSaveканонизирует district. Districtquery проверяетstoredcanonicalcode. Реальныеfullcombinedsearchтрасы нужны отдельно; не blanketobsolete.'),
'INVALID_OLD_DESCRIPTION_ASSERTION':('SOURCE_DIAGNOSED_FIRST_DESCRIPTION_EXPECTATION_MISMATCH','src/catalog/testcases/owner.py; src/catalog/forms.py','Firstassert требуетdescription_azerror, ноfixtureимеетdescription_az; отсутствующийname_az даётдругуюошибку. Точноеobservedexception сохранено; name-requiredpositive/negativeTask33source проверяется отдельно.')}
for e in data['entries']:
    if e.get('cause'):continue
    rows=byid[e['id']]
    if not rows:continue
    offset=seen[e['id']];seen[e['id']]+=1;t=rows[min(offset,len(rows)-1)]
    e['actual_first_assertion']=t['assert_source'];e['observed_exception']=t['observed_exception'];e['subtest']=t['subtest'];e['old_label_hint_only']=t['old_hint']
    if e['status'].startswith('CONFIRMED') or 'ConcurrencyTests' in e['id'] or 'failed_publish_keeps' in e['id']:continue
    name=e['id'].split('.')[-1];group=t['old_hint']
    if group in GROUP:status,source,reason=GROUP[group]
    elif group=='SUPERSEDED PUBLIC PRESENTATION':
        status='PARTIAL_PRESENTATION_CHANGE_OR_REGRESSION_REQUIRES_CURRENT_UX_REPLAY';source='src/catalog/templates/catalog/includes/place_card.html; src/catalog/templates/catalog/place_detail.html'
        reason='Exactfirstassert требуетadultlabel/ageстроку. ВsharedcardкороткийlabelВзрослые, вlegacydetailусловныйadultblockсохранён. Поканеустановлено, почемуэтотfixtureдоходитдоинойветки/форматаage: возможенUXregression, неавтоматическиacceptedpresentationdebt.'
    elif group=='SUPERSEDED CONTRACT OR INVALID FIXTURE':
        source='src/catalog/services/public_filter_options.py; src/catalog/services/public_languages.py; src/catalog/services/map_payload.py'
        if 'price_filter' in name or 'localized_strings' in name:
            status='SOURCE_DIAGNOSED_REMOVED_BUDGET_CONTROLS';reason='19удаляетbudgetcontrols/pricefilter. Pricequeryignored, старыйassertожидаетфильтрацию/обещаниеbudget. Actualfirstfailure сохранён; localesвдругихстроках не покрыты.'
        elif 'sitemap_includes_all_languages' in name:
            status='SOURCE_DIAGNOSED_INCOMPLETE_TRANSLATION_HREFLANG';reason='FixtureнеимеетполнойRU/ENdescription.21публикуетalternativesтолькосодержательныхпереводов; стараяall-languagesexpectedRUlinkотсутствует.'
        elif 'disable_anonymous_flag' in name:
            status='SOURCE_DIAGNOSED_PRESERVED_ANONYMITY_POLICY';reason='LegacyReviewis_anonymous=Trueсохранён, старыйassertFalseтребуетотменуprivacyflag.22сохраняетисторию/анонимизацию,непереключаетpolicy.'
        elif 'map_serialization_includes_card_fields' in name or 'map_search_text' in name:
            status='SOURCE_DIAGNOSED_NEW_VENUE_MEMBERS_PAYLOAD_SHAPE';reason='20payloadдобавляетvenuekey/members/matchedoffers, searchtextнаmemberа невtop-level. Старыйdictcomparison/lookupsearch_textнеподдерживаетnestedshape. MapUIconsumptionтребуетотдельногобраузера.'
        elif 'hero_statistics' in name:
            status='SOURCE_DIAGNOSED_TEMPLATE_EXPRESSION_EXPECTATION';reason='Assertищетliteraltemplateexpressionmap_places|length; currentcountсчитаетbusinessmembersвsharedvenue, нечислоточек. Неявляетсяruntimeпроверкойexactdisplaycounts.'
        else:
            status='PARTIAL_SPECIFIC_FIRST_FAILURE_SOURCE_BOUNDARY_UNRESOLVED';reason='Точноенаблюдение ниже. Несколькоdistrict/count/SEOfixturesиспользуютодноизвестноеBakuместо сдругимlabel иполучаютcanonicaldistrict; metadata21учитываетsubstantivetranslation. ДляэтогоIDбезcurrentfixture replay причинатолькочастичноустановлена, possibleUX/querydefectнеисключён.'
    else:continue
    e['status']=status;e['reason']=reason;e['contract_refs']=[source];e['confidence']='SOURCE_REVIEW_PLUS_FRESH_FIRST_FAILURE; FULL_FEATURE_REPLAY_NOT_RUN'
    e['remaining_boundary']='Firstassert and source cause identified. No wholesale acceptance, no oldassertion change, possible feature-specific gaps retained.'
data['unresolved_presentation_or_query_ids']=[e['id'] for e in data['entries'] if e['status'].startswith('PARTIAL_')]
(OUT/'domain-failure-classification.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'entries':len(data['entries']),'actual_first_assertion_entries':sum('actual_first_assertion' in e for e in data['entries']),'statuses':dict(collections.Counter(e['status'] for e in data['entries']))}))
