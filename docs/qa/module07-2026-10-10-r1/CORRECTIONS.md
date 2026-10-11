# Собственные QA corrections

Решение построено на fresh selected runs в results-summary.json. Raw outputs/attempts сохранены. CLI exit0 отражает выполнение скрипта, а не отсутствие FAIL в его JSON.

- Discovery selector находил hidden reset submit; harness ограничен visible auth form.
- Initial seed имел неверное поле Specialist; исправлен only initial fixture setup до аудируемых переходов.
- Admin business editor302 — запрет без business grant, не admin-editor redirect; canonical admin200 доказан отдельно.
- Volunteer document403 — middleware boundary. Fresh acl-boundaries covers3 languages, включая первый RU navigation timeout.
- Hidden avatar img src="" не является visible broken image; fresh settings/long-filled проверяют visibility/bounds.
- Modal Escape после250ms/isVisible заменён settled class/aria/opacity. Focus trap/return действительно FAIL18.
- Mobile logout использует native hamburger drawer; auth-resume завершает прежние аккаунты, не пересоздаёт их.
- Stale place save — AJAX photo-save403, не navigation; name сохранён и place state не изменён.
- First supplement self-invite не выбрал required place; empty Enter ещё завершал navigation. Fresh corrected rerun18 completed.
- Org409 refresh/finally длится дольше350ms; settled proof18 PASS. Delayed/repeated transport clearly SIMULATED.

204 superseded/harness observations исключены: [excluded-observations.json](excluded-observations.json). Raw attempts не итоговые assertions; одноимённые screenshots повторных successful states относятся к последнему fresh run.18 supplement-harness PNG — diagnostic. Valid codes/passwords hidden/cleared before capture; token URLs/OTP отсутствуют в results.

No-side-effects assertions сравнивают allowlisted qa_evidence state: users, verified, members/invitations, org grants/invitations, place owner/content/ownership versions/status, document status/consent, deletion status. Это не dump всех исторических audit/event таблиц. Source сверяет ранний permission/version rejection; report не утверждает отсутствие любого request logging/session cookie effect.
