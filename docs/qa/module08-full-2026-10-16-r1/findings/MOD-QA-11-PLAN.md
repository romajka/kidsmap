# PLAN MOD-QA-11 — причина решения в обработанной заявке

Новая причина внутри модуля08. P2: после native final reject причина точно хранится в revision.review_note, но администратор и reviewer не видят её на terminal content detail. Две actual native FAIL в audit-history.js.result.json; сохранённое значение доказано flows-native.js.result.json, terminal PNG для обоих actors. Не утверждается отсутствие причины во всех других поверхностях.

Причина: hub_detail выводит textarea только в pending; read model уже отдаёт row.revision с review_note, поэтому нового поля сервиса/ORM/ACL не нужно. Graph-first _revision_row найден; source/coverage metadata_match, no_recorded_issue, не proof completeness.

Точный scope2files:
- src/catalog/templates/admin/volunteer/hub_detail.html: для content approved/declined/rejected с непустым review_note показать read-only h2+экранированный текст с сохранением переносов. Использовать существующий km-volunteer-field (overflow-wrap:anywhere); новые CSS/JS/PO не нужны. Pending decision form и права сохранить. Affiliation/новую историю всех версий сюда не добавлять.
- NEW src/catalog/testcases/test_mod_hub_decision_note.py: authenticated real content-detail response при approve/reject/return,3языка, admin/reviewer, точный текст/переносы/escaping; empty/pending note, отсутствие повторной decision form и denied roles. Domain snapshots неизменны от GET; существующие assertions не менять.

[Candidate diff](MOD-QA-11-proposed.diff), [SHA unapplied](MOD-QA-11-manifest.json). До approval template не подключён.

После approval: meaningful RED→GREEN только новой группы+один смежный processed-action guard; реальный браузер RU/AZ/EN×360/390/768/1024/1280/1440, корректный terminal note, длинный/HTML-like текст, отсутствие decision controls, negative role,console/network/PNG и отсутствие domain mutations. Повторять весь уже завершённый полный корпус08 не требуется: сохранить его результаты, выполнить только зависимые проверки нового изменения. Новый scope требует отдельного одобрения.
