# Новые причины после MOD09–11

| ID | Статус | Что ломается | Точный план |
|---|---|---|---|
| MOD-QA-12 | OPEN / approval pending | Уведомление тёмное, текст выходит за фиксированную рамку; длинное название требует переноса | [CSS:1файл](findings/MOD-QA-12-PLAN.md) |
| MOD-QA-13 | OPEN / approval pending | Четвёртое уведомление блокирует renderer из-за синхронного while с отложенным удалением | [JS+NEWtest:2файла](findings/MOD-QA-13-PLAN.md) |

Три уникальных файла следующего batch: static/admin/css/pages/kidsmap_changelist.css; static/admin/js/kidsmap_notifications.js; NEW scripts/tests/notifications_toast_capacity.test.cjs. Candidate diff/manifests сохранены вне приложения, не применены. Новые причины требуют отдельного scope approval по правилам пользователя; прежнее одобрение MOD09–11 их не включает.

MOD09–11 CLOSED LOCAL в объёме утверждённых планов; вывод MOD10 касается перевода/подстановки, не принятия визуальной рамки или capacity новой причины. Исторический полный ACCEPT-08 с261backendPASS сохраняется; после дополнительных patches только целевые и затронутые общие сценарии.

Поручение пользователя на Git push и применение на сервере принято **после готовности модуля**. Пока MOD12/13 OPEN, условие выкладки не выполнено. Credentials нигде в bundle/Git не сохраняются. Production/commit/push/deploy не выполнялись.
