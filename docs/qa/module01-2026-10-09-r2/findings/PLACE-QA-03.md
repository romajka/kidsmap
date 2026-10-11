# PLACE-QA-03 — Смешанная правка опубликованного места блокирует одобрение

OPEN · P1 · PRE-EXISTING BASELINE · local module01-20261009-r2, 2026-10-09. Исправление не выполнено.

**Роль:** owner → moderator. **URL/endpoint:** `/ru/account/places/1/edit/ → moderator revision review (точный URL в review-inspect.result.txt)` (origin `http://localhost:8813`).

**Шаги:** Одобрить место. В одной сессии изменить название/адрес и цену с 15 на 18, сохранить, отправить candidate. Открыть эту revision модератором без второго редактора.

**Ожидание:** Цена по действующему immediate контракту меняется сразу; candidate identity/address остаётся пригодным к одобрению, если конкурентных изменений не было.

**Факт:** Review сообщает «Карточка изменилась после отправки…» и не даёт одобрить. У candidate base старые price_from/price_to, live уже 18.00. Исправленные identity/address не могут пройти этот путь.

**Свежие доказательства:** [published.result.txt](../published.result.txt); [resubmit-diagnose.result.txt](../resubmit-diagnose.result.txt); [review-inspect.result.txt](../review-inspect.result.txt); [candidate-diagnostic.json](../candidate-diagnostic.json); [screenshots/review-published-error-1440.png](../screenshots/review-published-error-1440.png).

**Первопричина / уверенность:** publication.py:_immediate/propose (base обновляется по immediate keys); pricing_plans.py:sync_legacy_price_fields; volunteer_places.py:revision_base_matches. Производные price_from/price_to меняются вместе с pricing, но остаются устаревшими в candidate base. _apply уже вызывает refresh_from_db: отсутствие refresh не является причиной. Уверенность высокая для воспроизведённого mixed edit.

**Почему P1:** Блокирует ключевой контракт одобрения опубликованной карточки при конкретном обычном trigger. Не утверждается блокировка всех заявок или production.

**Область исправления / зависимости:** Publication/revision rebasing и pricing projections; зависит от optimistic concurrency и атомарности.

## Самостоятельный промпт исправления

```text
Работай в фактическом checkout KidsMap. Прочитай AGENTS.md, канонические .agents и docs/qa/module01-2026-10-09-r2/findings/PLACE-QA-03.md. Сначала проверь актуальные HEAD/WORKTREE/active_run; сохрани чужие изменения и стенды. Историческое evidence используй как repro checklist, повтори на свежем DJANGO_TESTING=1 стенде с отдельными DB/cache/media/private-media/email и вымышленными данными. Без production credentials, внешних интеграций, commit/push/deploy.

Исправь PLACE-QA-03: после допустимой immediate правки pricing синхронизируй связанные производные поля candidate base атомарно, сохранив обнаружение настоящих конкурентных изменений. Не отключай revision_base_matches/CAS и не расширяй поля immediate без согласованного контракта. Сначала воспроизведи mixed name/address + price edit, затем проверь UI submit → moderator approve → live identity, отдельную цену, повторную правку, две вкладки и настоящего второго редактора. Existing assertions не ослаблять.

Подготовь конкретный план и согласуй scope реализации до изменения приложения согласно каноническим инструкциям. После согласования выполни только этот finding, meaningful regression проверки и rendered browser сохранение/reload. Сохрани новый отчёт, точные команды/exit codes, screenshots и ограничения NOT RUN. Не считай этот audit разрешением на реализацию.
```
