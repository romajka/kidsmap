# ACE-19: Проверка доступа к документам падает на отсутствующей категории в фикстуре

Приоритет: **P2**. Роль: **QA automation**. Среда: LOCAL, изолированный PostgreSQL/QA, текущий WORKTREE. Дата: 2026-10-07. Уверенность: высокая.

URL: [локальный сценарий](http://localhost:8783/qa/acceptance-version/). Код стенда: HEAD 2da9d33abbc53d1ac71bcb7e15a0170bef6277d5 + зафиксированный WORKTREE (source digest 146a8499b61ea65cfe70640f38816d1ee83b903f877d46a9bf06fa5a47e27a9a).

## Воспроизведение

1. Запустить IndependentSpecialistSecurityTests.test_live_place_owner_and_organization_grantee_cannot_read_person_documents в изолированном PostgreSQL.
2. Дождаться проверки ограничений после теста.

## Ожидание

Фикстура самодостаточна, тест проверяет ACL.

## Фактический результат

ForeignKeyViolation: category EDU отсутствует. Второй набор: 89 тестов, 1 ERROR.

## Первопричина и область исправления

create_quality_place использует EDU; этот тест не создаёт соответствующую Category. Ошибка проявляется на check_constraints.

Источник: [src/catalog/testcases/test_task33_specialist_security_review.py:190](/home/ramin/kidsmap/src/catalog/testcases/test_task33_specialist_security_review.py:190).

Предлагаемый scope: Исправить только подготовку изолированной фикстуры; проверки прав не ослаблять.

Предлагаемый владелец исправления: **QA/backend tests**. Зависимости: Изолированная Category fixture; assertions и ACL-контракт сохранить. Следующий шаг: согласовать этот отдельный scope, исправить и повторить указанный сценарий на изолированной QA.

## Доказательства

- Свежий вывод изолированного запуска / DOM и source; см. browser-evidence.json и раздел тестов отчёта.

Дополнительные свежие данные: [browser-evidence.json](/home/ramin/kidsmap/docs/qa/content-entry-acceptance-2026-10-07/browser-evidence.json). Исторические design-прототипы не использованы как доказательство.

## Приёмка исправления

Повторить указанный trigger на свежем изолированном стенде, затем проверить зависимые формы/публичные потребители, RU/AZ/EN и применимые PC/mobile/клавиатурные сценарии. Не менять правила организатора, площадки, публикации и доступа ради прохождения теста.

Задача только описана. Во время этой приёмки приложение и тесты не исправлялись.

