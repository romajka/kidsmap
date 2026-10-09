# Админка: предварительный UX-аудит

Дата: 2026-10-05. Execution identity: root, последовательная проверка, без независимого reviewer. Definition/reference: `.agents/rules/audit-contract.md`; scope — визуальные экраны организаций, специалистов, мероприятий, настройки видимости и пустая очередь модерации мероприятий. LOCAL HEAD `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5`, branch `task33-progress`, dirty WORKTREE, localhost:8780. Production NOT RUN. Код приложения не изменён.

## 1. Состояние области

Проверено 8 экранов на 1440×900 и 390×900: Organization list/view org2, Specialist list/edit4, Event list/add, SiteVisibilitySettings change, ModerationEvent list. Синтетический локальный demo_moderator; организация открылась в режиме просмотра — отсутствие редактирования само по себе не признано багом, права BusinessEditor отдельно регулируются business_team.

## 2. Сильные стороны

Статусы/счётчики, боковая навигация, группировка формы специалиста и отдельная зона сохранения. SiteVisibilitySettings объясняет эффект переключателей. На исследованных экранах горизонтального переполнения документа нет; широкие таблицы прокручиваются внутри собственного контейнера.

## 3. Реальные проблемы

| ID | Priority | Evidence, source, impact | Next step |
|---|---|---|---|
| ADM-SPEC-01 | P2 | Edit Specialist4 показывает вместо владельца строку dict: name/label/help_text/field/is_hidden. `templates/admin/catalog/specialist/change_form.html:115` выводит `field.field`, не учитывая readonly в этом блоке; в блоке модерации :379 это уже учтено. | Правильное readonly отображение и проверка остальных readonly полей. |
| ADM-EVENT-01 | P2 | На 390 px CTA «Добавить мероприятие» перекрывает заголовок, описание сжато до узкой колонки. Screenshot events-390. | Перестроить header/CTA на mobile, проверить соседние changelist headers. |
| ADM-ORG-01 | P2 | RU список содержит Organizations, status, CONTENT VERSION, UPDATED AT и «Добавить organization». `domain_admin/business.py`, generic BusinessEditor, model metadata/changelist. | Локализация заголовков/полей/кнопок и человекочитаемые названия. |
| ADM-ORG-02 | P2 | Mobile Organization view: «ФилиалыПрограммыСотрудники» без визуального разделения, крупные блоки публикации/связей отличаются от остальной формы. `templates/admin/catalog/business/change_form.html`, related_links. | Общая компоновка связанных разделов, доступные отдельные CTA, аккуратные статусы. |
| ADM-DENSITY-01 | P3 | Specialist edit высота 6963/8182 px (desktop/mobile), Event add 4365/6179 px. Specialist table scroll1284 при контейнере1074 на desktop, Event1505/1074. Это не горизонтальное переполнение документа, но усложняет просмотр. | Навигация по разделам, компактные поля и приоритетные колонки, мобильные строки/карточки без скрытия необходимых действий. |

Environment: LOCAL dirty WORKTREE; reproducibility: screenshots/DOM and source; confidence high для проявлений, root cause SPEC — source inference. Ownership/dependencies: будущий admin UI scope; generic templates и права бизнес-сущностей требуют отдельной проверки.

## 4. Tech debt

Сочетание generic Jazzmin, кастомной формы специалиста и BusinessEditor даёт разные стили/термины. DOM-проверка маленьких select не является finding: select2 прячет исходные controls, поэтому ширина1px сама по себе не баг.

## 5. Risks

Нельзя чинить недоступные действия расширением прав, менять publication/candidate/ownership contracts ради внешнего вида, делать приватные документы доступными или возвращать факультативную публичную отметку «Проверено». Business ownership verification — отдельный внутренний контракт. Нужна проверка общих CSS на соседних разделах. Любое сохранение/модерация для QA только в изолированных fixtures.

## 6. Dead/legacy candidates

Не установлены. Удаление общих шаблонов/стилей не обосновано этим обзором.

## 7. Tests gaps

Executed: 16 rendered contexts, DOM sizes, screenshots и targeted source inspection. Фото и данные синтетические. Никаких POST сохранения/модерации/удаления не выполнялось. Непустая очередь модерации, остальные роли/permissions, invalid submissions/409, keyboard/focus/contrast, AZ/EN, intermediate widths, весь sidebar, full suite NOT RUN. Этот отчёт не подтверждает отсутствие всех багов.

Evidence: ignored `.tmp/admin-ux-audit/` screenshots `organizations-1440.png`, `organization-edit-390.png`, `specialist-edit-1440.png`, `events-390.png`, `visibility-390.png` и остальные именные экраны. Browser command: `playwright_cli.sh -s=visual-demo run-code`, page.goto/setViewportSize/screenshot/evaluate; read-only navigation.

## 8. Recommendations

Отдельная задача для всей визуальной системы админки с этапами: карта страниц/виджетов → общий стандарт и макеты → согласованная реализация разделами → браузерная приёмка. Сначала confirmed defects трёх сущностей, затем общие таблицы/формы/модерация и оставшийся sidebar. Прогонять PC/mobile, длинные/пустые/ошибочные состояния, реальные действия в disposable fixtures, роли и отсутствие побочных изменений. Перед реализацией пользователь должен согласовать конкретный план/макеты.

## 9. Приоритеты

P0/P1 не установлены. P2 — служебный dict в owner, наложение mobile header, mixed localization, слипшиеся links. P3 — плотность/консистентность и длинные формы. Реализация не начата.
