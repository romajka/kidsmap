# Итоговый аудит: безопасность и границы запуска

**Текущий результат:** новые260 проверки дали **259 PASS,1 failure,0 errors/skips**; сбой сохранён.12 дополнительных проверок и отдельные6 конкурентных проверок прошли. Подтверждённого обхода ACL в проверенных сценариях не найдено. Это ограниченный security-аудит, а не доказательство безопасности всех ветвей или готовности production.

Исполнитель `/root/stage28_release`: canonical security-reviewer, затем последовательно canonical release-reviewer. Новый запуск по final-audit/PLAN.md; HEAD015d031d8eb17114bd860159dde805b38df3c13c/task33-progress, dirty WORKTREE. Собственный mirror `/root/km28-security`; root/browser/DB mirrors не изменялись. Только final-audit/security*,release-gates.json и qa/security*; application/assertions/старые28 отчёты не изменены. Production НЕ контактирован. Этот исполнитель раньше создал release override, поэтому не является независимым reviewer собственного package; прежняя DB crosscheck — отдельное свидетельство, а не новый собственный независимый review.

## 1. Состояние области и доказательства

Exact V3 `r2-local-sha256-65d8995ff21fb5e5b9fb88d81d18f2f36c4380841f14131cd11dc258bf8c61b2`, LOCAL image config ID `sha256:6566a67c0b3ab3da8ea040314b016908b1cbe17e09a50912fc5c80fe5228f5fd`. Fresh immutable archive/manifest SHA, полный контекст и фактический `/app` образа:2794 файла, без лишних/пропущенных/изменённых файлов и symlinks. Registry publish/digest availability не проверялись; config ID нельзя автоматически назвать опубликованным registry manifest digest.

Fresh selected260 elapsed88.516s; PostgreSQL17.11/Django6.0.2/Python3.12.3/psycopg3.2.10.167 применённых миграций/0 pending, check+makemigrations0, discovery1817unique/0 duplicates, network/libpq guardsTRUE, external credentialsFALSE, normal cleanupPASS/run+socket roots removed. Основные50 и дополнительные8 файлов совпали с WORKTREE/own mirror/frozen V3. QA diagnostic добавляет одну case только во внешний own mirror: causal discovery1818=1817 application+1 QA; repository и frozen artifact не менялись.

Команды: `wsl -d Ubuntu-24.04 -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/final-audit/qa/security_run.sh`, затем `security_supplement.sh`, затем `security_causal.sh`. Каждая запускает неизменённый QA04 на новой одноразовой БД и уникальном output; selected19 module labels→260, supplementary12 explicit method labels, causal original5+QA1. Raw вне repository `/root/task33-evidence/final-audit-security*-20261004`, JSON хранит IDs/агрегаты/guard/cleanup, не records/env/logs.

Codebase Memory сначала: generation2026-10-04T08:06:12Z, C-kidsmap/C:/kidsmap; bounded search4/has_morefalse. На ключевых service/config/storage путях coverage_unavailable/metadata_changed, Dockerfile partial10–26, nginx excluded; metadata ignored-list truncated2000/2020. Graph — подсказки, не доказательство полноты. Критические source/route/storage edges проверены прямым чтением и SHA; широких negative выводов по графу нет.

## 2. Сильные стороны — что получает пользователь

Семья видит допустимые публичные карточки и отзывы; закрытая площадка/отклонённое событие/личный документ не должны становиться доступны через чужую карточку, прямой ID или JSON-LD. У бизнеса связь с площадкой и авторство не заменяют владение; устаревшие версии и передача владельца перепроверяются. У специалиста подтверждённая личность отделена от управляющего бизнесом: менеджер не получает удостоверение личности, публичный сертификат требует согласия самого человека и approval. Модератору нужны отдельные полномочия: публикация не даёт право редактировать событие как организатор. Эти выводы ограничены конкретными свежими cases ниже.

| ID | Проверенный серверный контракт | Свежие конкретные case methods |
|---|---|---|
| SC01 | Волонтёр не читает чужой кандидат и не получает бизнес-права | test_volunteer_a_cannot_read_or_mutate_b_candidate_by_direct_id, test_informational_approval_without_business_grant |
| SC02 | Владелец не утверждает собственный отзыв; чужие реакции и устаревшие версии отклоняются | test_owner_moderation_denied_but_reply_report_scoped, test_cross_parent_reaction_and_stale_revision_are_rejected |
| SC03 | Рейтинг разных типов карточек не смешивается; скрытая карточка не принимает публичный отзыв | test_typed_rating_contributions_never_mix_and_pending_keeps_approved, test_hidden_target_rejects_public_submit_without_creating_review |
| SC04 | Управляющий бизнесом не получает доступ к личным документам специалиста | test_management_owner_cannot_read_or_choose_person_document_publication, test_live_place_owner_and_organization_grantee_cannot_read_person_documents |
| SC05 | Удостоверение личности остаётся закрытым; сертификат требует согласия человека | test_identity_cannot_become_public_even_with_tampered_flags, test_approved_certificate_without_person_opt_in_stays_private |
| SC06 | Отзыв прав и подмена document ID проверяются на сервере | test_dedicated_reviewer_permission_and_revocation, test_foreign_document_id_denied_to_verified_person |
| SC07 | Личный файл не имеет общего URL; закрытый media-путь отклоняется | test_private_storage_has_no_public_url, test_document_bytes_are_outside_public_media, test_direct_legacy_media_download_is_denied |
| SC08 | Владелец площадки не является организатором события | test_venue_legacy_owner_and_plain_staff_cannot_save_or_cancel_resolved_event, test_platform_publication_permission_never_grants_organizer_edit |
| SC09 | Чужая закрытая площадка не раскрывает адрес через событие | test_foreign_private_venue_id_cannot_capture_or_publish_secret_address, test_venue_privacy_is_rechecked_at_snapshot_after_initial_validation |
| SC10 | Старый владелец и устаревшая версия события не могут перезаписать изменения | test_organization_transfer_revokes_stale_actor_and_old_event_owner, test_stale_revision_cannot_overwrite_saved_edit_or_cancel |
| SC11 | Действия с событиями требуют своей карточки и CSRF; JSON-LD экранирует закрытие script | test_foreign_event_delete_and_submit_http_boundaries_and_csrf, test_public_jsonld_escapes_script_terminator_and_online_has_no_geo |
| SC12 | Уведомление привязано к актуальному адресату, владельцу и POST/CSRF | test_changed_email_cannot_read_old_address_notification, test_stale_join_confirmation_is_suppressed_after_owner_change, test_csrf_required_for_inbox_actions |
| SC13 | Очередь сохраняет транзакционные события и подавляет дубли записи | test_emit_is_transactional_and_dedupes_event_entity_version_recipient, test_parallel_duplicate_event_has_one_inbox_and_one_outbox |
| SC14 | Остановка HTTP-записи и выбранные участники не обходят CSRF | test_disabled_cohort_blocks_http_write_without_deleting_post_switch_rows, test_selected_cohort_allows_only_explicit_actor_ids, test_cohort_membership_does_not_bypass_csrf |

[security-controls.json](security-controls.json) связывает каждую строку с actual source и полными executed IDs; [security-results.json](security-results.json) содержит результат. Дополнительные12 cases проверяют CSRF/PKCE, истёкший и повторный OAuth state, конфликт identity, подмену identity в уже вошедшем браузере, OIDC issuer/audience/expiry/subject, внешние next redirect, обязательную авторизацию upload, pixel-limit до полного decode, MIME mismatch и удаление чужого фото. [security-supplement.json](security-supplement.json). Google transport замокан — успешный тест не подтверждает реальный OAuth.

## 3. Реальная проблема: SEC-FA-01, P2, schedule-sensitive тест

Новый260 run снова упал в `catalog.testcases.test_task33_ownership.OwnershipConcurrencyTests.test_transfer_racing_confirmation_never_grants_stale_network_right`, ownership testcase:362, **до** проверки отзыва network ACL. Original race helper:344 ловит ValidationError и возвращаетFalse; test:361 игнорирует outcomes, а:362 безусловно требует нового владельца. Service `organization_ownership._parents`:39–50 читает organization anchor до блокировки; concurrent confirmation может поменять связь, тогда сервис правильно отклоняет transfer: `Structure changed; reload.`. Это не успешная передача с оставленными правами.

Новая deterministic QA probe принудительно завершила confirmation между чтением anchor и блокировкой. Первый transfer отклоняется/откатывается, original owner/version1 остаются; network доступ действителен для текущей подтверждённой связи. Свежий retry получает корректные locks, меняет owner/version2 и отнимает network place.edit. Fresh original пять concurrency cases +probe —6/6 PASS. [security-causal.json](security-causal.json). Прежние current/V2 six-case probes и8 identical service/test/model/config hashes — retained same-source evidence [classification](../reports/28-security-causal-classification.json), не новая V2 execution.

Нельзя превращать259/260 в260PASS по результату targeted run. Нельзя называть QA04 generic BASELINE_FAILURE самостоятельным доказательством baseline: причинная граница выше подтверждена отдельно. Нет продемонстрированного stale-ACL bypass или новой precision регрессии. Confidence высокий для подтверждённого ordering guard; точный scheduler interleaving исходного nondeterministic сбоя не инструментирован. Owner integration-reviewer; будущий шаг — точный контракт возможных outcomes/deterministic test, сохраняя строгую проверку отсутствия устаревших прав. В этом аудите исходные assertions не изменены.

## 4. Технический долг

Нестабильное требование успеха конкурентной операции создаёт шум в общем gate. BASE compose отдельно не содержит private bind и cohort env, а Dockerfile имеетCOPY.; безопасная упаковка зависит от применения уже существующего reviewed override и проверенного allowlisted context. Source deploy-server pulls branch и restart failure trap не заменяет совместимый rollback грязного проверенного артефакта. Это доказанные repository-условия и будущие release prerequisites, не установленная production авария.

## 5. Риски и независимость release/recovery

Fresh после security: `security_release.py` проверил archive/context и фактический LOCAL image2794 SHA/metadata, networknone/noports/cleanupPASS; rebuild/up/push не выполнялись. `security_compose.py`: official standalone v5.5.0 SHA verified, чистый synthetic env/empty external envfile, merge0, required private/context/image три negativesexit1; defaultoff/IDs empty/private target/kidsmap-private-media. Image digest в config-only run синтетический и не заменяет actual image inspection.

`security_static.py`: exact image Python3.12.15, production WhiteNoise backend подDJANGO_TESTING1 и QA guards, networknone/noports/readonly helper/owned temp;9305 files, manifest`7da4de86a4cb148aa783c824d8a31bd0d9748941e24e5c2bcb2f9c2f3fa08ae2`, inventory`b408557f6ec81d5d9f46e44625a4b32bcc3777c7d4096bc4d39df8348656cb09`; cleanupPASS, совпадает с сохранённым root V3 static. Host suites Python3.12.3, image3.12.15;39 packages, retained/actual metadata показывает pip24.0→25.0.1. Retained DB-owned image precision5 — лишь пять конкретных tests, не full1817 inside image и не image-native restore.

Новая root-owned native V3 recovery PASS98 tables/25 public+2 private hashes: [recovery-results.json](recovery-results.json); это свежая execution root, не собственная recovery данного reviewer. Прежние private bind mechanics на служебном postgres container, nginx local6/6, image precision5 и независимая source crosscheck override — **retained same-source**. Root fresh host1817:109 failures/11 errors, Task33579/580, тот же ownershiprace; [full-results.json](full-results.json), классификация остальных failures root/domain-owned. Первый exact-image1817 завершился125F28E, Task33548/580. [image-full-comparison.json](image-full-comparison.json) сохраняет34 image-only случая:31 отказ по пути QA socket,1 readonly/tmp,1 отсутствующий taxonomy document в runtime allowlist,1 недостаточная rating population с пока не установленной причиной. Исправлены только QA bind/tmpfs; bounded preflight29/29 PASS с guards и cleanup. Corrected exact-image: 1817 tests, 108F/12E, Task33 580/580; cleanup PASS. Image-only 1, host-only 1, common 108. Initial125F28E preserved; see image-full-comparison.json; common IDs are not harmless-baseline proof. Первый результат сохранён; общие failed IDs не признаны безвредными без отдельной причинной проверки. Production image/env/schema/nginx/TLS/mounts/real cohort/least privilege/off-host backup/SMTP/OAuth/Maps и численные monitoring baselines UNKNOWN/NOT_RUN. Частичный LOCAL успех не сертификат launch-ready.

## 6. Legacy и кандидаты на удаление

Legacy owner/identity/URL/файлы требуют сохранения ID и явного разрешения неоднозначности. Застарелое владение не даёт verified-person права; informational affiliation не даёт business grant. Production legacy private-file placement не инвентаризирован. Dead-code/graph-absence не использованы для удаления; кандидатов на удаление здесь не утверждаем.

## 7. Пробелы проверки

Fresh272 security cases и6 causal cases не исчерпывают всю систему; выполненные наборы имеют пересечение, нельзя складывать их в количество уникальных всего продукта. Full application1817 и browser/keyboard/screenshots принадлежат root/browser, не этому reviewer. Нет real provider/mail/Maps/Redis multiworker/production-data penetration или effective proxy/mount acceptance. Public qualification download в Django и запрет nginx — разные слои; сохранённый local nginx test не доказывает текущую production конфигурацию.

## 8. Рекомендации и roadmap до запуска

[release-gates.json](release-gates.json) содержит12 machine-readable gates с владельцем, бизнес-эффектом, проверенной частью и точным remaining acceptance. Сначала закрепить фактически проверенную версию и решить baseline gate; затем проверить durable private storage/cohort/recovery/effective конфигурацию в separately approved release; подтвердить реальные интеграции/очередь/backup/monitoring. Production действия здесь не разрешены и не выполнялись. HTTP pause не останавливает offline writers/cron; recovery не означает перезапись новых rows старым dump.

## 9. Приоритеты и handoff

P0/подтверждённого P1 security exploit не найдено в выполненном scope. SEC-FA-01 — P2 test-contract issue с fresh failure, fresh causal reproduction, высоким confidence в защитном guard. RG P1 обозначают критические **предусловия будущего запуска**, не подтверждённые текущие incidents. Не увеличивать severity по слову«security» или «backup» без trigger/evidence.

Named handoff root integration-reviewer: сохранить fresh259/260 failure отдельно от new12/12 и6/6 PASS, actual58 source identity, fresh local image/Compose/static и ограничения self-authorship; присоединить новые root full/recovery и browser results, классифицировать remaining risks. Source/production/application/старые evidence сохранены. После handoff owned outputs заморожены.
