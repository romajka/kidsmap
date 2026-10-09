# ORG-09 Implementation Plan — три формы управления

**Status:** COMPLETE LOCAL (scope A), 2026-10-08. Согласовано сообщением «дальше» после показа плана и макетов. Scope B не выполнялся. Результат: docs/qa/org-09-fix-2026-10-08.md;464 browser checks,55 backend +28 JS PASS; ограничения и NOT RUN в отчёте.
**Goal:** унифицировать создание филиала, общей программы и приглашение сотрудника: поля не ниже44px, понятные подписи/обязательность, адаптивная сетка и видимый фокус.
**Architecture:** текущие Django формы, native input/select/button и существующие обработчики. Только scoped template/CSS; не создавать второй процесс или новые domain endpoints.
**Tech Stack:** существующие Django templates, CSS, vanilla JS.
**Spec:** docs/qa/organization-deep-audit-2026-10-08/prompts/org-09.md. Там прямо требуется: «Сначала покажи конкретный минимальный план и макеты трёх затронутых форм на PC/mobile. Реализация после согласования этого scope».

## Свежая проверка

LOCAL HEAD2da9d33a, task33-progress, dirty WORKTREE. На текущем8788 в пустой synthetic organization50 и заполненной60 при390/1440: branch name42px; category/role/scope22px; program name/email24px. Переполнения по ширине нет. Высота пустого кабинета3860px наPC/4713px mobile; заполненного6301/7668px (34 pending invitations влияют на высоту). Полные размеры/required — docs/qa/organization-controls-design-2026-10-08/evidence/browser_current.json. Исторические20/22px не выданы за текущие измерения.

## Предлагаемый минимальный scope A

- [x] Template `src/catalog/templates/pages/organization_workspace.html`: добавить общий scoped class только к трём существующим form и их label/error/action блокам. DOM selectors, names, actions, csrf, conditional permissions и data-team-* сохранять. Checkbox не превращать в text input.
- [x] CSS `static/css/pages/organization_workspace.css`: единый48px control (превышает минимум44),16px input font, full width/min-width0, знакомые10px radius/green focus. PC две колонки для branch и первых двух team fields; scope/team notices — на всю ширину. Mobile≤600px одна колонка, подпись всегда над своим полем, primary button на всю ширину.
- [x] Программа: отдельное полноширинное поле названия, кнопка ниже. Подпись «Название программы (AZ)»; не называть программу филиалом/занятием/группой/тарифом.
- [x] Обязательность: branch nameAZ+category; program nameAZ; invite email. Только эти значения помечать *. Role/scope остаются с defaults. Selected places требует хотя бы одного актуального филиала; пояснение не меняет серверный gate. Не требовать новый адрес, фото или перевод на этом экране.
- [x] Team: ясные роли/summary и scope, checkbox rows минимум44px (макет48). Состояния ORG-07/08, pending list, loading, failed read/uncertain response и readonly retry сохранять. Disabled visual state должен отличаться от enabled, native disabled не заменять одним ARIA.
- [x] Existing validation output связать с конкретным control/label там, где уже выводится. Видимый focus:focus-visible; labels/native select не заменять custom dropdown. Не добавлять новые server validations, autosave promises или changes to role actions.

### Границы / неизменные правила

Owner-only team form; can_create_branch и can_manage_programs прежние. Employee получает только разрешённые ему формы. Все joins/confirms/detach остаются canonical; здесь они не меняются. Программа создаётся существующим POST и переходом в редактор; branch — текущий workflow; invitation не выдаёт grant. Duplicate protection, publication, ownership and actuality rules unchanged. RU/AZ/EN используют существующие категории и тексты ролей; иллюстративные категории прототипа не заменяют queryset.

### После согласования — приёмка

- [x] Fresh snapshot/active_run; preserve dirty files + exact source/runtime hashes; isolated synthetic fixtures only.
- [x] Render owner/employee permitted forms, empty/populated network, RU/AZ/EN ×360/390/768/1440. Проверить control/checkbox/action targets≥44px, label association, wrap/overflow, Tab/arrows/Enter, focus and disabled.
- [x] На isolated data: branch creation / duplicate refusal / new program / invitation success,400/403/409, reload, selected scope, loading/double action, two tabs and uncertain/read failure. Не выдавать prototype submit за настоящее сохранение.
- [x] Для новых ошибок доступа/потери данных/versions — meaningful RED/GREEN. Простое CSS/layout проверять rendered browser; существующие targeted permissions/ORG-07/08 regressions повторять по затронутому слою, без mirror-тестов CSS.
- [x] PC/mobile screenshots, local diff, exact PASS/FAIL/NOT RUN. No commit/push/deploy/production/external email.

## Отдельное предложение B — длинная навигация

В минимальный scope A не включено. Рекомендую сначала A. Якоря — допустимый текущий контракт, а не сломанные tabs. Их можно подписать «Разделы страницы»; отдельный макетB показывает sticky anchor menu PC и горизонтальное меню mobile. Все sections остаются в DOM; несохранённый ввод не уничтожается, keyboard переход к ошибке не требует скрывать формы. Не заменять на настоящие tabs/многошаговый workflow без отдельного согласования. Полный кабинет включает также сведения; макет показывает только три затронутых формы.

## Артефакты на согласование

- docs/qa/organization-controls-design-2026-10-08/prototype.html (+ prototype.css/prototype.js): standalone mockup, no POST/API/storage.
- http://localhost:8789/prototype.html?lang=ru — основной вариант.
- http://localhost:8789/prototype.html?lang=ru&nav=1 — отдельное nav предложение.
- Query lang=az/en; state=error/loading/success/disabled. Это иллюстративные состояния, не runtime backend proof.
- 29 rendered PNG: три формы PC/mobile RU/AZ/EN, overview и дополнительные состояния.
