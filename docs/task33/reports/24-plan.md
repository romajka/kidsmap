# Stage24 implementation plan

Goal: выполнить только prompts/24.md, D08 и specialist/review/rights architecture; APPROVED IMPLEMENT по прямому поручению пользователя. Lead root django-reviewer; зависимость23 DONE. Production и25+ запрещены.

Architecture: стабильный Specialist PK и typed review22 сохраняются. Additive verified person identity, claim и employment records; legacy owner не становится автоматически verified person. Все новые документы private, публикация только по явному выбору подтверждённого специалиста и отдельному решению KidsMap. Не переносить существующие production файлы автоматически.

Tech stack: Django6, PostgreSQL17, FileSystemStorage, isolated QA04 launcher.

- [x] Прочитать spec/dependency/canonical roles, проверить active_run и snapshot HEAD015d031d; сохранить dirty worktree24-entry-manifest.json до изменений. Codebase Memory transport unavailable; scoped source fallback.
- [x] Root: RED private-download/storage/direct-media tests в test_task33_specialist_privacy.py; обычный staff и foreign owner получают404, storage.url не выдаёт public URL, guarded public media закрывает protected_docs. Выполнить QA04 all с отдельным label до реализации.
- [x] Domain worker: test-first proposal/claim/employment/history в test_task33_specialist_domain.py; claim concurrent approvals допускают одного verified person; invitation не подтверждает вторую сторону; withdraw и online switch сохраняют records. Реализация в новых models/specialist_domain.py, services/specialist_domain.py и owner_specialist_use_cases.py. Root координирует существующую Specialist schema и additive migrations0131/0132.
- [x] Root: private storage module, dedicated active-staff reviewer permission с volunteer deny, guarded download и public certificate provenance. New Specialist verified_person_user/created_by/person_verified_at, документ opted_in_by/opted_in_at. Пример доступа: ordinary staff ->404; dedicated reviewer ->200 private attachment; anonymous approved document without specialist consent ->404.
- [x] Root: admin inline не показывает file.url/не выдаёт документы обычному staff/не задаёт owner consent; legacy owner не получает identity ownership через admin. Django DEBUG и SERVE_MEDIA_FILES используют одинаковый guarded media handler; local nginx deny prefix precedes public media alias.
- [x] Root: review22 reply/report используют verified specialist person; account-deletion hook отзывает consent и личные claim actor metadata, сохраняет историю по действующей retention policy, не вводит новую policy.
- [x] Root: operational private-media transition документирует inventory/quarantine/manual verification/copy verification/release rollback; local synthetic nginx/files проверяются без production перемещений.
- [x] Независимые security и DB reviewers проверяют root/domain implementation с отдельными negative/concurrency тестами; собственные изменения не выдаются за независимый review.
- [x] Final: targeted domain/privacy + adjacent Task33 suites, Django checks/migration consistency, full-suite comparison с23 classified IDs; browser AZ/RU/EN×7 widths если existing UI изменён. Exact commands/results/not-run записать в24.md, source manifest не хеширует свой отчёт.
- [x] Сверить критерии prompt24; DONE только после всех checks/review, снять active_run. Stage25 screens checkpoint остаётся отдельным prerequisite25.

Execution: inline root и bounded domain worker по действующей авторизации; commit/push/merge/deployment не выполнять.
