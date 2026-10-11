# Отдельные промпты на исправление

Ни один промпт не выполнен этим аудитом. Приложение и assertions сохранены.

## ORG-QA-03 / P2

```text
Прочитай AGENTS.md и docs/qa/module02-2026-10-09-r1/findings/ORG-QA-03.md. Scope: исправить responsive toolbar административного выбора мест перед подключением к организации. На1024px с sidebar доступно660px, а nowrap форма требует803–893px; document overflow126–216px наEN/AZ/RU. Исследуй kidsmap_changelist.css и существующий search panel. Согласуй конкретный план scope; используй доступную ширину контента/перенос controls, сохрани локальный scroll таблицы. Не скрывай переполнение всего документа и не меняй ownership/connections logic. Докажи поиском/выбором/переходом к preview на360/390/768/1024/1280/1440, RU/AZ/EN, с sidebar и без, клавиатурой и fresh screenshots/geometry. Новые fictional isolated данные; без production/commit/push/deploy, сохранить чужой WORKTREE.
```

## ORG-QA-04 / P3

```text
Прочитай AGENTS.md и docs/qa/module02-2026-10-09-r1/findings/ORG-QA-04.md. Scope: устранить остаточные русские заголовки административного редактора организации наAZ/EN. Свежие browser proofs показывают корректные поля, но вкладку «Названия», заголовок «Организации» и служебные секции по-русски. Текущий gettext для первых двух строк возвращаетRU наAZ/EN. Сначала проверь все фактические источники и текущие PO/MO; не смешивай missing translations с frozen import-time labels. Представь точечный план и согласуй scope; добавь недостающие переводы/исправь привязку языка существующих строк без нового workflow. Проверь сменуRU→AZ→EN в одном процессе и браузере, create/edit/draft/pending/published, mobile/desktop screenshots и labels. Обновляй только согласованные application/locale файлы. Без production/commit/push/deploy; чужие изменения сохранить.
```

## ORG-QA-01 / P2

```text
Продолжаем KidsMap. Прочитай AGENTS.md, канонические .agents и docs/qa/module02-2026-10-09-r1/findings/ORG-QA-01.md. Проверь текущие checkout/HEAD/WORKTREE/active_run и сохрани чужие изменения. Scope: исправить привязку ServerDraft к форме опубликованной организации после одобрения.
Воспроизведи на новых вымышленных изолированных данных: автосохранение draft → submit → review approve → редактирование опубликованного → серверное autosave → новая browser context. Сейчас форма source_version=2 получает draft source_version=1 и HTTP409, same-tab recovery скрывает проблему. Исследуй _detail_context, organization_workspace.html и существующий draft/publication контракт. Используй актуальный draft на текущей базе либо предусмотренное безопасное восстановление устаревшего; не ослабляй CAS и проверки владельца, не стирай локальные данные и не перекрывай более новый submitted candidate старым working draft.
Добавь содержательную regression проверку перехода approve→fresh autosave и conflict при настоящей конкуренции. Докажи сохранение/reload в независимой сессии, сохранность публичной версии до review, RU/AZ/EN и mobile/desktop error states. DJANGO_TESTING=1, отдельные DB/cache/media/email, без production/commit/push/deploy. Сначала представь конкретный план исправления в этом scope согласно AGENTS, затем реализуй после согласования scope. Итог: diff, команды/exit codes, свежие evidence/screenshots и оставшиеся ограничения.
```

## ORG-QA-02 / P2

```text
Продолжаем KidsMap. Прочитай AGENTS.md, канонические .agents и docs/qa/module02-2026-10-09-r1/findings/ORG-QA-02.md. Проверь checkout/HEAD/WORKTREE/active_run; сохрани чужие изменения. Scope: дать владельцу сети поддержанный UI отзыва активного сетевого доступа и отмены pending приглашения в существующем кабинете организации.
Сначала воспроизведи create invite→accept→place edit→owner team list. Сейчас есть список/новое приглашение/refresh, но нет revoke/cancel controls; существующие APIs grant/cancel работают. Переиспользуй текущие business_team services, grant expected_version и invitation guards; не создавай вторую систему прав. Покажи роль/scope/последствия, явное подтверждение, busy/error/conflict и актуальный результат. При отзыве доступ к сетевым местам прекращается; независимые прямые разрешения сохраняются. Устаревшая форма, чужой grant/invite ID, потеря ответа/повтор и отсутствие прав не должны менять доступ неправильно. Отказ сотрудника в inbox оцени отдельно и не расширяй scope молча.
План и согласование scope согласно AGENTS; затем содержательные tests и реальный браузер RU/AZ/EN на mobile/desktop, клавиатура/фокус, round-trip и матрица прав. Только новые изолированные вымышленные данные, DJANGO_TESTING=1, без production/commit/push/deploy. Верни diff, команды/exit codes, screenshots и ограничения. Существующие assertions не ослаблять.
```
