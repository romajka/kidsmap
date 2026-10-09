Работай в /home/ramin/kidsmap. Сначала прочитай AGENTS.md, docs/qa/content-entry-audit-2026-10-06.md и docs/qa/organization-deep-audit-2026-10-08.md. Перепроверь дефект на текущем HEAD/WORKTREE: исторические результаты не считать свежим доказательством. Сохрани чужие изменения. Только DJANGO_TESTING=1, изолированные DB/cache/media и вымышленные данные, без внешних интеграций. Без commit/push/deploy/production.

Исправь только ORG-13 (P2): Редактор нового сеанса показывает старый ServerDraft поверх отправленной заявки.

Подтверждённое воспроизведение: Создать организацию13. Через настоящий drafts API сохранить name_en Older server working copy. Через HTML save отправить Explicit latest submitted на модерацию. Открыть кабинет из чистого сеанса без sessionStorage.
Фактический результат: Draft201, submit302, свежий GET200. Candidate pending содержит Explicit latest submitted; поле редактора Older server working copy. В том же старом браузере local recovery может скрыть дефект.
Нужный результат: Редактор различает отправленную заявку и старую рабочую копию; старый черновик не подменяет успешно отправленные данные молча.

Область и границы изменения: Django drafts + frontend: определить порядок live/candidate/working draft, связать рабочую копию с версией candidate или потреблять только действительно отправленный draft с CAS. Показать выбор восстановления, если данные различаются; сохранить более новый параллельный черновик.
Первопричина: Сначала payload candidate накладывается на live, затем ServerDraft с совпадающим source_version безусловно перекрывает его; версия candidate/явная отправка не учитываются.
Точка входа в код: src/catalog/controllers/organization_workspace.py:268.
Доказательства: docs/qa/organization-deep-audit-2026-10-08/evidence/ и screenshots/, файлы candidate-overlay.json; browser-candidate-overlay.json; screenshots/candidate-overlay-390.png.

Не меняй правила доступа, владения, актуальности связей и публикации ради исправления интерфейса. Связи выполняй через canonical request_join/confirm_join/detach, не прямое присваивание organization_id. Не расширяй права автора/сотрудника. Проверь позитивный сценарий, отказ, повтор и конфликт; UI — RU/AZ/EN, 360/390/768/1440 и клавиатуру. Для ошибок доступа, потери данных и версий добавь регрессию, которая падает до исправления и проверяет пользовательский результат. Простые CSS и текстовые изменения проверь в rendered browser. В конце покажи локальный diff, точные команды/результаты, скриншоты PC/mobile и NOT RUN. Выполни только эту задачу; остальные findings не исправляй.
