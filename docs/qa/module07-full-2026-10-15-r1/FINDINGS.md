# Findings ACCEPT-07, 2026-10-15

## ACCESS-QA-06 — P3 — форма обрезает пробелы в точной фразе удаления

**OPEN. Application patch NOT RUN, требуется отдельное одобрение.**

Роль: ordinary authenticated user с подтверждённым собственным email. URL: `/{ru|en}/account/deletion/<OWN-ID>/confirm/`, AZ без prefix. Только собственные вымышленные аккаунты, local mail, SIMULATED-QA07 policy.

Шаги: native signup → код собственного письма → login/verification → запрос удаления → новый код письма. Контроль: другой неверный текст отклоняется400. Затем показанная фраза с одним дополнительным пробелом слева и справа + правильный код. Wire содержит именно строку с дополнительными пробелами.

Ожидание:400/typed_confirmation error, account active, запрос CONFIRMATION_SENT. Факт:302, SCHEDULED, account inactive. **6/6 native cases RU/AZ/EN ×390/1440 FAIL**,30control observations PASS. [Результаты](whitespace-recheck-r2.js.result.json), [native exit/counts](whitespace-recheck-r2.js.status.json), `screenshots/space-before-*` / `space-result-*` в [manifest](png-manifest.json). Перед before-снимком код очищен; ранее полученная server error относится к контрольному неверному тексту. Источник дефекта — результат следующего POST и readback, а не оставшийся старый текст ошибки на before PNG.

Причина: `src/catalog/forms.py:904`, default `CharField(strip=True)` меняет raw input. View отдаёт сервису cleaned_data; строгая проверка `account_deletion.py:421` получает уже обрезанную строку. Подсказка template:33 и existing test `test_confirmation_phrase_rejects_leading_or_trailing_whitespace` закрепляют точный ввод. [Runtime form proof](whitespace-form-proof.json). Предложенный [HTTP/form regression](access06_proposed_tests.py):4метода,24subtestFAIL,0ERROR — [exit](access06-proposed-RED.status.json), [output](access06-proposed-RED.output.txt). Existing321 +17дополнительных тестов проходят, потому что проверка raw→form→service для этой границы отсутствовала.

P3 обоснование: это нарушение контракта дополнительного подтверждения; правильный email-код и авторизация остаются обязательны. Удаление чужого аккаунта/утечка не подтверждены. Не объявлять общей security-катастрофой.

[Конкретный план](PLAN-ACCESS-QA-06.md): одна строка strip=False только у typed_confirmation в forms.py + новый test_access_qa06_deletion_phrase.py. [Reviewable diff](proposed-ACCESS-QA-06.diff) проходит git apply --check0 и не применён. Scope отдельный от ACCESS05/twoPO/fourentries. Сессии/retention/словарь фраз/код/локализацию и остальные формы не менять.

## Состояние исторических ID

| ID | Состояние | Свежая / связанная проверка |
|---|---|---|
| ACCESS-QA-01 | CLOSED LOCAL |18cells focus trap/settled Escape/opener/visible submit; local mail/reset/new password/replay на RU/AZ/EN mobile/desktop |
| ACCESS-QA-02 | CLOSED LOCAL |native place decline, org decline +18inbox cells, replay/canceled invite deny; existing boundary tests |
| ACCESS-QA-03 = ORG-QA-02 | CLOSED LOCAL, alias |свежий module02-r2 сохраняется; native org role/revoke/pending cancel и stale tab здесь подтверждены, нового patch нет |
| ACCESS-QA-04 | CLOSED LOCAL |native long-email invite,18cells full text/control geometry/select, Space cancel |
| ACCESS-QA-05 | CLOSED LOCAL |approved fourPO entries; 8RED→8GREEN /7target /522native repair PASS; fresh full deletion errors retain translations |
| ACCESS-QA-06 | OPEN |новый raw-input/form boundary,6native FAIL и24proposed subtestFAIL |

QA/environment failures отдельно: [oracle provenance](oracle-provenance.json), [runner correction](runner-correction.json), [queue shadow correction](queue-shadow-correction.json), [initial invalid fixture](whitespace-initial-fixture.json), [isolated dependency](isolated-dependency-manifest.json), [owned interpreter/child proof](owned-venv-proof.json). Они не превращены в application findings и не скрывают06.
