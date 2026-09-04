# KidsMap Agent Orchestration

Используй специализированных subagents как независимых проверяющих, когда задача соответствует их области.

## code-reviewer

Вызывать после существенных изменений кода, особенно если:
- изменено несколько файлов;
- был рефакторинг;
- исправлялся сложный баг;
- изменялась бизнес-логика;
- менялись Python/JavaScript/template зависимости.

Основная задача:
независимо проверить git diff, регрессии, архитектуру и корректность реализации.

Не вызывать для тривиального изменения текста или одного очевидного CSS-отступа.

## django-reviewer

Вызывать, если изменялись:
- Django models;
- migrations;
- forms;
- validation;
- views;
- services;
- ORM;
- admin;
- permissions;
- backend business logic.

Особенно обязательно при изменениях данных, тарифов, возраста, расписания, прав пользователей и публикации карточек.

## frontend-reviewer

Вызывать после существенных визуальных изменений:
- templates;
- CSS;
- UI components;
- карточки;
- расписание;
- фильтры;
- формы;
- профиль;
- responsive layout.

Он должен независимо оценить:
- hierarchy;
- spacing;
- alignment;
- typography;
- consistency;
- mobile;
- accessibility;
- соответствие KidsMap UI.

## browser-qa

Вызывать, когда результат можно и нужно проверить в реальном браузере.

Особенно после:
- frontend изменений;
- исправления пользовательского бага;
- изменения формы;
- изменения JS;
- фильтров;
- карточек;
- расписания;
- авторизации;
- пользовательских сценариев.

Использовать Playwright и/или Chrome DevTools, когда они доступны.

Проверять фактическое поведение, а не только исходный код.

## security-reviewer

Вызывать при изменениях:
- authentication;
- authorization;
- permissions;
- object ownership;
- user-generated content;
- uploads;
- API;
- admin actions;
- sensitive data;
- внешних URL;
- CSRF/XSS-sensitive кода.

Не вызывать для каждой CSS-правки.

# Обязательная логика после реализации

Для существенной задачи:

1. Основной агент реализует изменение.
2. Вызывает релевантного reviewer/subagent.
3. Reviewer должен анализировать результат независимо.
4. Если найдены P0/P1/P2 или Critical/High/Medium проблемы:
   - основной агент исправляет их;
   - выполняет повторную проверку.
5. Не завершать задачу только потому, что код изменён.
6. Перед утверждением "готово" получить фактическое подтверждение соответствующими тестами или проверкой.

# Выбор нескольких агентов

Разрешено использовать несколько агентов для одной задачи.

Примеры:

Изменение Django формы + UI:
django-reviewer
→ frontend-reviewer
→ browser-qa

Изменение permissions:
django-reviewer
→ security-reviewer
→ code-reviewer

Большой frontend redesign:
frontend-reviewer
→ browser-qa

Сложный backend refactor:
django-reviewer
→ code-reviewer

Полная функция с frontend + backend:
django-reviewer
→ frontend-reviewer
→ browser-qa
→ code-reviewer

# Не создавать лишнюю бюрократию

Не вызывать всех агентов для каждой мелкой задачи.

Количество reviewer должно соответствовать реальному риску изменения.

Простая правка:
может не требовать subagent.

Средняя задача:
обычно 1 reviewer.

Существенная задача:
обычно 1–3 reviewer.

Security/data/permissions изменения:
соответствующий специализированный reviewer обязателен.
