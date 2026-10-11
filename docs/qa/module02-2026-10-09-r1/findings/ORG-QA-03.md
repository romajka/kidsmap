# ORG-QA-03 — административный выбор карточек выходит за экран на 1024px

OPEN, P2, высокая уверенность. Свежий локальный Chromium; baseline текущего WORKTREE, regression не установлена. Роль: администратор, первый шаг массового подключения. URL `/admin/catalog/place/?q=QA02+BULK`.

Открыть список с боковой панелью на1024×950, найти QA02 BULK, выбрать карточку клавиатурой. Toolbar поиска/сортировки/колонок не помещается. Ожидание: доступные controls в пределах рабочей области, локальный scroll для широкой таблицы. Факт: горизонтальный overflow всего документа; сортировка/колонки обрезаются справа.

RU document width1240 (+216px), AZ1158 (+134px), EN1150 (+126px), viewport1024. Toolbar660px, form630px, formScrollWidth893/811/803px, computed flexWrap=nowrap. [Geometry proof](../admin-overflow.result.txt), [fresh72 admin states](../admin-render-proof.result.txt), [RU screenshot](../screenshots/moderator-ru-1024-admin-selection.png), [AZ](../screenshots/moderator-az-1024-admin-selection.png), [EN](../screenshots/moderator-en-1024-admin-selection.png).

Причина подтверждена source/computed styles: `static/admin/css/pages/kidsmap_changelist.css:467` задаёт nowrap; wrap включается только при viewport≤900 (`:989`), хотя на1024 sidebar оставляет660px. Template search panel находится в `src/catalog/templates/admin/catalog/includes/km_changelist_search_panel.html:44`; connect control — `.../place/change_list.html:96`. Другие проверенные ширины данного сценария не дали document overflow.

P2: промежуточный desktop/tablet размер ломает доступность инструментов выбора перед массовым подключением. Данные/согласия не повреждены. Ответственные frontend-admin/layout. Исправлять по доступной ширине контента; не маскировать overflow глобальным hidden и не менять бизнес-сервис. Следующий шаг — отдельный repair scope.
