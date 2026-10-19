# SOCIAL-QA-07 Implementation Plan

> Lead django-reviewer, frontend/browser checks последовательно. Реализация только после прямого одобрения этого двухфайлового scope; approved06 не означает approved07. Новых subagents не требуется.

**Goal:** показывать настоящее публичное имя Activity на странице отзывов, согласованное с карточкой и её языковым fallback, без технического object ID.

**Architecture:** Activity target_name читает существующий public_presentation.present(target,request language)['name']. Остальные kind сохраняют прежний name_i18n/str path. Общий presentation resolver/локализация/ACL/модели не меняются; новый9method regression защищает routes/response/escaping/fallback/visibility.

**Tech Stack:** Django6.0.2/Python3.12.15/PostgreSQL17.11, существующие SSR templates, native Chromium155. Новых dependencies нет.

**Spec:** [finding](../module09-2026-10-10-r1/findings/SOCIAL-QA-07.md), [repair prompt](../module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-07.txt), [guide](../continuation-and-repair-prompts-2026-10-11.md#repair-SOCIAL-QA-07), [fresh REPORT](REPORT.md).

## Global constraints

- Только SOCIAL07/P3, exact two-file scope ниже. Source1021, C:\kidsmap, branch codex/module09-transfer-2026-10-16-r1, HEAD852938d96764ae315b92859e3651e5ea62054a36; dirty approved SOCIAL03–06 сохранить.
- No production/commit/push/deploy/reset/clean/stash/dirty checkout switch. Index/task33ref/active_run:NONE/sharedMO/.cbmignore/foreign files/containers/processes сохранить; active_run автоматически не назначать.
- CSS/templates/sharedJS/models/services/schema/PO/существующие assertions и SOCIAL08–09 вне application scope. Existing Activity label observation05–06 — тот же SOCIAL07, не новый ID.
- Tests только DJANGO_TESTING1/own PG/testDB/cache/media/private-media/email, fictional data, cleared env/no .env/prodcredentials; external blocked/SIMULATED. Fresh RU/AZ/EN builder/verify, sole LOCALE_PATHS до setup; sharedMO не пересобирать.
- Не добавлять ручной name_ru→name_az fallback или raw Program/draft/revision reads. Канонический resolver уже учитывает локальные поля, AZ fallback и permitted approved snapshot/live affiliation.
- При отсутствии публичного имени сохранить canonical empty string; не подставлять технический str(Activity) и не выдумывать перевод. Для staff-only unpublished Activity тоже canonical empty. Это ограничение/выбор плана: заголовок после локализованного префикса может быть пустым, как public presentation. Privacy/visibility не ослаблять, content-quality неизвестные отдельно.
- Source graph partial/unavailable/metadata_changed не доказательство completeness: relevant source/native response проверены. Full ACCEPT09/global/08–09 не начинать автоматически.

## Source map / причина

typed_reviews._target() уже вызывает present() для visibility Place/Activity. public_details.activity_detail() читает presentation.name; present() использует activity_texts()/translated() и approved text provenance. Activity.name_i18n/__str__ не предоставляют такого display path. target_reviews() около98 сейчас использует getattr(name_i18n) or str(target), поэтому имя становится Activity object(pk).

Минимальный новый context expression:

~~~python
'target_name': present(target, getattr(request, 'LANGUAGE_CODE', get_language()))['name'] if kind == 'activity' else (getattr(target, 'name_i18n', None) or str(target)),
~~~

Изменяется только строка context render, включая normal200 и existing409render. GET/POST/CAS/cooldown/moderation/permissions и routes не меняются. Это дополнительный read-only вызов существующего presentation resolver для Activity; он повторяет часть чтений visibility, оптимизация/cache/refactor не входит в scope. Не превращать этот fix в перенос resolver в модель.

## Task1 — gates и meaningful RED

- [ ] Получить approval двухфайлового scope; записать human message/approved plan/hash. Уже данное approval этого scope не спрашивать повторно.
- [ ] Проверить [source-entry.json](source-entry.json),1021hashes/HEAD/index/dirty/active_run/MO и own runtime/controller/template/presentation origins. Own m09s07-plan-r1-app/pg/internalnet/33347/session можно reuse лишь после fresh ownership/isolation proof.
- [ ] Использовать unchanged native RED [matrix](matrix.json) и9method baseline [tests.log](tests.log). Не повторять неизменившийся full corpus; если drift — affected freshRED в новом уникальном профиле.
- [ ] Новые tests исполнены до patch как candidate_tests.SocialQA07TitleTests из ignored scratch, не application test path; meaningful failures должны исчезнуть после patch. Existing assertions не редактировать.

## Task2 — exact two-file implementation

**Modify:** src/catalog/controllers/typed_reviews.py, только Activity target_name expression около98.

**Create:** src/catalog/testcases/test_social_qa07_activity_review_title.py. Полный тестовый код: [candidate_tests.py](candidate_tests.py),9методов.

Полный proposed controller: [candidate-typed_reviews.py](candidate-typed_reviews.py), [exact two-file diff](proposed.diff), [hashes](candidate-manifest.json).

- [ ] Apply-check и patch:

~~~powershell
git apply --check --ignore-space-change docs/qa/social-qa07-recheck-2026-10-17-pc-r1/proposed.diff
git apply --ignore-space-change docs/qa/social-qa07-recheck-2026-10-17-pc-r1/proposed.diff
~~~

- [ ] Source count1022, controller normalized after SHA/tests SHA совпадают с manifest; прочие1020изначальных source побайтно прежние. Сохранить dirty03хунки в этом же контроллере.
- [ ] Не менять общий presentation name contract ради заголовка; no __str__/name_i18n model additions, no migrations, no newPO, no href/SEO/indexability changes.
- [ ] Canonical empty/public unpublished cases осознанно остаются empty; tests фиксируют это без технического fallback/утечки private name.

## Task3 — targeted GREEN / native acceptance

- [ ] Fresh own source gate1022/runtime/template/MO, исключить cached module старого процесса только своим новым runtime/serve. Full suites не повторять.
- [ ] Запустить ровно новые9методов одним запуском:

~~~text
catalog.testcases.test_social_qa07_activity_review_title.SocialQA07TitleTests
~~~

- [ ] Expected GREEN: requested names guest/author RU/AZ/EN; AZ fallback; permitted snapshot; live published Program; HTML escaping; empty canonical names; Place/Specialist/Event unchanged; hidden guest/author404; permitted staff-only private Activity has no public-name leak.
- [ ] Small affected existing render/CAS subset при изменённом target_reviews(), один запуск:

~~~text
catalog.testcases.test_social_qa03_conflict_recovery.TypedReviewConflictRecoveryTests.test_stale_draft_renders_with_latest_version_and_no_write
catalog.testcases.test_social_qa03_conflict_recovery.TypedReviewConflictRecoveryTests.test_conflicting_script_text_is_escaped_and_preserved
~~~

- [ ] [cell-body.js](cell-body.js)/[matrix.py](matrix.py) после patch: guest/author×RU/AZ/EN×6widths localized Activity36cells; AZ fallback и permitted snapshot дополнительно12cells390; shared Place/Specialist/Event18cells390. Actual public card→native link→review→reload, h1/document title equality, no technicalID, data unchanged, role forms/layout.
- [ ] Все current Activity sourceFAIL должны стать PASS без weakening controls. Public card/name/review/title сверять с literal fixture values и canonical present; source failure counts historical не переносить.
- [ ] Добавить final representative escaping/blank/staff-hidden/live Program native checks и301/404/guest/author limits; не исправлять adjacent visual issues автоматически.
- [ ] Native viewport screenshots после real scroll/finite animation wait; console/pageerrors/local HTTP/static/font/icon/overflow, actual URLs/reload. External blocked requests/SIMULATED и own media limitations отдельно; realSR/fullWCAG/physical/otherbrowsers NOTRUN без выполнения.
- [ ] POST/moderation data changes нужны только affected CAS fixture checks в своей testDB; production mutations нет. Existing submissions/ratings/replies/reactions/public projections не менять.

## Task4 — report/preservation/stop

- [ ] Новый unique fix-run approval/diff/RED→GREEN/source/commands/exits/counts/nativePNG/failedattempts/NOTRUN/verification/artifact manifest.
- [ ] Проверить1020unchangedsource/oldpackages/refs/index/active_run/sharedMO/.cbmignore/entrycontainerIDs-states. Не утверждать whole-machine process continuity из Docker snapshot.
- [ ] Закрыть только SOCIAL07 по actual evidence, добавить отдельную guide note сохранив прежние bytes/history. SOCIAL08–09/fullACCEPT09/global/module10 не начинать автоматически, no commit/push/deploy.

## Self-review

Два точных файла/full diff/tests заданы. Canonical current-public text/provenance reuse, requested locale/AZ fallback/snapshot/live Program/empty/staff privacy/escaping/other kind/CAS/render/browser flows/SQL-read overhead учтены. Candidate пока unapplied, live GREEN NOT RUN, implementation approval PENDING.
