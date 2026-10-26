# Publication and saved-card readiness implementation plan

**Goal:** одобрение карточки завершает соответствующую заявку; редактор и административные списки считают сохранённую рабочую версию одинаково.
**Authorization:** пользователь 2026-10-26 прямо поручил реализовать прошлый план и объединить подсчёт. Работа выполняется последовательно /root, без отдельного запроса approval.
**Spec:** `docs/reports/publication-pending-request-2026-10-26.md` и два пользовательских скриншота 80%/20%.
**Architecture:** сохранить `place_readiness.evaluate_readiness` единственным набором правил. Добавить адаптер сохранённой рабочей версии, использующий действующую проекцию кандидата и form adapter. Публичная проверка по live данным остаётся отдельным потребителем тех же правил. Заявки PUBLICATION завершать в publication transaction с точным сравнением версий; CLAIM не затрагивать.
**Stack:** существующие Django/PostgreSQL, серверные templates и административный JavaScript. Новых зависимостей и миграций нет.

## Constraints

- Сохранить исходный dirty WORKTREE; без commit/push/deploy и production mutations.
- Не закрывать исторические stale/чужие CLAIM/новые candidate версии по признаку published.
- Не добавлять фото и координаты в обязательный знаменатель: действующий контракт содержит 10 требований; проверка готовности карты отдельная.
- Unsaved ввод оценивает форму; после сохранения/reload список и форма должны совпасть. Частный автосейв ServerDraft не подменяет общую сохранённую рабочую версию.
- Тесты только с очищенным environment, DJANGO_TESTING=1 и собственным PostgreSQL/media/cache/mail. Browser fixtures вымышленные.

## Task 1: publication/request consistency

Files: `src/catalog/services/publication.py`, `src/catalog/services/organization_ownership.py`; regression: `src/catalog/testcases/test_publication_request_completion.py`.

- [x] Сначала воспроизвести PENDING после `publication.review(...approve=True)` и `publication.publish(...)`.
- [x] Завершать только PENDING PUBLICATION с совпавшими applicant/owner, ownership/content/candidate версиями до принятия. Записывать модератора/дату/note и один audit в той же транзакции.
- [x] При вызове через moderate_place_request перечитать решение после публикации, не писать второй audit; передать note в publish/review. Сохранить проверки freshness.
- [x] Проверить оба входа, direct publish без revision, повторные вызовы, чужие CLAIM/applicant, stale source/candidate/ownership, активный несогласованный draft, отказ/permission/conflict и полный rollback при сбое audit.

Observable acceptance:
```python
publication.review(actor=staff, revision_id=revision.pk, version=revision.version, approve=True)
request.refresh_from_db()
assert request.status == 'APPROVED'
assert request.audit_entries.filter(action='APPROVED').count() == 1
```

## Task 2: saved readiness consistency

Files: `src/catalog/services/place_readiness.py`, `src/catalog/domain_admin/place.py`, `src/catalog/domain_admin/owner.py`; regression: `src/catalog/testcases/test_admin_saved_readiness.py`.

- [x] Воспроизвести base 20% / saved candidate 80% в реальных HTTP editor/list responses.
- [x] Добавить `evaluate_saved_place_readiness(place)` с overlay draft/pending/rejected, включая explicit clear, candidate tariffs/nested pricing и structured schedule. Без candidate использовать live readiness. Approved/declined candidates не заменяют текущую карточку.
- [x] Применить адаптер в административных индикаторах места/заявки. Использовать relation prefetch/select_related, не создавать ModelForm на каждую строку.
- [x] Сверить 10 пунктов, done/total/percentage и missing codes в editor/list/request list; смену candidate статусов и явное удаление данных; неизменность live/public данных и read-only GET.
- [x] Проверить реальные browser DOM editor/list/check/save/reload AZ/RU/EN и 390/768/1024/1280/1440; проверить console/network. Целевая связанная регрессия после обеих правок одним общим запуском.

Observable acceptance:
```python
assert editor_summary['completion_pct'] == 80
assert list_trigger['data-score'] == '80'
assert list_trigger['data-done'] == '8'
assert list_trigger['data-total'] == '10'
```

## Verification and delivery

- [x] TDD RED → GREEN для обеих ошибок; связанные publication/readiness/admin suites; Django check/migration drift и diff whitespace.
- [x] Зафиксировать точные команды, числа, browser evidence, ограничения и итоговый scope в `docs/reports/publication-and-readiness-2026-10-26.md`.
- [x] Остановить только собственный QA runtime. Production заявка №351 и deploy остаются отдельными действиями.
