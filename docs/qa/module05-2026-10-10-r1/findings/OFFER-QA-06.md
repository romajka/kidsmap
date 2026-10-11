# OFFER-QA-06 — AZ/EN административные статусы частично остаются русскими

OPEN · P3 · LOCAL C:/kidsmap · run module05-2026-10-10-r1 · HEAD8d188b316f800fbedf0b1e376905dfd4924cb1b6.
Роль: admin-editor; LOCAL locale environment. Endpoint/URL: `/admin/catalog/program/1/change/; activity/2; offeringgroup/2`. Исполнитель /root, sequential AUDIT ONLY. Дефект приложения не исправлялся.
Classification: pre-existing baseline текущего WORKTREE. Регрессия относительно другого SHA/production NOT RUN. Для06 отдельно подтверждён ENVIRONMENT компонент existing .mo.

Шаги: В административном language switch выбрать English или Azərbaycan. Открыть статус группы и владения.

Ожидание: Системные статусы отображаются на выбранном языке; fallback пользовательского текста отделён от перевода UI.

Факт: html.lang=en, но «Публикация занятия: Published», «Владелец назначен», «Условия не подтверждены». AZ аналогично. Owner add_group/add_plan и ошибки цены в свежей проверке переведены корректно; прежняя гипотеза о всех owner CTA отвергнута.

Причина / confidence: Смешанная причина подтверждена чтением gettext: перевод «Владелец назначен» есть в .po, отсутствует в .mo; для «Публикация занятия: %(status)s» и «Условия не подтверждены» нет .po записей. .mo не пересобирались в аудите. Confidence HIGH по наблюдаемому поведению; ограничения гипотез явно указаны.

Приоритет: Неполная локализация рабочих статусов; P3, не auth/данные. Часть ENVIRONMENT, часть source catalog gap.

Область и зависимости: Translations/build packaging; definitions BusinessEditor; зависит от согласованного набора переводов и выпуска compiled catalogs. Владельцы будущего решения: django-reviewer / frontend-reviewer / frontend-admin / database-reviewer по указанному слою; независимый запуск этих ролей не заявляется.

Доказательства свежего запуска:

- [i18n-evidence.json](../i18n-evidence.json)
- [diagnostics.result.txt](../diagnostics.result.txt)
- [admin-group-en-badge-crop-390.png](../screenshots/admin-group-en-badge-crop-390.png)
- [admin-editor-offeringgroup-tab0-az-390.png](../screenshots/admin-editor-offeringgroup-tab0-az-390.png)

Source references: src/catalog/domain_admin/business.py:118–150; locale/en/LC_MESSAGES/django.po; locale/az/LC_MESSAGES/django.po; existing .mo runtime. Snapshot и проверка неизменности: [snapshot](../snapshot.json), [verification](../verification.json).

Копируемый промпт для отдельного согласованного исправления:

```text
KidsMap: OFFER-QA-06, AZ/EN административные статусы частично остаются русскими. Найди фактический checkout, прочитай AGENTS.md и canonical .agents. Отчёт: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-06.md. Старые screenshots/DB — только repro checklist; проверь новый HEAD/WORKTREE/active_run и свежий UI.
Сначала составь конкретный план области Translations/build packaging; definitions BusinessEditor; зависит от согласованного набора переводов и выпуска compiled catalogs. Реализацию выполняй только в рамках явно согласованного пользователем scope. Не исправляй остальные findings попутно.
Отдели недостающие msgid/msgstr от устаревших .mo. Подготовь AZ/EN status translations и воспроизводимую сборку locale artifacts, затем повтори fresh browser проверку фактически поставляемых файлов. Не называй recompilation приложения исправлением безопасности и не меняй бизнес-статусы.
Сохрани чужие изменения/active_run/стенды. Только DJANGO_TESTING=1 и собственные isolated DB/cache/media/private-media/email с вымышленными данными, без production credentials и внешних integrations. Без commit/push/deploy/production. Существующие assertions не ослаблять. Приложи exact commands/counts/exits и свежие browser screenshots/save/reload, докажи соответствие runtime WORKTREE; ограничения оставь NOT RUN.
```
