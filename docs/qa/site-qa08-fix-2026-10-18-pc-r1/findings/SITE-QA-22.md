# SITE-QA-22 — «Сохранить и выйти» возвращает subsection settings в тот же редактор

**OPEN / P3 / LOCAL dirty WORKTREE / 2026-10-18.** Owner: django-reviewer; presentation/route acceptance — frontend-admin/browser-qa. Execution /root inline, independent review NOT RUN. Production UNKNOWN/не контактировали.

Native mobile360/390 ×AZ/RU/EN: по6branding/footer cases, всего12false `exited` checks в evidence/browser-media-footer.json. POST302 сохраняет точное значение и один LogEntry, затем GET changelist302 → GET тот же singleton change200. Нет потери данных; подпись обещает выход, фактически остаётся редактирование. Gallery `_save` и catalogue `_save` этого эффекта в проверенном scope не показали.

Source: src/catalog/domain_admin/site.py:178 `_BaseSiteSettingsSectionAdmin.changelist_view()` всегда перенаправляет на singleton change; исходник этого Python file полностью совпадает с entry hash до CSS patch. Новая CSS не меняет HTTP transitions. Классификация PRE-EXISTING LOCAL behavior, уверенность высокая для branding/footer native trigger; другие подклассы base нуждаются в своих native случаях, не объявлены проверенными.

Доказательство: evidence/browser-functional-diagnostic.json id save-exit с реальной цепочкой302POST→302GET→200GET, исходные12FAIL retained; actual data/reload/public checks при этом PASS. Исходный SITE08 UI diff/права/backend не расширялись.

Следующий шаг: отдельный конкретный Django plan — после `_save` из subsection направить пользователя к settings hub, сохранив `_continue`, revisions/stale409, права, media validation и gallery/catalogue semantics. Проверить native desktop/mobile3langs и meaningful redirect regression. До согласования не реализовывать. SITE08 CSS followup этот finding не исправляет.
