# ACE-17: Текст удаления специалиста не читается на белом фоне

Приоритет: **P2**. Роль: **модератор**. Среда: LOCAL, изолированный PostgreSQL/QA, текущий WORKTREE. Дата: 2026-10-07. Уверенность: высокая.

URL: [локальный сценарий](http://localhost:8783/admin/catalog/specialist/4/change/). Код стенда: HEAD 2da9d33abbc53d1ac71bcb7e15a0170bef6277d5 + зафиксированный WORKTREE (source digest 146a8499b61ea65cfe70640f38816d1ee83b903f877d46a9bf06fa5a47e27a9a).

## Воспроизведение

1. Открыть редактор на PC и телефоне.
2. Посмотреть действие удаления в панели сохранения.

## Ожидание

Название действия читается в обычном состоянии.

## Фактический результат

Computed color=rgb(255,255,255), background=transparent; фон панели белый, текст почти невидим.

## Первопричина и область исправления

Общий km-btn--danger задаёт color:white!important; CSS специалиста меняет фон на прозрачный, цвет без important проигрывает.

Источник: [static/admin/css/kidsmap_admin_forms.css:182](/home/ramin/kidsmap/static/admin/css/kidsmap_admin_forms.css:182).

Предлагаемый scope: Устранить конфликт стилей в существующей панели и проверить остальные потребители кнопки.

Предлагаемый владелец исправления: **frontend-admin**. Зависимости: Общий CSS и CSS специалиста; опасное действие должно оставаться различимым. Следующий шаг: согласовать этот отдельный scope, исправить и повторить указанный сценарий на изолированной QA.

## Доказательства

- [matrix-specialist-admin-ru-1440.png](/home/ramin/kidsmap/docs/qa/content-entry-acceptance-2026-10-07/screenshots/matrix-specialist-admin-ru-1440.png)
- [matrix-specialist-admin-ru-360.png](/home/ramin/kidsmap/docs/qa/content-entry-acceptance-2026-10-07/screenshots/matrix-specialist-admin-ru-360.png)

Дополнительные свежие данные: [browser-evidence.json](/home/ramin/kidsmap/docs/qa/content-entry-acceptance-2026-10-07/browser-evidence.json). Исторические design-прототипы не использованы как доказательство.

## Приёмка исправления

Повторить указанный trigger на свежем изолированном стенде, затем проверить зависимые формы/публичные потребители, RU/AZ/EN и применимые PC/mobile/клавиатурные сценарии. Не менять правила организатора, площадки, публикации и доступа ради прохождения теста.

Задача только описана. Во время этой приёмки приложение и тесты не исправлялись.

