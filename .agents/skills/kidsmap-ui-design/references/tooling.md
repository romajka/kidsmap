# Инструменты: какой skill/плагин на каком шаге

Установленные плагины (2026-11-05): website-design, audit-suite, icons8, playwright (MCP), ui-consistency, design. Правила KidsMap важнее любых общих рекомендаций этих skills.

| Шаг | Использовать | Зачем |
|---|---|---|
| Аудит существующей страницы | `website-design:web-review`, `design:design-critique`, `audit-suite:audit-as-ux-eng` | Список проблем по приоритету |
| Перед написанием UI | `ui-consistency:finding-patterns` | Как проект уже строит такие страницы, какие компоненты переиспользовать |
| Токены, дрейф цветов/отступов | `icons8:design-tokens`, `ui-consistency:values`, `design:design-system` | Сверить с `tokens.md`, найти лишние значения |
| Направление дизайна главной / лендинга | `website-design:web-design-system`, `frontend-design` | Только в рамках бренда KidsMap |
| Анимации | `audit-suite:web-animation-design`, `icons8:motion` | Значения брать из `motion.md` |
| Финальная полировка деталей | `audit-suite:make-interfaces-feel-better`, `audit-suite:emil-design-engineering`, `icons8:ui-polish` | Выравнивание, тени, состояния |
| Иконки | `icons8:icons8`, `icons8:asset-check` | Только Material Symbols / SVG категорий (см. `icons.md`); icons8-пак — лишь с согласия пользователя |
| Иллюстрации пустых состояний | `icons8:ouch` | Один стиль, согласовать с пользователем |
| Тексты интерфейса | `icons8:ux-writing`, `design:ux-copy` | Конкретно, AZ/RU/EN |
| Состояния и логика экрана | `icons8:ux-check` | empty/loading/error, формы |
| Доступность | `ui-consistency:accessibility`, `design:accessibility-review`, `audit-suite:audit-as-a11y-eng` | Контраст, клавиатура, aria |
| Производительность (карта, анимации) | `audit-suite:audit-as-perf-eng` | Long tasks, перерисовки |
| Браузерная проверка | Playwright MCP (`browser_navigate`, `browser_resize`, `browser_take_screenshot`, `browser_console_messages`, `browser_hover`, `browser_emulate_media`) | Доказательства «до/после» |
| Независимая сверка | `ui-consistency:verifying` (отдельный агент) | Проверка против чек-листа |

Не применять: `audit-suite:vercel-react-best-practices` (проект на Django-шаблонах и vanilla JS, не React), backend/DX-аудиты audit-suite для визуальных задач.
