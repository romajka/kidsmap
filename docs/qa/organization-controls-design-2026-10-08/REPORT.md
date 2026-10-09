# ORG-09 — проверка и макеты, без внедрения

2026-10-08. Codex /root, последовательная работа. Scope: свежая проверка и конкретный план/PC/mobile макеты. Требование ORG-09 — согласовать их до реализации. [План](../../superpowers/plans/2026-10-08-org-09-controls-design.md).

HEAD `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5`, branch task33-progress. Current runtime8788 matches2761 source +6PO/MO manifest; digest `8e6b6699a0918f58150303dc1958b1297c86ba76ff04ef38a01602547c1d9689`.5651 входной файл побайтно сохранён; application changes0, active_run остаётся NONE. New artifacts только docs. [Срез/сохранность](evidence/preservation.json), [runtime](evidence/runtime-version.json).

## Текущий дефект

Owner synthetic networks50(empty)/60(populated),390/1440. Branch name42px; category/role/scope22px; program/email24px. На телефоне Email/role используют inline native layout вместо связанных вертикальных label+control. CSS styled group inputs/textarea, но не select; program/team не используют общие groups. Overflow в этих4 контекстах не обнаружен. Page heights зависят от наполнения: пустойPC3860/mobile4713, заполненныйPC6301/mobile7668. Навигация — настоящие anchors; не выдаём их за неисправные tabs. [Fresh measurements](evidence/browser_current.json).

## Предложение

Единые48px controls,16px input font, подписи над полями, native select и ясный focus. PC: branch/team две колонки, program полноширинное поле. Mobile: одна колонка, full-width primary buttons, checkbox label targets48px. * только существующая обязательность. Role/scope defaults и бизнес-связи не меняются. Три самостоятельные формы, не новый wizard.

Минимальный scopeA: template/CSS этих трёх forms. ScopeB, sticky anchor navigation, показан отдельно и исключён из A. Рекомендация: утвердить A, навигацию рассматривать отдельно. Не смешивать роли сотрудников, действия приглашения, общий program, место, занятие, группу и тариф.

Прототип: [основной](http://localhost:8789/prototype.html?lang=ru), [отдельная навигация](http://localhost:8789/prototype.html?lang=ru&nav=1). Select language RU/AZ/EN и состояния демонстрационные. Макет не сохраняет, не отправляет API, не пишет storage. Для program/branch demo submit показывает только «Запрос не отправлялся». Категории/названия — вымышленные иллюстрации; реальные backend choices не изменяются.

## Проверки и пределы

| Проверка | Результат |
|---|---|
| Чтение актуальных форм владельца на8788, empty/populated,390/1440 | PASS:4 contexts; defect подтверждён |
| Prototype RU/AZ/EN ×360/390/768/1440 | PASS: control/button targets48px, no overflow |
| Prototype Tab/ArrowDown, role summary, selected branch controls | PASS |
| Prototype error/loading/success/disabled и labelled optional navigation | PASS |
| Финальные prototype browser assertions |77 PASS,0 FAIL,0 pageerrors |
| Screenshots |29 rendered PNG; основные PC/mobile формы визуально просмотрены |
| App creation/save/reload/negative ACL/concurrency после ORG-09 | NOT RUN: приложение не менялось |
| Настоящий screen reader / Firefox / WebKit | NOT RUN |
| Production / external integrations / commit/push/deploy | NOT RUN |

Browser роль авторизована только через isolated QA; актуальные forms не отправлялись (кроме QA login). Prototype hosted отдельным docs-only Python server8789, localhost-only, DJANGO_TESTING=1. Live Django stand8788 остался неизменным. Проверки прототипа не подтверждают создание branch/program/invitation, права, сохранение или публикацию. Результаты прежних ORG fixes не переназваны свежей полной приёмкой.

Команды:

```bash
playwright-cli -s=org09-design-20261008 open http://localhost:8788/qa/
python3 .tmp/org09-design-20261008/run_browser.py browser_current
python3 .tmp/org09-design-20261008/run_browser.py browser_prototype
# current4; prototype77 PASS,0FAIL
```

[Prototype evidence](evidence/browser_prototype.json). Preview PID сохранён в `.tmp/org09-design-20261008/preview.pid`; serving только данный docs каталог на127.0.0.1:8789. Browser automation session закрыта, preview оставлен для согласования. Срок/полнота внедрения не заявлены.

## Макеты

| Форма | PC1440 | Mobile390 |
|---|---|---|
| Новый филиал | [PC](screenshots/ru-1440-branch.png) | [Mobile](screenshots/ru-390-branch.png) |
| Общая программа | [PC](screenshots/ru-1440-program.png) | [Mobile](screenshots/ru-390-program.png) |
| Приглашение сотрудника | [PC](screenshots/ru-1440-team.png) | [Mobile](screenshots/ru-390-team.png) |

[PC overview](screenshots/ru-1440-overview.png), [mobile overview](screenshots/ru-390-overview.png), [ошибки](screenshots/ru-390-error.png), [отправка](screenshots/ru-390-loading.png), [без JS](screenshots/ru-390-disabled.png), [отдельное nav предложение](screenshots/ru-390-nav.png). AZ/EN находятся в том же screenshots каталоге.
