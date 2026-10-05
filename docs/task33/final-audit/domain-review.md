# Domain review: Task33, этапы 01–28

Role definition: [.agents/agents/django-reviewer/agent.md](../../../.agents/agents/django-reviewer/agent.md).

## 1. Состояние и границы доказательств

Режим AUDIT, canonical django-reviewer; исполнитель `/root/stage28_database` последовательно сменил прежнюю роль database-reviewer. Приложение и старые assertions не изменялись. Мои прежние DB/recovery/image отчёты не являются независимой проверкой собственной работы. Новый root native recovery выполнен другим исполнителем.

LOCAL HEAD `015d031d8eb17114bd860159dde805b38df3c13c`; dirty WORKTREE соответствует V3. Active_run `final-audit-20261004-080525Z`. PRODUCTION UNKNOWN/NOT_CONTACTED. Архив V3: `r2-local-sha256-65d8995ff21fb5e5b9fb88d81d18f2f36c4380841f14131cd11dc258bf8c61b2`, 2794 файла. Прочитаны 28 prompts, D01–D15, Task33 architecture и фактические role/shared contracts. Все 306 исходных пунктов сверены буквально; прежний CURRENT_LOCAL_COVERAGE не принят как PASS.

Codebase Memory сначала:25162 nodes/81390 edges,64 partial files,43 excluded directories. Root ранний index2026-10-03T21:35:01Z, отдельный domain coverage generation2026-10-04T08:08:36Z. Поздний actual check явно вернул indexed_at/generation2026-10-04T08:49:58Z,recorded_at08:49:59Z; status26976nodes/86175edges/45excluded. Это metadata полей tool, не время запроса. Конкретные services всё ещё metadata_changed/coverage_unavailable. [domain-graph.json](domain-graph.json). Граф — указатель; ORM/source проверены отдельно, удаления не обоснованы графом.

Свежий root full: **1817 тестов, 109 failures, 11 errors, 0 skip; Task33 579/580**. Единственное падение Task33 — `OwnershipConcurrencyTests.test_transfer_racing_confirmation_never_grants_stale_network_right`. Прежние 580/580 исторические. Focused security causal 6/6 PASS при том же source не отменяет текущий нестабильный результат полного прогона. [full-results.json](full-results.json), [security-causal.json](security-causal.json).

[stage-map.json](stage-map.json) содержит 28 строк с обещанием, реализацией, связями, source и точными test IDs. [requirements-review.json](requirements-review.json) содержит 306 индивидуальных записей: 220 имеют текущие узкие assertion scopes; ещё один содержит failed subclause ownership race; 52 относятся к историческому scope. Один пункт фиксирует product gap, один — mail crash window, один — незакрытую общую приёмку. Для 11 браузерных пунктов сопоставлены реальные действия и размеры экранов, но строгая браузерная проверка FAIL. Остальные 19 имеют конкретные role/source/workflow/external boundaries. Все прежние generic unverified записи заменены точными рассмотренными scopes. Настоящие assertions и результат их выполнения связаны с каждым выбранным тестом. Это **не 306 PASS**.

Свежий exact image: **1817 тестов, 108 failures, 12 errors, 0 skip; Task33 580/580 PASS**, guards и cleanup PASS. Исполнитель `/root/stage28_release`, [image-full-r2-results.json](image-full-r2-results.json). Первоначальные 125F/28E сохранены как история диагностированного QA harness. Host 579/580 остаётся действующим результатом: тот же ownership race проходит в образе без изменения source. Совпадают 108 failing IDs; дополнительная ошибка образа — тест taxonomy читает `docs/product`, намеренно отсутствующий в application artifact. Полный suite остаётся красным.

Свежий браузер: **816 contexts, 1724/1724 business/DOM checks PASS; strict FAIL** из-за одного `InvalidStateError` ViewTransition. Проверки R1/Specialist/Event охватывают AZ/RU/EN и семь ширин; Program/public Activity/public Organization — только 390/1280. Нативные POST проверки Program impact confirmation, candidate-only edit, stale 409, scope 404 и закрытые pending/private страницы прошли. Начальные approved display fixtures созданы ORM: полного публикационного UI-пути это не доказывает. [domain-browser-evidence.json](domain-browser-evidence.json) и [browser-results.json](browser-results.json). Из 1724 итоговых проверок 1721 представлены raw named UI checks; ещё три — collector checks Event. Их нельзя выдавать за дополнительные самостоятельно рассмотренные UI assertions.

Отдельная причинная диагностика browser reviewer: оба нативных Program POST (400 без impact confirmation и 302 с подтверждением) дают InvalidStateError ViewTransition. При 400 candidate не создаётся; при 302 pending сохраняется, approved данные не меняются. Это подтверждает ошибку браузерного перехода при правильном business state. Два diagnostic errors не добавлены к основным 816 contexts/1724 checks. [browser-motion-results.json](browser-motion-results.json).

## 2. Что работает и как части соединены

| Сквозной путь | Реальная связь и доказательство | Ограничение |
|---|---|---|
| Org→Place→Activity/Group→Tariff→search/map | Join подтверждает affiliation; Program approval создаёт approved snapshot; nested writer создаёт группы/тарифы; matching_groups проверяет условия на одной группе. Новые probes используют реальные writers и Program propose/review. | Standalone writer не создаёт taxonomy, необходимую точному поиску. |
| Affiliation→contacts→detach | Detach сохраняет approved местные данные/IDs, отключает наследование контактов; public resolver читает свежую связь. `test_detach_pending_program_retains_approved_snapshot_ids_and_visibility`, `test_active_contacts_fallback_and_detach_remove_live_org_sources` root PASS. | Синтетическая связь не доказывает реальные полномочия бизнеса. |
| Transfer→team/invite→edit | Transfer повышает ownership_version, отзывает team/invites; ACL проверяется заново при locked save. `test_transfer_suspends_old_team_cancels_invites_and_preserves_author`, `test_owner_controller_authorization_is_rechecked_at_locked_save` root PASS. | Fresh race test FAILED; concurrency гарантия не закрыта. |
| Owner/Admin/Volunteer→candidate→public | Один publication pipeline с schema/base/candidate version; пересекающиеся правки проверяются, pending сохраняет approved live. `test_pending_and_rejected_keep_approved_live`, `test_overlapping_live_change_refuses_stale_approval`, `test_dependent_price_conditions_bundle_wholly_gated` root PASS. | Старые payload без signed token требуют индивидуального причинного разбора. |
| Typed reviews→rating→reactions→deletion | Раздельные Place/Activity/Specialist/Event heads/revisions; pending не вытесняет approved, reactions привязаны к revision; unknown authors не объединяются. `test_pending_edit_keeps_approved_projection_and_one_rating`, `test_reaction_ids_and_original_revision_are_preserved`, `test_retention_clears_all_labels_and_pending_candidate` root PASS. | Org не получает общий балл; trusted legacy save — отдельный compatibility путь. |
| Specialist claim→employment→practice→documents | Claim назначает аккаунт человека; employment требует согласий обеих сторон; online сохраняет историю; public certificate требует dedicated review и person opt-in. `test_claim_assigns_verified_person_and_records_legacy_manager`, `test_organization_invitation_or_proposal_is_not_person_confirmation`, `test_certificate_http_consent_moderation_and_revocation` root PASS. | Identity evidence никогда не становится certificate; реальные identity checks не выполнялись. |
| Event organizer≠venue→snapshot→history/calendar | Организатор — Org или verified person; venue owner не получает прав; publication фиксирует venue, cancel/reschedule сохраняют историю, прошлое проведение требует нового ID; Baku query использует [start,end). `test_venue_owner_cannot_edit_organizers_event`, `test_publication_snapshot_stays_at_original_venue_after_move`, `test_past_occurrence_cannot_be_reused_under_same_id` root PASS. | История защищена сервисом/ORM, не от произвольного raw SQL. |
| Mutation→inbox/outbox→retry | Transactional emit/dedupe; проверяются текущий recipient/email/доступ; SMTP failure сохраняет inbox. `test_emit_is_transactional_and_dedupes_event_entity_version_recipient`, `test_smtp_failure_keeps_inbox_and_retry_sends_once` root PASS. | Exactly-once физическая отправка при crash не доказана. |
| Conversion→новые записи→native restore→writes-off reader | Root свежая репетиция: 98 таблиц, 25 public и 2 private media файла, exact V3 reader, HTTP ACL, cleanup PASS. [recovery-results.json](recovery-results.json). | Disposable synthetic restore; не production backup/deploy и не независимая повторная оценка моей прежней DB работы. |

## 3. Подтверждённые проблемы

**DOMAIN-P2-01: часть новых занятий теряется при сочетании фильтров.** Реальный `replace_nested_pricing` создаёт standalone Activity без category/subcategory. `publication.fields_for('activity')` не предоставляет category; `catalog_search.matching_groups` проверяет taxonomy из program_snapshot. Новое занятие 4–8 лет находится по возрасту 5 и в общем каталоге, но отсутствует по category EDU+age5. Реальный Program propose/review делает category+age рабочим; subcategory writer отсутствует, известная Place.subcategory не помогает. Воспроизведено двумя новыми probes; [domain-results.json](domain-results.json).

Исключение неизвестной taxonomy из exact search консервативно и прямо описано в architecture19. Но это ограничивает исходную пользу этапов14/19. D04 обещает Program category, **не отдельное поле Program.subcategory**; исходный19 обещает поиск по categories/subcategories. Passing `ExactSearchTests.offer` внедряет category в snapshot через ORM, subcategory reader test также внедряет snapshot. Это доказывает reader, а не доступный пользователю writer. Confidence HIGH; owner django/frontend/product. Зависимости14→19→18/20/21. Требуется согласованный источник approved taxonomy и интеграционный writer→search/map тест; APP не исправлен.

**DOMAIN-P2-02: ownership concurrency приёмка нестабильна.** Свежий полный suite и security aggregate падают на transfer/confirmation race; focused6 PASS. Подтверждено падение проверки, **не подтверждён чужой доступ**. Нельзя списывать его на старые fixtures или объявлять exploit без фактического ACL counterexample. Нужны оба thread outcomes и точное разделение ожидаемого structure conflict/retry от неправильного результата. Owner security/django/database; этапы06/07/28 частичны до разрешения.

**DOMAIN-P3-03: crash window почты.** `workflow_notifications.deliver_batch` отправляет SMTP внутри DB transaction, затем пишет sent. Crash после физической отправки до commit допускает повтор. Нормальный retry test и DB dedupe не доказывают strict exactly-once email17-03. Fault injection такого окна и внешний SMTP NOT_RUN. Confidence source HIGH/runtime UNKNOWN. Owner backend/release: явно принять at-least-once policy либо provider idempotency; не менять ожидания молча.

## 4. Технический долг и старые failures

[domain-failure-classification.json](domain-failure-classification.json) сохраняет все120freshproblem entries/109uniqueIDs, теперь у каждого exact firstassertion/subtest/exception из свежего raw trace. Все35SIGNED/28OPTIONAL рассмотрены отдельно: token failure8, approved/candidate projection, неприменимый bulk mock, неверные счётчики12→10, optionalfields и contactalternatives. Firstfailure/source diagnosis не выдан за проверку уникального feature сvalidpayload. Семь presentation/geography/SEOquery причин остаются частичными; actual9queries vsold4 — реальное увеличение overhead, не автоматически harmless.

Три admin причины доказаны отдельно новыми probes. Claim approval меняет owner/APPROVED, но не публикует: прежний assert active=True противоречит D02/D06. Unpublish POST не содержит version; повтор с единственным current version даёт302/draft/inactive. Pagination: пять fixtures фактически district=baku_narimanov, query=baku даёт ноль строк; замена только района запроса возвращает три корректные страницы/nav/currentpage. Старые assertions сохранены.

Failed-publish test требует photo/coords blocking и старую message, при этом payload без token. Это частичное source contract mismatch; полный актуальный publish action не воспроизведён, поэтому весь failure не объявлен безвредным. Sitemap UTC/Baku midnight expectation из прежнего28 отчёта утром проходит при неизменном source: это времязависимость, а не исправление.

Отдельный шестой causalprobe воспроизвёл два oldaudiencefailures: вcatalog естьshortlabel«Взрослые», detail200содержитage6–17 и«Взрослые группы». Facts сохранены, меняются exactstring/расположение units. Это nativeHTTPtext, не rendered visual acceptance.

## 5. Риски и внешние границы

OAuth/Maps/SMTP реальных providers, production cron, реальные private volumes и участники пилота NOT_RUN. Browser reviewer отдельно проверяет rendered AZ/RU/EN/widths/keyboard; HTML source не выдаётся за рендер. SQL constraints покрывают локальную структуру/XOR/FK/bounds; cross-parent/ownership/history частично защищены ORM/service. Raw SQL и bulk update не подразумевают те же гарантии. Upload suffix/size не равно полному MIME анализу.

Fresh stage19: одна карточка6→8 queries,0.107488→0.111060s; восемь41→8 queries,0.206756→0.329205s при параллельной QA нагрузке. Для восьми снижение query count доказано, ускорение этим замером не доказано. Root native20/200 medians15.958→3.909/159.979→11.596ms — другой bounded synthetic consumer. Оба результата сохранить; production load NOT_RUN.

## 6. Legacy/dead-code кандидаты

Удалений не предлагаю. Legacy Place/readers/review rows/reactions/scalar-only pricing нужны для совместимости; отсутствие static graph edge не доказывает ненужность. Старые URLs/IDs/media проверены на fixtures; production состав UNKNOWN.

## 7. Выполнено и не выполнено

Мой runtime: шесть новых внешних QA-only cases на `/root/km-final-domain`; final r5 PASS6/0F0E,167 migrations/0unapplied. Django6.0.2/PostgreSQL17.11/Python3.12.3/psycopg3.2.10, DJANGO_TESTING1, disposable UnixPG/tmpfs/networknone/noports/no checkoutmount, LocMemcache/email, isolatedmedia. Network/libpqguards иcleanupPASS. Пять проверенных критических sourcepaths совпали с текущимV3.

Exact command: `wsl -d Ubuntu-24.04 -u root --exec /root/kidsmap-task33/.venv/bin/python /mnt/c/kidsmap/docs/task33/final-audit/qa/domain_run.py --mode probe --output /tmp/task33-qa-domain-cross-stage-r5-20261004`.

Предыдущие попытки сохранены: first2PASS/3 adaptererrorsmissingClient; r2 4PASS/1 adaptererrormissingsetUpTestData; r3 5PASS; r4 5PASSсcausalpaginationreplay; r5 6PASSсaudiencefacts. Менялся только внешний adapter. Rawevidence `/root/task33-evidence/final-audit-domain-cross-stage-20261004`; repoсодержитагрегатыбезприватныхdumps/logs. SourceSHA в [domain-source.json](domain-source.json), helperSHA вdomain-results.

Inventory/report commands: `python docs/task33/final-audit/qa/domain_inventory.py`, `python docs/task33/final-audit/qa/domain_report.py`, `python docs/task33/final-audit/qa/domain_failures.py`. Проверены28/306 literal unique records и1817 AST test functions; source refs существуют. APP full/recovery/browser/security коллег — attributed, не дублирован мной. Production/реальные письма/Git/deploy/schema/app/assertion edits NOT_RUN.

## 8. Рекомендации

1. Закрыть повторяющийся ownership race, сохранив failed traces и ACL после обоих outcomes. Focused PASS не заменяет failed aggregate.
2. Согласовать taxonomy writer gap14/19; проверить реальный writer→exact search→map без выдуманных требований к Program.subcategory.
3. Разобрать120 legacy entries индивидуально: актуальный payload/fixture, assertion, causal replay; не ослаблять старые assertions ради green.
4. Исправить и повторить строгую браузерную проверку ViewTransition; расширить Program/Activity/Organization с двух ширин до обещанного набора. Для остальных source/external gates сохранить конкретную границу. Макет, source, HTTPtest, renderedbrowser, isolatedrecovery иproduction — разные доказательства.
5. Явно описать email crash boundary и ручные gates private media/пилот/provider. Production этим аудитом не запускать.

## 9. Приоритеты и handoff

P0 не подтверждён. P1 чужой доступ/потеря данных в этом review не подтверждены. Ownership race — незакрытый P2 gate с возможным security impact до причинного разбора; taxonomy product gap P2 HIGH; outbox crash window P3 source-only. Full109F11E остаётся реальным долгом.

Named handoff: `/root`, canonical kidsmap-orchestrator. Объединить28-row map/306 inventory с fresh browser/security/native/full-image evidence; сохранить PARTIAL/UNKNOWN и авторство. Исправления findings не выполнялись, им нужен отдельный согласованный scope.
