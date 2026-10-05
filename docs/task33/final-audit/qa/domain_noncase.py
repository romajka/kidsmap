"""Non-test scope evidence and precise pending clauses, never browser-by-source PASS."""
NONCASE={
'R05-11':('PARTIAL_ROLE_REVIEW_ATTRIBUTED','domain-source.json; domain-review.md; recovery-results.json','Итоговый source/schema прочитан canonical django ролью; root native current167/0. Прежний database review мой собственный, поэтому не independent self-review.'),
'R06-11':('PARTIAL_CURRENT_SECURITY_ROLE_EVIDENCE','security-results.json; security-causal.json; security-review.md','Независимый security исполнитель выполнил локальные ACL/concurrency. Aggregate ownership race FAILED, focused causal6PASS не закрывает gate.'),
'R08-12':('WORKFLOW_COMPLIANCE_SOURCE_AND_SNAPSHOT','entry.json; domain-results.json; full-results.json','APP assertions не менялись в этом аудите; новый внешний adapter отдельный. Старые109F11E сохранены; unchanged source согласуется с V3.'),
'R12-02':('SOURCE_REVIEWED_RENDERED_BOUNDARY_PENDING','src/catalog/templates/pages/organization_workspace.html:10','Фактический include pages/includes/account_navigation.html. Source подтверждает reuse, не focus/render всех screens.'),
'R13-09':('SOURCE_CONTEXT_USER_TEXT_NOT_EXHAUSTIVELY_VERIFIED','src/catalog/templates/pages/owner_place_create.html; src/catalog/forms.py','User labels и wizard sections inspected. Полный AZ/RU/EN rendered поиск всех technical labels в данном review отдельно не выполнен; внутренние field names не равны видимому тексту.'),
'R15-01':('PARTIAL_SOURCE_EDITOR_REUSE','src/catalog/domain_admin/place.py; src/catalog/domain_admin/business.py','Admin классы и общие components сохранены; проверка всех notification/photo/location/token consumers и визуального соответствия в browser scope.'),
'R15-03':('PARTIAL_SOURCE_STRUCTURE_PRESENTATION','src/catalog/domain_admin/place.py; src/catalog/models/catalog_structure.py','Place address/hours отдельно от Activity/Group schedule/pricing; standalone nullableOrg. Пользовательская ясность всех форм требует rendered review.'),
'R15-05':('SOURCE_REVIEWED_EXPLICIT_PREVIEW_LANGUAGE_CONTROL','src/catalog/templates/admin/catalog/place/form/section_verification.html:6; static/admin/js/kidsmap_place_form.js:1429','ФактическийselectAZ/RU/EN, refreshPreviewчитаетid_name_ выбранногоязыка. Templateявно сообщает: Пустые переводы не создаются автоматически. Sourcepositiveподтверждён, nativebrowserselectchangepreviewтекстнепроверенвданномreview.'),
'R21-06':('SOURCE_AND_WORKFLOW_PRODUCTION_NOT_CONTACTED','domain-review.md; src/catalog/services/publication.py','Во время аудита production команды не запускались. Текущие publication actions не вызывают state-writing SEO audit/fix. Поведение реально deployed production UNKNOWN.'),
'R25-01':('HISTORICAL_APPROVAL_NOT_CURRENT_UI_PASS','docs/task33/reports/25.md; docs/task33/implementation-status.md','Принятие Specialist макетов историческое prerequisite; не доказательство текущей rendered реализации. Production не запускался.'),
'R28-01':('PARTIAL_CURRENT_ACCEPTANCE_REVIEW','stage-map.json; requirements-review.json; full-results.json','28prompts/306literal clauses, currentsource и fresh IDs сопоставлены. Taxonomy/race/legacy/image gaps не скрыты старымPASS.'),
'R28-02':('PARTIAL_CURRENT_MULTI_ROLE_EVIDENCE','full-results.json; security-results.json; recovery-results.json; browser-review.md','Fresh full/native/security/browser roles, источник каждого результата указан. Full109F11E,Task33579/580; rendered breadth не означает все возможные действия.'),
'R28-03':('PARTIAL_PRECISION_FIX_REVERIFIED_NEW_GAPS_OPEN','docs/task33/reports/28-precision-results.json; full-results.json','V3 admin/owner minute precision5casePASS и frozenruntime evidence. Новые comprehensiveAUDITfindings не исправлялись: пользователь разрешил аудит, не APP fixes.'),
'R28-04':('PROVED_LOCAL_SYNTHETIC_NATIVE_RECOVERY_ATTRIBUTED','recovery-results.json','Root fresh conversion/reconciliation/native restore с post-switch R1/R2, private docs/outbox.98tables/25public+2private/exact2794-reader/cleanupPASS. Реальные production records NOT_TESTED.'),
'R28-05':('PARTIAL_EXACT_PACKAGE_EXTERNAL_GATES_OPEN','release-gates.json; image-full-results.json; recovery-results.json','Exact V3 image/archive/schema/media/cohort validation и writes-off recovery локально. Fresh whole-image additionalfailures остаются; operationalprivatevolume/pilot/providerNOT_RUN.'),
'R28-06':('DOCUMENTED_EXTERNAL_NOT_RUN','release-gates.json; domain-review.md','OAuth/Maps/SMTP real providers, production pilot/cron/private media transition NOT_RUN; stubs не выданы за externalsuccess.'),
'R28-09':('WORKFLOW_COMPLIANCE_PRODUCTION_NOT_CONTACTED','PLAN.md; domain-results.json; release-gates.json','Production deploy отдельное разрешение. В этом аудите не выполнялся.'),
'R28-10':('PARTIAL_FRESH_CHECKS_WITH_FAILED_GATES','full-results.json; recovery-results.json; security-results.json; browser-review.md','Current migrations/full/concurrency/native/browser/SEO/private/outbox evidence attributed. Full неgreen, race нестабилен, querycount/time выводы раздельны; performance productionNOT_RUN.'),
'R28-11':('PARTIAL_PRECISE_ROLE_ATTRIBUTION','domain-review.md; security-review.md; release-gates.json','Canonical sequential role identities обозначены. Мой старыйDB авторство не independent selfreview; security послеrelease sameexecutor не independentreview ownpackage. Root nativefresh execution отдельно.')}
BROWSER={
'R12-10':'AZ/RU/EN × обязательные widths, focus/navigation, stale join, save failure, selected manager',
'R13-11':'Widths/keyboard/errors и shared volunteer wizard regression',
'R14-11':'Program/group long titles и mobile tariffs AZ/RU/EN',
'R15-11':'Admin tablet/mobile/keyboard/CSS/JS404',
'R16-11':'Volunteer hub diff/preview/error/focus каждого relevant state',
'R18-11':'Org/Activity/Place accepted design, languages,widths,keyboard,longcontent',
'R19-11':'Filter state resize/back/locale; root exactquery/timecomparison available отдельно',
'R20-11':'Map popup keyboard/resize/console и unavailablemap list',
'R25-10':'Person/invitation/claim/certificates languages/mobile/focus/errors плюс transfer',
'R27-08':'Calendar keyboard/mobile long titles',
'R27-11':'Event admin/owner/public integration + approved design languages'}
for id,clause in BROWSER.items():
    NONCASE[id]=('PENDING_EXACT_RENDERED_ROLE_MAPPING','browser-review.md; browser-plan.md; browser-targeted-attempts.json',
        'Backend/source не доказывает именно: '+clause+'. Текущая browser роль выполняет отдельную фактическую матрицу; сопоставить только завершённые contexts/actions, не blanket screenshotPASS.')
