# ORG-04 Detach Compatibility Implementation Plan

> **For agentic workers:** Выполнять последовательно в текущем чате после пользовательского согласования этого плана. Делегирование и commit/push/deploy не разрешены. Сохранить dirty WORKTREE и актуальную авторизацию; повторно прочитать prompt и свежий source. Статус: IMPLEMENTED LOCAL 2026-10-08; пользователь согласовал этот scope сообщением «дальше». Проверки и ограничения: docs/qa/org-04-fix-2026-10-08.md.

**Goal:** Закрыть отсоединение без обзора последствий во всех HTTP-входах, сохранив canonical права и данные места.

**Architecture:** Веб-входы используют существующий detach-preview → consent → server receipt → execute_detach → canonical detach. Старый JSON detach перестаёт выполнять мутацию и возвращает явное указание пройти веб-обзор; новый JSON-протокол не создаётся в ORG-04. Право выполнить отвязку и право читать карточку проверяются отдельно: допустимая отвязка приватного места не раскрывает его метаданные.

**Tech Stack:** Существующие Django controllers/services/templates, PostgreSQL QA, штатный coordinator и его10-минутные receipts; новые зависимости и миграции не нужны.

**Spec:** [ORG-04 prompt](../../qa/organization-deep-audit-2026-10-08/prompts/org-04.md); [свежая проверка](../../qa/org-04-compatibility-2026-10-08.md).

## Global Constraints

- Только ORG-04; только DJANGO_TESTING=1, isolated DB/cache/media, вымышленные данные, без внешних интеграций.
- Без commit/push/deploy/production. Ни старые отчёты, ни текущий HEAD без WORKTREE не являются доказательством runtime.
- Не менять canonical request_join/confirm_join/detach, права и версии владения, актуальность связей, публикацию, consent и программные snapshots.
- Не писать organization_id напрямую. Предварительный обзор не отсоединяет; consent без server receipt не исполняется.
- Не расширять чтение чужого приватного места ради возможности показать обзор. ORG-01/02/03 сохраняются.

## Решение по совместимости

| Вход | Новое поведение | Последствие для старых клиентов |
|---|---|---|
| «Мои места» | Ссылка на существующий detach-preview вместо POST отсоединения | Нужны обзор и подтверждение; новый параллельный мастер не создаётся |
| Старый HTML POST `/account/organizations/<org>/branches/<place>/detach/` | После проверок actor/target/version:302 на detach-preview, без мутации | Старая открытая форма приведёт к обзору, а не выполнит действие |
| Старый JSON POST `/api/ownership/detach/place/<id>/` | Валидный авторизованный запрос:409 `confirmation_required`, `preview_url`; связь не меняется | Намеренное изменение контракта: клиент не должен считать409 успешным отсоединением и не должен повторять запрос автоматически |
| Новый preview GET | Создаёт receipt/snapshot и показывает последствия; мутации связи нет | Действителен10 минут, привязан к actor/organization/place/action |
| Новый confirm POST | Нужны consent=1,preview_id,idempotency_key; target берётся из receipt | Повтор того же receipt/key возвращает тот же результат без повторной мутации |
| Чужие права/невалидные поля/неверный target/version | Отказ без мутации, без раскрытия приватных данных | Существующие403/404/400 не заменяются сообщением об успешной операции |

JSON ответ авторизованному старому клиенту:

```json
{"error":"confirmation_required","preview_url":"/ru/account/organizations/123/branches/456/detach-preview/"}
```

URL строится через reverse для текущего языка и только после проверки права canonical отвязки. Ни названий, ни адресов, ни документов в этом ответе нет. Остальные ownership actions и их форматы остаются прежними. Новые поля consent/preview_id не добавляются к старому JSON-протоколу: подтверждение выполняется формой существующего веб-обзора.

Это честный разрыв старой автоматической операции, а не обратно совместимый200. Клиенты вне репозитория неизвестны; production не проверялся. Выпуск вне локального QA потребует отдельно уведомить/обновить известных клиентов. Временный200 или флаг обхода согласия не допускается.

## Что учитывает обзор

Обычная доступная карточка использует существующие данные: название/адрес, точная связь, количество общих программ, сетевых и прямых разрешений, наследуемые контакты. Последствия: содержимое места сохраняется; общие занятия становятся локальными снимками по canonical правилам; обновления сети и наследование контактов прекращаются; сетевой доступ пропадает; прямые актуальные разрешения остаются.

Свежая проверка выявила исключение: org-side owner архивной сети законно может выполнить canonical detach приватного места, но не может открыть нынешний preview. Сохраняем это право без выдачи place.view: обзор/результат показывает только известный клиенту ID связи и общие последствия, без name/address/publication/контактов/списков сотрудников/счётчиков приватных зависимостей. Snapshot остаётся серверным, результат читается только actor. Этот режим не применяется к join/search/pending и не расширяет visibility gate.

Старый pending не подтверждается и не переписывается автоматически. После отвязки новое подключение выполняется отдельным request_join/confirm_join, старый receipt его не восстанавливает. Изменение места/владения/сети/зависимостей после preview даёт changed/no_rights/manual_review согласно существующим правилам, без исполнения старого намерения.

## Карта файлов

| Файл | Ответственность |
|---|---|
| `src/catalog/controllers/organization_workspace.py` | Старый HTML POST → обзор; разрешённые исключения preview без права читать карточку |
| `src/catalog/controllers/organization_ownership_api.py` | Закрытие старой JSON-мутации,409 confirmation_required с безопасным URL |
| `src/catalog/services/organization_connections.py` | Только detach: проверка существующей mutation authority отдельно от display visibility; coordinator/snapshot/redacted result |
| `src/catalog/templates/pages/owner_places.html` | Ссылка «Отсоединить: посмотреть последствия» |
| `src/catalog/templates/pages/organization_connections.html` и includes/organization_connection_rows.html | Общие последствия/ID для redacted режима без ложных нулевых счётчиков |
| `locale/az/LC_MESSAGES/django.po`, `locale/en/LC_MESSAGES/django.po` | Только необходимые новые detach-review строки; существующие переводы переиспользовать |
| Новые `src/catalog/testcases/test_organization_detach_transport.py` | Регрессии транспорта/consent/privacy/version/replay |
| Existing workspace/connections/ownership testcases | Ожидания старого detach меняются только в части транспорта; canonical tests остаются прежними |

Schema/models/canonical organization_ownership.py/publication/прочие findings не меняются. CSS/JS правки не планируются; обнаруженные несвязанные визуальные дефекты фиксируются отдельно.

## Task1: регрессии и разделение display/mutation

**Interfaces:** Новый внутренний helper в organization_connections.py: `detach_access(*, actor, place_id, organization_id, expected_ownership_version=None)` возвращает fresh actor,place,organization либо существующий PermissionDenied/ObjectDoesNotExist/ValidationError. Он не меняет данные, не предоставляет business/read grants; использует те же active actor/side-owner/version/target/deleted/history условия, что canonical detach. Изменение связи по-прежнему происходит только в ownership.detach.

- [ ] Создать TestCase с owner/other/staff, private Place и Organization; связи установить через request_join/confirm_join. Написать assertions до кода:

```python
response = client.post(legacy_html_url, {'expected_ownership_version': place.ownership_version})
place.refresh_from_db()
self.assertEqual(place.organization_id, org.pk)
self.assertEqual(response.status_code, 302)
self.assertEqual(response['Location'], preview_url)

response = client.post(legacy_api_url, json.dumps({
    'organization_id': org.pk, 'expected_ownership_version': place.ownership_version,
}), content_type='application/json')
place.refresh_from_db()
self.assertEqual(place.organization_id, org.pk)
self.assertEqual(response.status_code, 409)
self.assertEqual(response.json(), {'error':'confirmation_required', 'preview_url':preview_url})
```

- [ ] Добавить archived/private org-side case: lawful preview200, поля приватного места отсутствуют, receipt можно подтвердить без новых read grants. Чужой/сотрудник/staff не получает receipt и ссылку на приватный target. Все POST проверить enforce_csrf_checks=True.
- [ ] Запустить тесты из guarded disposable PostgreSQL runner, зафиксировать RED на текущем коде: старые POST меняют связь, archived preview не доступен.
- [ ] Добавить helper и ветви **только action=detach**: preview/execution допускают прежнюю mutation authority; connection_result строит для non-readable строки ID/code/complete/executable/redacted=True без `_row` и без display fields; row.redacted управляет отдельным ID-only отображением в общем table include. Для connect/search/current pending прежняя visibility policy сохраняется.
- [ ] Проверить GREEN: archived owner не получает place.view, неизвестный чужой ID не раскрывает метаданные; canonical actor/history/stale/deleted conditions совпадают. Не чинить иные lifecycle findings.

## Task2: закрытие старого транспорта и ссылка из списка

- [ ] Старый HTML handler после существующей авторизации и expected_version validation возвращает `redirect('organization_detach_preview', org_id=org_id, place_id=place_id)`; не вызывает detach. При чужих правах/невалидном target/version сохранить отказ, а не создавать видимость подтверждения.
- [ ] В ownership API импортировать reverse из django.urls и detach_access из organization_connections; только в detach ветви заменить вызов service.detach на detach_access и:

```python
return JsonResponse({
    'error': 'confirmation_required',
    'preview_url': reverse('organization_detach_preview', args=[data['organization_id'], target_id]),
}, status=409)
```

- [ ] В owner_places.html заменить только affiliated_places detach form на GET anchor существующего preview. Переиспользовать подпись/переводы «Отсоединить: посмотреть последствия». Join/confirm/informational blocks не менять.
- [ ] Existing transport tests после нового RED адаптировать к review→consent→result; не заменять проверку сохранения прав проверкой одного302. Canonical detach tests не менять.
- [ ] Проверить оба владельца, staff/чужого, inactive/volunteer, invalid JSON/CSRF/версии/targets. Отказ старого API не должен менять Place/Activity/requests/grants/outbox.

## Task3: последствия и lifecycle проверок

- [ ] Для доступного места оставить существующий impact. Для redacted detach review показывать «Карточка недоступна для просмотра. Подтверждение относится к связи места #ID», общие предупреждения о программах/контактах/доступе; не показывать пустые значения как0 или отсутствие зависимостей. Добавить AZ/EN переводы только этих необходимых строк.
- [ ] Регрессии: consent отсутствует/false; receipt другой action/actor/place/org; просрочен; другой idempotency key; replay старого receipt после повторного согласованного подключения; изменение ownership/content/program/grant/price/group после preview; частичная ошибка coordinator. Snapshot старого намерения не исполняется при conflict.
- [ ] Positive canonical outcome: owner/status/public visibility/photo IDs+order/price IDs+values/group IDs/schedule до и после совпадают. Activity становится локальным approved snapshot, source_program/version сохраняются по нынешним правилам. Network staff теряет place access, direct grant остаётся; нет автоматического переноса в другую сеть.
- [ ] Исполнить targeted organization_connections/concurrency/workspace/ownership/join_visibility/creation_confirmation/drafts. Зафиксировать точные fresh команды/результаты; full suite/image/CI не заявлять без запуска.

## Task4: браузер и handoff

- [ ] Только новые синтетические fixtures. Из «Моих мест» и workspace перейти в review через keyboard; до consent связь неизменна; показать PC/mobile последствия и отмену выходом без POST-confirm.
- [ ] RU/AZ/EN×360/390/768/1440 (+1024/1280 по engineering contract), Tab/Space/Enter, error/empty/loading/result, geometry/icons/console/network. Отдельно две вкладки/expired receipt/change by another editor/repeat. Проверить доступный и redacted lawful review.
- [ ] Снять PC/mobile, сохранить local.diff относительно исходного dirty WORKTREE, source/runtime/HEAD stamps, SHA preservation и PASS/FAIL/NOT RUN. Известные ViewTransition/ORG-06 не маскировать и не исправлять в этом scope.
- [ ] Проверить совпадение source и runtime, сохранность ORG-01/02/03 и остальных входных файлов. Закрыть свой active_run и свои browser sessions. Без commit/push/deploy.

## Приёмочное решение

План охватывает оба подтверждённых обхода и обнаруженное исключение lawful archived/private detach. Legacy API intentional409 — главный предмет согласования. Вариант согласован и реализован локально. Fresh server130/130 и Chromium176 functional PASS; console gate FAIL12 ViewTransition. Детальный отчёт: [ORG-04](../../qa/org-04-fix-2026-10-08.md). Альтернативного обхода consent нет; production/commit/push/deploy NOT RUN.
