# Specialist account shell implementation plan

**Goal:** страницы специалиста воспринимаются как раздел обычного кабинета; пользователь на localhost:8799 получает выбор своей/чужой анкеты.
**Authorization:** прямой follow-up пользователя в текущем чате; указан его локальный стенд 8799. Согласованная ранее логика self/other и проверки личности сохраняется. Production/Git publication не входят в задачу.
**Architecture:** общий account shell с существующими классами шапки/меню из owner_reviews; specialist workspace и editor используют его, внутренние действия остаются вкладками. Перенос в runtime checkout выполняется трёхсторонним слиянием только собственных изменений; CRLF и изменения целевого дерева сохраняются.
**Tech Stack:** Django templates, существующие CSS, HTTP tests и Chromium.
**Spec:** текущие скриншоты пользователя (единая рамка как «Отзывы») и сценарий self/other из текущего чата.

## Confirmed findings
- SPEC-SHELL-01: отдельный sw-layout теряет общую шапку пользователя и основную навигацию.
- SPEC-RUNTIME-01: 8799 запущен из /home/ramin/kidsmap-transfer-2026-10-19, тогда как ранее изменения сделаны в /home/ramin/kidsmap.
- SPEC-RUNTIME-02: файлы специалиста в runtime совпадают с исходной версией предыдущей задачи после нормализации CRLF; новые self/other изменения на стенде отсутствуют.

## Exact application files
- Create `src/catalog/templates/pages/account_shell.html`: общая рамка с существующими account классами.
- Modify `src/catalog/templates/pages/specialist_workspace.html`: вложенный контент, контекстные действия вместо отдельной левой панели.
- Modify `src/catalog/templates/pages/owner_specialist_create.html`: редактор внутри той же рамки, сохраняет выбор self/other.
- Modify `src/catalog/controllers/specialist_workspace.py`: признак текущего account section.
- Modify `src/catalog/templates/pages/includes/account_navigation.html`: активный раздел и на дочерних страницах/legacy create route.
- Modify `static/css/pages/specialist_workspace.css`: адаптация вложенной композиции и вкладок.
- Modify `src/catalog/testcases/test_specialist_self_onboarding.py`: regression общей рамки и выбора при входе через create.

Runtime transfer включает также ровно предыдущий self-onboarding patch (context processor, draft service, account dashboard, listing selector, specialists CSS, recovery JS и новые PO entries); посторонние изменения не переносятся. Исходные файлы обоих checkout сохраняются. Собственный temporary QA backend изолирован; пользовательская synthetic DB не reseed/flush/migrate, текущие данные и авторизация сохраняются. После переноса перезапускается только подтверждённый local server 8799 с тем же runtime/settings. Другие процессы и production не затрагиваются.

## Steps
- [x] Snapshot both checkouts and test RED for account frame.
- [x] Implement common shell and scoped responsive CSS; GREEN targeted/shared checks.
- [x] Three-way merge scoped changes into runtime checkout, preserve its unrelated edits and line endings.
- [x] Compile translations into owned directory, refresh only local runtime code/translation cache.
- [x] Verify actual 8799 browser flows, common menu across reviews/specialists, self/other, desktop/mobile, RU/AZ/EN.
- [x] Record actual source/runtime hashes and checks; leave user's 8799 running.
