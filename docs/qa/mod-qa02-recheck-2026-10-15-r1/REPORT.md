# MOD-QA-02 — PLAN / CONFIRMED OPEN

2026-10-15, LOCAL dirty WORKTREE. Выполнен свежий recheck и подготовлен конкретный [implementation plan](IMPLEMENTATION_PLAN.md), [diff](proposed-MOD-QA-02.diff), [семифайловый manifest](proposal-manifest.json). **Application fixes пока0, approval этого scope pending. MOD-QA-02 не закрыт.** MOD01 scoped LOCAL PASS сохранён; остальной модуль08/full ACCEPT08 ещё не выполнен.

Один исполнитель /root; канонические kidsmap-orchestrator/frontend-admin/django-reviewer/browser-qa применены последовательно, без независимых специалистов. Definitions .agents/agents/*/agent.md, текущий registry/engineering/audit contracts. Применены systematic-debugging, writing-plans, KidsMap UI/frontend-design, TDD и verification; Playwright CLI — настоящий Chromium. Пользователь запросил начать02; правило отдельных PLAN→approval сохраняется. Ни старое MOD01, ни CSS/module07 approval не разрешает этот patch.

## Snapshot / сохранность

Root `/home/ramin/kidsmap`; HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`, dirty WORKTREE, `active_run: NONE`. [Entry](entry.json):30216project-file hashes,66existing container identities/states/ports,5knownHTTP identities. Ни reset/clean/stash/active_run assignment, ни рестарт чужих процессов не выполнялся. Новые собственные QA/docs только в этом каталоге и ignored scratch; guide получил одну явно отделённую pending status note, [inverse proof](guide-edits.json). Финальная сверка в [verification](verification.json). Не утверждается непрерывность более старых исчезнувших процессов, уже NOT VERIFIED в module07.

## Причина / актуальные источники

`src/catalog/domain_admin/volunteer.py:moderation_hub_detail` сначала вызывает `moderation_hub.detail`, затем рендерит `hub_detail.html`. `moderation_hub._revision_row` строит `changes` как `(label,current,payload)`; template выводит эти values обычным escaped текстом. В runtime нет ни одного image внутри comparison, хотя storage содержит корректные декодируемые current/candidate main/cover/двеgallery. Payload candidate2,1 валиден: числовой order2,1 должен отображаться1,2, как после apply/public readback. Это presentation SOURCE defect/P2, не поломка сохранения и не production proof.

Legacy `domain_admin.volunteer.review` имеет preview main/cover, но иной reviewer gate и не решает gallery; переносить его superadmin-only права на штатный hub нельзя. Новый presenter планируется только после существующей авторизации detail. Приватные документы не часть Place photo/gallery, их download ACL не меняется. Не добавлять media/download route; не превращать raw payload names в произвольные URLs.

[Graph/source map](graph-and-source.json): актуальный graph root/generation/full index; проверена coverage пяти критических source paths, graph best effort/часть inventory truncated. Dynamic import/caller подтверждён actual source, а не отсутствием graph edge. [Context7](storage-docs.txt): official Django6.0 storage.exists/url; url само по себе не доказывает существование/декодирование.

## Свежий собственный профиль

PG `127.0.0.1:43781`, HTTP `127.0.0.1:32937`, DB/user `mod02_recheck_r1`, container+volume `mod-qa02-recheck-2026-10-15-r1-pg`. Это зафиксированные значения этого запуска, при продолжении перепроверить. Создан новый profile/DB/cache/media/private-media/filebased-email, fictional4users/1place/1revision; не использована старая DB/browser session.

`runtime.py` очищает окружение до setup, `DJANGO_TESTING=1`; manage.py/.env/production credentials не читаются. Собственные credentials только ignored scratch mode600, directory700. Socket guard допускает только свойPG; браузер только свой origin. Это guard конкретных QA процессов, не host-wide firewall и не контроль transport инструментов. Внешние fonts BLOCKED, внешние интеграции отключены. Default account-deletion policy inactive, не включалась.

Новый Python3.12.3 interpreter, Django6.0.2 из существующего read-only checkout env. pypdf6.20.1 скопирован только в новый own python-deps после побайтовой проверки [manifest](dependency-manifest.json); shared installations не менялись.175migrations в новой DB. [Runtime-info](runtime-info.json), startup/source [proof](runtime-source-final.json): фактический PID/argv/cwd/два app module origins, загруженный cached hub_detail origin/hash,846bounded source paths совпадают с pinned disk. Entry охватывает более широкий проект,846 не объявлены полным inventory.

Текущие RU/AZ/EN PO собраны `scripts/build_isolated_locales.py` в новый собственный каталог: build0,verify0; [manifest](locale-manifest.json). Sole LOCALE_PATHS до django.setup, фактически открыты own3MO (Django builtin catalog отдельно); shared MO не перезаписаны.

## Воспроизведение / exact commands

[Commands/exits/durations](commands.jsonl), [launch](launch.py), [source](runtime-source-final.json). `capture.py` и browser `open/goto` выполнены напрямую; capture stdout/counts подтверждены entry/final gate, own browser open identity в ignored CLI snapshot; остальные native commands ledger содержит путь к фактическому JS (`drive.py` передаёт его TEXT, path placeholder не literal аргумент).

Initial fixture:8собственных raster images, каждый существует и декодируется, [proof](fixture-media-proof.json). Live/place/gallery initial setup; draft→pending через canonical `volunteer_proposals.propose`, не прямой status update. [Fixtures](fixtures.json) явно обозначает setup, **native owner/volunteer upload/draft/reload/submit NOT RUN** на этом PLAN.

[Native result](native-recheck.js.result.json):261observations = **189PASS controls/72expected sourceFAIL/0NOT RUN**, 36maincells = admin/reviewer×actualRU/AZ/EN×360/390/768/1024/1280/1440. Native login→language menu/set_language→queue→real pending link→detail→Tab approve→back. Проверяется фактический html.lang, AZ выбран реальным меню (unprefixed /admin по умолчанию RU, это учтено). В каждом cell три valid changes и0img вместо8; отдельно0gallery previews вместо4. Keyboard existing actions и native back проходят. CLI exit0 означает выполненную автоматизацию, **не отсутствие дефекта**. Необъяснённых page/console/local network errors0;236blocked external requests и их236console records сохранены. Source содержит внешний Google Fonts CSS; diagnostic records этой матрицы различают local/external, но не сохраняют полный URL inventory, поэтому все236 не атрибутируются одному host/font. Никакие approve/reject/save не нажимались. [Readonly state](state-final.json) до/после совпал:1place/1pending revision/2live gallery, неизменённый domain hash. Login/session writes — только setup.

[Regression draft](proposed_test_mod_qa02_hub_media.py): сначала7methods/13assertion failures/0errors, [first output](proposed-RED.output.txt). Один FAIL — QA mismatch int freshly-created fixture vs Decimal после DB read. Сохранён весь первый test; [correction](harness-correction.json) добавила только setup refresh_from_db, assertions не менялись. Повтор [RED-r2](proposed-RED-r2.status.json):7methods,12expected assertion failures,0errors, exit1,67.946s process/6.489s test runtime. Контроли ACL и отсутствия GET mutation проходят. Test находится в QA docs, permanent app test пока не установлен. No postpatch GREEN.

## Evidence / план / пределы

[36PNG manifest](png-manifest.json): все PREPATCH_RED. Реально просмотрены desktopRU/admin1440 и mobileAZ/reviewer360, [visual review](visual-review.json); не заявляется ручной просмотр всех36. Изображения подтверждают пути/raw gallery вместо фото; новый дизайн пока не отрендерен.

[План](IMPLEMENTATION_PLAN.md): два existing files +пять новых, минимальный detail-only presenter/partial/scopedCSS/scopedJS/regression. Main/cover/gallery previews, стабильный order, full-size keyboard links, safe names/field storage, localized empty/unavailable and decode-error state. Shared text consumers/ACL/POST error handling проверяются targeted, существующие assertions не ослабляются. Новых схем/прав/PO/routes/upload/publish семантики нет.

**NOT RUN:** application patch/GREEN; native author upload/draft/reload/submit/approve/reject/public after-approval readback; новые fallback/empty/corrupt/private-document download и postpatch mobile layout; full08/global/module09, real external services, cross-browser/screen-reader, production/commit/push/deploy. Всё это не выдаётся за выполненное. После approval обязательна acceptance плана; full08 один раз после его задач. Следующий шаг — явное одобрение [этого scope](IMPLEMENTATION_PLAN.md), [handoff](next-prompt.txt).
