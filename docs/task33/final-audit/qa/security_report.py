"""Final audit report from actual fresh evidence; historical results stay historical."""
import json
import hashlib
import sys
import importlib.metadata
from pathlib import Path

root=Path('/mnt/c/kidsmap/docs/task33');audit=root/'final-audit'
def read(name):return json.loads((audit/name).read_text())
selected=read('security-results.json');supplement=read('security-supplement.json');causal=read('security-causal.json')
source=read('security-source.json');extra=read('security-supplement-source.json')
image=read('security-image.json');static=read('security-static.json');compose=read('security-compose.json')
comparison=read('image-full-comparison.json')
corrected=comparison.get('image_corrected')
full_image_summary=(f"Corrected exact-image: {corrected['tests']} tests, {corrected['failures']}F/{corrected['errors']}E, Task33 {corrected['task33_passed']}/{corrected['task33_total']}; cleanup {corrected['cleanup']}. Image-only {len(corrected['image_only'])}, host-only {len(corrected['host_only'])}, common {corrected['common_problem_ids']}. Initial125F28E preserved; see image-full-comparison.json; common IDs are not harmless-baseline proof."
                    if corrected else 'Initial exact-image1817:125F28E, Task33548/580; corrected wrapper preflight29/29PASS; corrected full repeat RUNNING. Actual trace groups31 socket-contract+1 readonly/tmp+1 excluded taxonomy+1 unresolved rating. Initial attempt preserved.')
suite=selected['suite-results.json'];failed='catalog.testcases.test_task33_ownership.OwnershipConcurrencyTests.test_transfer_racing_confirmation_never_grants_stale_network_right'
assert suite['tests_run']==260 and suite['failures']==1 and suite['errors']==suite['skipped']==0
assert [p['id'] for p in suite['problems']]==[failed]
assert len(set(suite['executed_ids']))==260
for evidence,count in ((selected,260),(supplement,12),(causal,6)):
    assert evidence['suite-results.json']['tests_run']==count
    assert evidence['run.json']['cleanup']=='PASS' and evidence['run.json']['run_root_removed'] and evidence['run.json']['socket_root_removed']
    assert evidence['isolation.json']['network_guard'] and evidence['isolation.json']['libpq_guard'] and not evidence['isolation.json']['external_credentials_present']
    assert evidence['migrations.json']=={'applied_count':167,'unapplied_count':0}
    assert all(c['status']=='PASS' and c['exit']==0 for c in evidence['checks.json'])
assert supplement['suite-results.json']['status']==causal['suite-results.json']['status']=='PASS'
assert source['all_matches'] and len(source['files'])==50 and extra['all_matches'] and extra['file_count']==8
assert image['status']==static['status']==compose['status']=='PASS'
assert image['artifact_identity']==static['artifact_identity']==source['artifact_identity']
assert image['actual_context_file_count']==image['actual_image_file_count']==2794
assert static['file_count']==9305
recovery=json.loads((audit/'recovery-results.json').read_text());native=recovery['r2-rehearsal.json']
assert recovery['run.json']['status']=='PASS' and recovery['run.json']['cleanup']=='PASS'
assert native['tables_compared_count']==98 and native['media_files_compared']==25 and native['private_files_compared']==2
assert native['source_and_restore_row_digests_equal'] and native['media_byte_digests_equal'] and native['private_media_digests_equal']
assert native['compatible_standby_read']['artifact_identity']==image['artifact_identity']
assert native['compatible_standby_read']['read_only_database']
candidate=json.loads((root/'reports/28-artifact.json').read_text())
host_manifest=json.loads(Path(candidate['archive']).with_name('manifest.json').read_text())
assert hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest()==host_manifest['python_executable_sha256']
def normalized(values):return {name.lower().replace('_','-'):version for name,version in values}
host_deps=normalized((d.metadata['Name'],d.version) for d in importlib.metadata.distributions())
assert host_deps==normalized(host_manifest['dependencies'])
image_deps=normalized(image['metadata_runtime']['dependencies'])
delta=[{'package':p,'host_version':host_deps.get(p),'image_version':image_deps.get(p)}
       for p in sorted(set(host_deps)|set(image_deps)) if host_deps.get(p)!=image_deps.get(p)]
assert len(host_deps)==len(image_deps)==39 and delta==[{'package':'pip','host_version':'24.0','image_version':'25.0.1'}]
(audit/'security-runtime.json').write_text(json.dumps({'host_python':selected['isolation.json']['python'],
 'image_python':image['metadata_runtime']['python'],'host_dependency_count':len(host_deps),
 'image_dependency_count':len(image_deps),'changed_dependencies':delta,
 'root_full_image':comparison['corrected_full_status'],'full_image_summary':full_image_summary,
 'image_comparison':'image-full-comparison.json','production':'NOT_CONTACTED'},indent=2)+'\n')
(audit/'security-findings.json').write_text(json.dumps([{
 'id':'SEC-FA-01','severity':'P2','environment':'LOCAL dirty WORKTREE / disposable PostgreSQL',
 'kind':'schedule_sensitive_test_contract','title':'Конкурентный тест требует успеха безопасно отклонённой операции',
 'business_impact':'Шумящий gate затрудняет различение отказа с reload и нарушения ACL; подтверждённой выдачи устаревших прав нет.',
 'source':['src/catalog/testcases/test_task33_ownership.py:344','src/catalog/testcases/test_task33_ownership.py:362',
           'src/catalog/services/organization_ownership.py:39'],
 'reproduction':'Fresh selected260:259PASS/1F; fresh original5+forced structure-retry/ACL probe6/6PASS.',
 'confidence':'Высокая для контролируемого ordering guard; точный interleaving исходного scheduler не инструментирован.',
 'evidence':['security-results.json','security-causal.json','../reports/28-security-causal-classification.json'],
 'owner':'integration-reviewer + domain owner','next':'Будущий отдельный deterministic outcome contract test без ослабления ACL.',
 'application_changes':False,'assertion_changes':False,'production':'NOT_CONTACTED'}],ensure_ascii=False,indent=2)+'\n')
passed=set(suite['executed_ids'])-{failed}
controls=[]
def control(key,name,paths,methods):
    ids=[next(test for test in passed if test.endswith('.'+method)) for method in methods]
    controls.append({'id':key,'name':name,'status':'PASS_FRESH_SELECTED_CASES',
                     'source':paths,'executed_case_ids':ids,'evidence':'security-results.json',
                     'limit':'Конкретные негативные сценарии; не полное доказательство каждой ветви или всей production-системы.'})
control('SC01','Волонтёр не читает чужой кандидат и не получает бизнес-права',
 ['src/catalog/services/volunteer_places.py','src/catalog/volunteer_middleware.py'],
 ['test_volunteer_a_cannot_read_or_mutate_b_candidate_by_direct_id','test_informational_approval_without_business_grant'])
control('SC02','Владелец не утверждает собственный отзыв; чужие реакции и устаревшие версии отклоняются',
 ['src/catalog/services/review_use_cases.py','src/catalog/services/review_moderation.py'],
 ['test_owner_moderation_denied_but_reply_report_scoped','test_cross_parent_reaction_and_stale_revision_are_rejected'])
control('SC03','Рейтинг разных типов карточек не смешивается; скрытая карточка не принимает публичный отзыв',
 ['src/catalog/services/review_use_cases.py'],
 ['test_typed_rating_contributions_never_mix_and_pending_keeps_approved','test_hidden_target_rejects_public_submit_without_creating_review'])
control('SC04','Управляющий бизнесом не получает доступ к личным документам специалиста',
 ['src/catalog/services/specialist_documents.py:50','src/catalog/private_storage.py:13'],
 ['test_management_owner_cannot_read_or_choose_person_document_publication','test_live_place_owner_and_organization_grantee_cannot_read_person_documents'])
control('SC05','Удостоверение личности остаётся закрытым; сертификат требует согласия человека',
 ['src/catalog/services/specialist_documents.py:38'],
 ['test_identity_cannot_become_public_even_with_tampered_flags','test_approved_certificate_without_person_opt_in_stays_private'])
control('SC06','Отзыв прав и подмена document ID проверяются на сервере',
 ['src/catalog/services/specialist_documents.py:25'],
 ['test_dedicated_reviewer_permission_and_revocation','test_foreign_document_id_denied_to_verified_person'])
control('SC07','Личный файл не имеет общего URL; закрытый media-путь отклоняется',
 ['src/catalog/private_storage.py:17','src/catalog/views.py'],
 ['test_private_storage_has_no_public_url','test_document_bytes_are_outside_public_media','test_direct_legacy_media_download_is_denied'])
control('SC08','Владелец площадки не является организатором события',
 ['src/catalog/services/event_domain.py:44'],
 ['test_venue_legacy_owner_and_plain_staff_cannot_save_or_cancel_resolved_event','test_platform_publication_permission_never_grants_organizer_edit'])
control('SC09','Чужая закрытая площадка не раскрывает адрес через событие',
 ['src/catalog/services/event_domain.py:81'],
 ['test_foreign_private_venue_id_cannot_capture_or_publish_secret_address','test_venue_privacy_is_rechecked_at_snapshot_after_initial_validation'])
control('SC10','Старый владелец и устаревшая версия события не могут перезаписать изменения',
 ['src/catalog/services/event_domain.py:67'],
 ['test_organization_transfer_revokes_stale_actor_and_old_event_owner','test_stale_revision_cannot_overwrite_saved_edit_or_cancel'])
control('SC11','Действия с событиями требуют своей карточки и CSRF; JSON-LD экранирует закрытие script',
 ['src/catalog/services/event_domain.py','src/catalog/services/event_queries.py'],
 ['test_foreign_event_delete_and_submit_http_boundaries_and_csrf','test_public_jsonld_escapes_script_terminator_and_online_has_no_geo'])
control('SC12','Уведомление привязано к актуальному адресату, владельцу и POST/CSRF',
 ['src/catalog/services/workflow_notifications.py'],
 ['test_changed_email_cannot_read_old_address_notification','test_stale_join_confirmation_is_suppressed_after_owner_change','test_csrf_required_for_inbox_actions'])
control('SC13','Очередь сохраняет транзакционные события и подавляет дубли записи',
 ['src/catalog/services/workflow_notifications.py'],
 ['test_emit_is_transactional_and_dedupes_event_entity_version_recipient','test_parallel_duplicate_event_has_one_inbox_and_one_outbox'])
control('SC14','Остановка HTTP-записи и выбранные участники не обходят CSRF',
 ['src/catalog/r1_middleware.py:25','src/catalog/services/r1_cohort.py'],
 ['test_disabled_cohort_blocks_http_write_without_deleting_post_switch_rows','test_selected_cohort_allows_only_explicit_actor_ids','test_cohort_membership_does_not_bypass_csrf'])
(audit/'security-controls.json').write_text(json.dumps(controls,ensure_ascii=False,indent=2)+'\n')
gates=[]
def gate(key,priority,status,owner,title,impact,done,next_check,evidence,kind='launch_prerequisite'):
    gates.append({'id':key,'priority':priority,'status':status,'owner':owner,'title':title,
                  'business_impact':impact,'verified_local':done,'remaining_acceptance':next_check,
                  'evidence':evidence,'kind':kind})
gate('RG01','P1','PARTIAL_LOCAL','release-reviewer','Точный образ и доступная неизменяемая версия',
 'Иначе сервер может получить исходники или зависимости, отличающиеся от проверенных.',
 'Архив, чистый контекст и фактический LOCAL image:2794 файла/SHA совпадают.',
 'При отдельно разрешённом выпуске закрепить registry manifest digest, проверить pull этой версии и effective image. Required Compose interpolation проверяет наличие строки, а не семантическую allowlist/context SHA или реальную immutable registry identity; caller обязан их проверить. Здесь publish/pull/deploy НЕ запускались.',
 ['security-image.json'])
gate('RG02','P1','PARTIAL_LOCAL','release-reviewer + security-reviewer','Постоянное закрытое хранилище документов',
 'Пересоздание контейнера без отдельного тома может потерять загруженные документы; публичное размещение нарушает конфиденциальность.',
 'Путь /kidsmap-private-media вне /app/media; новый Compose merge требует private bind. Прежняя проверка сохранения bind-байтов была на служебном контейнере.',
 'Проверить абсолютный одобренный host path, права, отдельный backup, actual web mount и сохранение байтов после пересоздания exact web image в rehearsal; legacy публичные файлы отдельно инвентаризировать/перенести.',
 ['security-compose.json','security-controls.json','../reports/28-release-validation.json'])
gate('RG03','P1','PARTIAL_LOCAL','release-reviewer + orchestrator','Запись сначала выключена; разрешены только выбранные участники',
 'Неконтролируемый первый запуск позволяет менять данные до завершения сверки.',
 'Новый synthetic Compose defaultoff/IDs empty; новые HTTP/cohort/CSRF negatives PASS.',
 'В effective production settings отдельно подтвердить off/selected и одобренные actor IDs; согласовать переход к all. Quiesce offline writers/queue/cron отдельно: HTTP-флаг их не останавливает.',
 ['security-compose.json','security-controls.json'])
gate('RG04','P1','PASS_ROOT_LOCAL_EXTERNAL_OPEN','database-reviewer / root','Данные, ID, связи, документы и очередь сохраняются при восстановлении',
 'Откат старым dump поверх новых записей теряет изменения семьи, бизнеса и специалиста.',
 'Новая root native V3 recovery PASS:98 tables/25 public+2 private hashes; evidence root-owned, не собственная execution этого reviewer.',
 'Для запуска отдельно сверить настоящую schema/data и проверить recoverable/off-host restore; новая synthetic native recovery не заменяет реальный backup.',
 ['recovery-results.json','../reports/28-recovery-results.json'])
gate('RG05','P2','LOCAL_SUITE_FAILURES_OPEN' if corrected else 'CORRECTED_IMAGE_REPEAT_RUNNING','integration-reviewer + release-reviewer','Проверки в фактическом runtime образа',
 'Различие interpreter/dependencies может проявиться после сборки, хотя host suites прошли.',
 'Fresh image metadata Python3.12.15/39 packages; host3.12.3/39, только pip версия отличается. Retained image precision5 PASS; fresh static9305 PASS. Root fresh host1817:109F11E, Task33579/580, тот же ownershiprace; классификация root-owned.',
 full_image_summary+' Нужна пригодная CI suite и отдельная причинная классификация сбоев; неполный runtime test-document manifest нельзя скрывать инъекцией файлов.',
 ['security-image.json','security-static.json','full-results.json','image-full-results.json','image-full-r2-results.json','image-full-comparison.json','security-image-preflight.json','../reports/28-image-precision-results.json'])
gate('RG06','P1','PARTIAL_LOCAL','release-reviewer','Статика, proxy и private-denial effective configuration',
 'Ошибочная конфигурация сервера ломает интерфейс или открывает закрытые файлы.',
 'Fresh WhiteNoise production backend9305/manifest+inventory SHA совпадают с сохранёнными V3; прежний local nginx6/6 не заменяет effective production nginx/TLS.',
 'При отдельном разрешении проверить actual nginx routes/TLS/static volume/404 и private-denial в effective конфигурации, без раскрытия пользовательских файлов.',
 ['security-static.json','../reports/28-release-nginx.json'])
gate('RG07','P1','OPEN_EXTERNAL','release-reviewer + backend owner','Работник очереди и реальная доставка уведомлений',
 'Действия есть в кабинете, но письма могут не отправляться или повториться после сбоя SMTP.',
 'Fresh local transaction/dedupe/current-recipient/CSRF cases PASS; email locmem и транспорта нет.',
 'Назначить worker schedule/locking/retry owner, наблюдаемость и SMTP acceptance; учесть crash после SMTP ack, исключение exactly-once обещания.',
 ['security-controls.json'])
gate('RG08','P2','OPEN_EXTERNAL','security-reviewer + auth owner','Настоящий OAuth и внешние интеграции',
 'Вход и карты могут не работать с реальными ключами/redirect settings, несмотря на успешные mocks.',
 'Fresh12 negative cases OIDC/state/replay/identity/redirect/upload PASS; реальные provider/Maps/SMTP НЕ вызваны.',
 'При отдельном согласовании проверить реальные callback allowlist/scopes/provider configuration и карту; секреты в отчёт не включать.',
 ['security-supplement.json','security-supplement-source.json'])
gate('RG09','P1','OPEN_EXTERNAL','database-reviewer + release-reviewer','Effective права БД, backup и аварийное восстановление',
 'Избыточные права или непроверяемый backup увеличивают ущерб от ошибки и время восстановления.',
 'QA использует одноразовую PostgreSQL17.11/Unix sockets; это не production least privilege или backup strategy.',
 'Проверить least privilege, fresh recoverable/off-host backup и approved schema preflight в отдельно разрешённом выпуске; production здесь NOT_CONTACTED.',
 ['security-results.json'])
gate('RG10','P1','OPEN_EXTERNAL','orchestrator + release-reviewer','Контролируемый выпуск и stop criteria',
 'Автоматический pull/restart может запустить непроверенный код; возврат старой БД не является безопасным rollback.',
 'Source deploy-server pulls branch и имеет restart failure trap; exact candidate dirty WORKTREE не определяется одним HEAD.',
 'Отдельно одобрить конкретную версию/config/cohort и план; остановиться при потере ID/байтов/очереди, чужом доступе, schema mismatch или новых500; сохранить новые данные, quiesce writers, reconcile перед возобновлением.',
 ['../release-R2.md','../../../scripts/deploy-server.sh'])
gate('RG11','P2','CONFIRMED_TEST_DEBT','integration-reviewer','Конкурентный тест требует успеха отклонённой операции',
 'Шумящий gate усложняет различение настоящего нарушения доступа и безопасного отказа с reload.',
 'Fresh selected260:259 PASS/1F; fresh original5+forced retry probe6/6 PASS; прежние V2/current causal6/6 сохранены.',
 'В будущем отдельно уточнить контракт outcomes и deterministic ordering без ослабления проверки ACL; original assertion в текущем аудите не изменять.',
 ['security-results.json','security-causal.json','../reports/28-security-causal-classification.json'],'confirmed_test_issue')
gate('RG12','P2','OPEN_EXTERNAL','orchestrator + analytics/release owners','Базовые метрики и владелец наблюдения',
 'Без порогов ошибок/задержки/очереди невозможно вовремя заметить проблему ограниченного запуска.',
 'Local suites и snapshot не устанавливают реальные traffic/error/latency/query baselines.',
 'Назначить численные пороги, alert/incident owner и cohort observation window; отдельно проверить actual error/query/mail queue/worker metrics.',
 ['security-review.md'])
gate_report={'mode':'AUDIT_ONLY','production':'NOT_CONTACTED','production_ready':False,
 'artifact_identity':image['artifact_identity'],'local_image_config_id':image['image_config_id'],
 'self_authorship_limit':'Тот же исполнитель ранее создал release override; это не независимый review собственного package. Историческая DB crosscheck атрибутирована отдельно.',
 'fresh_execution':['security-results.json','security-supplement.json','security-causal.json','security-image.json','security-compose.json','security-static.json','security-image-preflight.json','image-full-r2-results.json'],
 'retained_same_source':['../reports/28-recovery-results.json','../reports/28-image-precision-results.json','../reports/28-release-validation.json','../reports/28-release-nginx.json'],
 'gates':gates}
(audit/'release-gates.json').write_text(json.dumps(gate_report,ensure_ascii=False,indent=2)+'\n')
rows='\n'.join(f"| {c['id']} | {c['name']} | {', '.join(i.split('.')[-1] for i in c['executed_case_ids'])} |" for c in controls)
report=f'''# Итоговый аудит: безопасность и границы запуска

**Текущий результат:** новые260 проверки дали **259 PASS,1 failure,0 errors/skips**; сбой сохранён.12 дополнительных проверок и отдельные6 конкурентных проверок прошли. Подтверждённого обхода ACL в проверенных сценариях не найдено. Это ограниченный security-аудит, а не доказательство безопасности всех ветвей или готовности production.

Исполнитель `/root/stage28_release`: canonical security-reviewer, затем последовательно canonical release-reviewer. Новый запуск по final-audit/PLAN.md; HEAD015d031d8eb17114bd860159dde805b38df3c13c/task33-progress, dirty WORKTREE. Собственный mirror `/root/km28-security`; root/browser/DB mirrors не изменялись. Только final-audit/security*,release-gates.json и qa/security*; application/assertions/старые28 отчёты не изменены. Production НЕ контактирован. Этот исполнитель раньше создал release override, поэтому не является независимым reviewer собственного package; прежняя DB crosscheck — отдельное свидетельство, а не новый собственный независимый review.

## 1. Состояние области и доказательства

Exact V3 `{image['artifact_identity']}`, LOCAL image config ID `{image['image_config_id']}`. Fresh immutable archive/manifest SHA, полный контекст и фактический `/app` образа:2794 файла, без лишних/пропущенных/изменённых файлов и symlinks. Registry publish/digest availability не проверялись; config ID нельзя автоматически назвать опубликованным registry manifest digest.

Fresh selected260 elapsed{suite.get('elapsed_seconds')}s; PostgreSQL17.11/Django6.0.2/Python3.12.3/psycopg3.2.10.167 применённых миграций/0 pending, check+makemigrations0, discovery1817unique/0 duplicates, network/libpq guardsTRUE, external credentialsFALSE, normal cleanupPASS/run+socket roots removed. Основные50 и дополнительные8 файлов совпали с WORKTREE/own mirror/frozen V3. QA diagnostic добавляет одну case только во внешний own mirror: causal discovery1818=1817 application+1 QA; repository и frozen artifact не менялись.

Команды: `wsl -d Ubuntu-24.04 -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/final-audit/qa/security_run.sh`, затем `security_supplement.sh`, затем `security_causal.sh`. Каждая запускает неизменённый QA04 на новой одноразовой БД и уникальном output; selected19 module labels→260, supplementary12 explicit method labels, causal original5+QA1. Raw вне repository `/root/task33-evidence/final-audit-security*-20261004`, JSON хранит IDs/агрегаты/guard/cleanup, не records/env/logs.

Codebase Memory сначала: generation2026-10-04T08:06:12Z, C-kidsmap/C:/kidsmap; bounded search4/has_morefalse. На ключевых service/config/storage путях coverage_unavailable/metadata_changed, Dockerfile partial10–26, nginx excluded; metadata ignored-list truncated2000/2020. Graph — подсказки, не доказательство полноты. Критические source/route/storage edges проверены прямым чтением и SHA; широких negative выводов по графу нет.

## 2. Сильные стороны — что получает пользователь

Семья видит допустимые публичные карточки и отзывы; закрытая площадка/отклонённое событие/личный документ не должны становиться доступны через чужую карточку, прямой ID или JSON-LD. У бизнеса связь с площадкой и авторство не заменяют владение; устаревшие версии и передача владельца перепроверяются. У специалиста подтверждённая личность отделена от управляющего бизнесом: менеджер не получает удостоверение личности, публичный сертификат требует согласия самого человека и approval. Модератору нужны отдельные полномочия: публикация не даёт право редактировать событие как организатор. Эти выводы ограничены конкретными свежими cases ниже.

| ID | Проверенный серверный контракт | Свежие конкретные case methods |
|---|---|---|
{rows}

[security-controls.json](security-controls.json) связывает каждую строку с actual source и полными executed IDs; [security-results.json](security-results.json) содержит результат. Дополнительные12 cases проверяют CSRF/PKCE, истёкший и повторный OAuth state, конфликт identity, подмену identity в уже вошедшем браузере, OIDC issuer/audience/expiry/subject, внешние next redirect, обязательную авторизацию upload, pixel-limit до полного decode, MIME mismatch и удаление чужого фото. [security-supplement.json](security-supplement.json). Google transport замокан — успешный тест не подтверждает реальный OAuth.

## 3. Реальная проблема: SEC-FA-01, P2, schedule-sensitive тест

Новый260 run снова упал в `{failed}`, ownership testcase:362, **до** проверки отзыва network ACL. Original race helper:344 ловит ValidationError и возвращаетFalse; test:361 игнорирует outcomes, а:362 безусловно требует нового владельца. Service `organization_ownership._parents`:39–50 читает organization anchor до блокировки; concurrent confirmation может поменять связь, тогда сервис правильно отклоняет transfer: `Structure changed; reload.`. Это не успешная передача с оставленными правами.

Новая deterministic QA probe принудительно завершила confirmation между чтением anchor и блокировкой. Первый transfer отклоняется/откатывается, original owner/version1 остаются; network доступ действителен для текущей подтверждённой связи. Свежий retry получает корректные locks, меняет owner/version2 и отнимает network place.edit. Fresh original пять concurrency cases +probe —6/6 PASS. [security-causal.json](security-causal.json). Прежние current/V2 six-case probes и8 identical service/test/model/config hashes — retained same-source evidence [classification](../reports/28-security-causal-classification.json), не новая V2 execution.

Нельзя превращать259/260 в260PASS по результату targeted run. Нельзя называть QA04 generic BASELINE_FAILURE самостоятельным доказательством baseline: причинная граница выше подтверждена отдельно. Нет продемонстрированного stale-ACL bypass или новой precision регрессии. Confidence высокий для подтверждённого ordering guard; точный scheduler interleaving исходного nondeterministic сбоя не инструментирован. Owner integration-reviewer; будущий шаг — точный контракт возможных outcomes/deterministic test, сохраняя строгую проверку отсутствия устаревших прав. В этом аудите исходные assertions не изменены.

## 4. Технический долг

Нестабильное требование успеха конкурентной операции создаёт шум в общем gate. BASE compose отдельно не содержит private bind и cohort env, а Dockerfile имеетCOPY.; безопасная упаковка зависит от применения уже существующего reviewed override и проверенного allowlisted context. Source deploy-server pulls branch и restart failure trap не заменяет совместимый rollback грязного проверенного артефакта. Это доказанные repository-условия и будущие release prerequisites, не установленная production авария.

## 5. Риски и независимость release/recovery

Fresh после security: `security_release.py` проверил archive/context и фактический LOCAL image2794 SHA/metadata, networknone/noports/cleanupPASS; rebuild/up/push не выполнялись. `security_compose.py`: official standalone v5.5.0 SHA verified, чистый synthetic env/empty external envfile, merge0, required private/context/image три negativesexit1; defaultoff/IDs empty/private target/kidsmap-private-media. Image digest в config-only run синтетический и не заменяет actual image inspection.

`security_static.py`: exact image Python3.12.15, production WhiteNoise backend подDJANGO_TESTING1 и QA guards, networknone/noports/readonly helper/owned temp;9305 files, manifest`{static['manifest_sha256']}`, inventory`{static['file_inventory_sha256']}`; cleanupPASS, совпадает с сохранённым root V3 static. Host suites Python3.12.3, image3.12.15;39 packages, retained/actual metadata показывает pip24.0→25.0.1. Retained DB-owned image precision5 — лишь пять конкретных tests, не full1817 inside image и не image-native restore.

Новая root-owned native V3 recovery PASS98 tables/25 public+2 private hashes: [recovery-results.json](recovery-results.json); это свежая execution root, не собственная recovery данного reviewer. Прежние private bind mechanics на служебном postgres container, nginx local6/6, image precision5 и независимая source crosscheck override — **retained same-source**. Root fresh host1817:109 failures/11 errors, Task33579/580, тот же ownershiprace; [full-results.json](full-results.json), классификация остальных failures root/domain-owned. Первый exact-image1817 завершился125F28E, Task33548/580. [image-full-comparison.json](image-full-comparison.json) сохраняет34 image-only случая:31 отказ по пути QA socket,1 readonly/tmp,1 отсутствующий taxonomy document в runtime allowlist,1 недостаточная rating population с пока не установленной причиной. Исправлены только QA bind/tmpfs; bounded preflight29/29 PASS с guards и cleanup. {full_image_summary} Первый результат сохранён; общие failed IDs не признаны безвредными без отдельной причинной проверки. Production image/env/schema/nginx/TLS/mounts/real cohort/least privilege/off-host backup/SMTP/OAuth/Maps и численные monitoring baselines UNKNOWN/NOT_RUN. Частичный LOCAL успех не сертификат launch-ready.

## 6. Legacy и кандидаты на удаление

Legacy owner/identity/URL/файлы требуют сохранения ID и явного разрешения неоднозначности. Застарелое владение не даёт verified-person права; informational affiliation не даёт business grant. Production legacy private-file placement не инвентаризирован. Dead-code/graph-absence не использованы для удаления; кандидатов на удаление здесь не утверждаем.

## 7. Пробелы проверки

Fresh272 security cases и6 causal cases не исчерпывают всю систему; выполненные наборы имеют пересечение, нельзя складывать их в количество уникальных всего продукта. Full application1817 и browser/keyboard/screenshots принадлежат root/browser, не этому reviewer. Нет real provider/mail/Maps/Redis multiworker/production-data penetration или effective proxy/mount acceptance. Public qualification download в Django и запрет nginx — разные слои; сохранённый local nginx test не доказывает текущую production конфигурацию.

## 8. Рекомендации и roadmap до запуска

[release-gates.json](release-gates.json) содержит12 machine-readable gates с владельцем, бизнес-эффектом, проверенной частью и точным remaining acceptance. Сначала закрепить фактически проверенную версию и решить baseline gate; затем проверить durable private storage/cohort/recovery/effective конфигурацию в separately approved release; подтвердить реальные интеграции/очередь/backup/monitoring. Production действия здесь не разрешены и не выполнялись. HTTP pause не останавливает offline writers/cron; recovery не означает перезапись новых rows старым dump.

## 9. Приоритеты и handoff

P0/подтверждённого P1 security exploit не найдено в выполненном scope. SEC-FA-01 — P2 test-contract issue с fresh failure, fresh causal reproduction, высоким confidence в защитном guard. RG P1 обозначают критические **предусловия будущего запуска**, не подтверждённые текущие incidents. Не увеличивать severity по слову«security» или «backup» без trigger/evidence.

Named handoff root integration-reviewer: сохранить fresh259/260 failure отдельно от new12/12 и6/6 PASS, actual58 source identity, fresh local image/Compose/static и ограничения self-authorship; присоединить новые root full/recovery и browser results, классифицировать remaining risks. Source/production/application/старые evidence сохранены. После handoff owned outputs заморожены.
'''
(audit/'security-review.md').write_text(report)
print(json.dumps({'report':'security-review.md','controls':len(controls),'release_gates':len(gates),
                  'fresh_selected_tests':260,'observed_failures':1,'supplement':12,'causal':6,'production':'NOT_CONTACTED'}))
