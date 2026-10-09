# ORG-11 — доступные имена организации

APPROVED IMPLEMENT: пользователь поручил следующий пункт сообщением «дальше» после ORG-10. Только ORG-11, без commit/push/deploy/production.

1. RED на текущем стенде: новая synthetic сеть7 филиалов через canonical services; RU/AZ/EN, owner/employee. Проверить aria-label и реальное доступное имя пагинации, аналогичные literals на organization pages; сохранить входной WORKTREE.
2. Минимальное template исправление: пагинация как native nav с именем в текущем языке; аналогичный literal RU имени поиска мест на organization index также перевести. Использовать текущие inline RU/AZ/EN ветки; JS/CSS/domain/locales не менять. Другие найденные проблемы не исправлять.
3. GREEN в rendered browser: языки/360/390/768/1024/1280/1440, страницы1/2, поиск/пустой результат, клавиатура, повторное открытие, employee/outsider. Проверить отсутствие POST и сохранность старых и новых domain данных, существующие targeted rights/conflict regressions. PC/mobile screenshots, diff и exact PASS/FAIL/NOT RUN.

COMPLETE LOCAL 2026-10-09: template2lines; RED3P/12F → GREEN15P; matrix478P + separate focus FAIL36, targeted47P. Report docs/qa/org-11-fix-2026-10-09.md.
