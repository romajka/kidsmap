# MOD-QA-02: предпросмотр фото в центре модерации — Implementation Plan

**Status:** PLAN / CONFIRMED OPEN. Implementation approval pending. Этот план ещё не применён.

**Goal:** Проверяющий видит текущие и предложенные главное фото, обложку и галерею в порядке публикации, может открыть полный снимок и отличить удалённое/отсутствующее/повреждённое фото.

**Architecture:** Только presentation уже разрешённого detail. После существующей `moderation_hub.detail → query → reviewer_scopes` к найденной строке добавляется `display_changes`. Новый read-only helper типизирует только три публичных image-поля Place; остальные поля/сущности остаются обычным escaped текстом. Не менять publication payload/validation/version/ACL/approve/reject.

**Tech stack:** текущие Python3.12.3 / Django6.0.2, Django templates, существующий field storage, маленькие scoped CSS/JS без зависимостей.

**Spec:** [исторический finding](../module08-2026-10-10-r1/findings/MOD-QA-02.md), [repair prompt](../module08-2026-10-10-r1/repair-prompts/MOD-QA-02.txt), свежий [REPORT](REPORT.md). Исполнение последовательно в этом чате; без subagents/commit/push/deploy/production.

## Snapshot и границы

`/home/ramin/kidsmap`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, `task33-progress`, dirty WORKTREE, `active_run: NONE`. Сохранить исходный чужой WORKTREE/стенды/артефакты, не присваивать active_run. Разрешение MOD01 на новый scope не переносится. Этот PLAN закрывает только причину MOD-QA-02; другие MOD IDs/full08 не принимаются.

## Точные файлы — семь

| Действие | Файл | Ответственность |
|---|---|---|
| Изменить | `src/catalog/services/moderation_hub.py` | Только две строки импорта/call presenter после успешного поиска разрешённого detail; индекс/очередь не трогать. |
| Создать | `src/catalog/services/moderation_media.py` | `comparison_rows(row)` и read-only helpers: main/cover/gallery, field storage, проверка имён, отсутствие файлов, порядок галереи. |
| Изменить | `src/catalog/templates/admin/volunteer/hub_detail.html` | Подключить два scoped asset; типизированные before/after cells; локальные подписи колонок для узкой ширины. |
| Создать | `src/catalog/templates/admin/volunteer/hub_media.html` | Нумерованный список изображений и escaped captions, ссылка на полный размер, empty/unavailable. |
| Создать | `static/admin/css/pages/moderation_media.css` | Только comparison этой страницы: thumbnails object-fit:contain, max-width, mobile stacking с подписями Сейчас/Предложено. |
| Создать | `static/admin/js/moderation_media.js` | Только img error/cached decode failure: скрыть неисправную ссылку/картинку, показать локализованный fallback. |
| Создать | `src/catalog/testcases/test_mod_qa02_hub_media.py` | Семь предложенных regression methods через реальный detail endpoint; существующие assertions не менять. |

Полное reviewable содержимое: [diff](proposed-MOD-QA-02.diff), [точный manifest/SHA](proposal-manifest.json), [готовые файлы](proposed/). Проектные файлы ещё не менялись. QA runtime/evidence/docs остаются в новом собственном каталоге. Shared CSS/JS, legacy review, models/schema/migrations/PO/permissions/storage config/routes/editor upload и publication services в scope не входят. Существенное расширение — отдельное согласование.

## Шаги реализации

- [ ] **1. Проверить approval и исходники.** Сверить SHA семи targets с manifest: существующие файлы должны совпасть, пять новых отсутствовать. Сверить HEAD/branch/active_run; сохранить новые чужие изменения. При drift остановить зависимый patch и объяснить расхождение.
- [ ] **2. Установить неизменённый предложенный test.** `proposed/test_mod_qa02_hub_media.py` → указанный application test path. Повторить его RED в собственном test DB текущего профиля после проверки его принадлежности/изолированности/source/locales. Уже выполненный PLAN RED ниже сохранён; сравнить SHA assertions. Не переносить старые PID/порты без проверки.
- [ ] **3. Применить ровно предложенный diff.** `comparison_rows(row)` возвращает список `{label, before, after, media, before_images, after_images}`. Только известные Place fields становятся media; affiliation/organization/program сохраняют text rendering. `detail()` добавляет это после авторизации и существующего object lookup, в том числе на повторном render ошибочного POST. `row.changes/current/candidate` и candidate/live не мутировать.
- [ ] **4. Проверить изображения безопасно.** Разрешены только нормальные относительные `places/...` raster names (конкретный список suffix в diff). Запретить URL/absolute/traversal/backslash/percent-encoded/path-with-query/PDF/SVG/private-root. Использовать storage соответствующего model field, сначала exists, затем url; отказ/ошибка storage → unavailable без raw path. Разрешены только безопасные relative URL или http(s) URL, возвращённые доверенным storage. Новых media/download endpoints нет. Галерею сортировать стабильно по `order`, как public apply/readback; подписи экранировать. Отсутствующее значение/пустая галерея — «Фотографии не добавлены», недоступный/повреждённый файл — «Фото недоступно». Все новые UI strings уже имеют активные RU/AZ/EN переводы; PO/shared MO не менять.
- [ ] **5. Проверить доступность.** Полный размер открывается обычной ссылкой в новой вкладке с noopener/noreferrer и доступным именем (current/proposed, номер, подпись). Существующий focus-visible contour сохраняется. Нет нового modal/ловушки фокуса/автоперевода фокуса. Для decode error скрыть broken link и показать текст; не рисовать успешный preview по одному HTTP200.
- [ ] **6. Выполнить один targeted GREEN.** Семь новых methods + шесть существующих ниже. При новом дефекте QA классифицировать source/baseline/environment/harness, сохранить первый output. Не ослаблять assertions. Заново полный module07/08 или global corpus не запускать.
- [ ] **7. Native regression после patch.** Выполнить следующую acceptance, сохранить реальные PNG/manifest, readback и точные commands/exits. Показать исправленный desktop/mobile кадр, отметить объём ручного просмотра. Если acceptance не выполнена — ID остаётся OPEN/NOT RUN.
- [ ] **8. Итог.** Новый уникальный fix REPORT/verification: точный diff, isolation/process/source/locale proof, RED→GREEN, counts, console/network, сохранность чужих файлов/shared MO/стендов/HEAD/active_run и NOT RUN. Обновить только текущую строку MOD02 со ссылкой, сохранив исторические отчёты. Полный ACCEPT-08 один раз после остальных задач.

## Уже выполненный RED

[Native](native-recheck.js.result.json): 36cells = admin/reviewer × RU/AZ/EN ×360/390/768/1024/1280/1440. 189 control PASS,72expected source FAIL (2preview assertions ×36cells),0NOT RUN;36PNG. Реальные login/language-menu/queue-link/back/keyboard переходы. Сервисом создана валидная draft→pending заявка; все8fixture files существуют и декодируются. Native author upload/draft/reload/submit и решения модерации на этом PLAN ещё NOT RUN.

[Предложенные tests](proposed-RED-r2.status.json):7methods,12ожидаемых assertion failures,0errors; контроль авторизации и сохранности данных проходит. Первый запуск сохранён: дополнительный harness FAIL был вызван int в объекте freshly-created fixture против Decimal после DB read. Единственная коррекция — refresh_from_db в setup перед before snapshot; assertions не менялись. [Разбор](harness-correction.json).

## Точные targeted tests после approval

Запускать через проверенный собственный runtime с `DJANGO_TESTING=1` и отдельным test DB; `<own-python> <own-runtime> test` получает эти селекторы:

```text
catalog.testcases.test_mod_qa02_hub_media
catalog.testcases.test_task33_volunteer_hub.VolunteerHubTests.test_hub_get_post_ajax_and_version_conflict
catalog.testcases.test_task33_volunteer_hub.VolunteerHubTests.test_hub_program_preview_lists_affected_branches
catalog.testcases.test_task33_volunteer_hub.VolunteerHubTests.test_hub_respects_distinct_content_and_affiliation_reviewer_permissions
catalog.testcases.test_task33_volunteer_hub.VolunteerHubTests.test_missing_hub_item_is_not_a_server_error
catalog.testcases.test_task33_publication.PublicationTests.test_gallery_delete_is_pending_until_approval
catalog.testcases.test_task33_specialist_screens_security.SpecialistScreensSecurityTests.test_staff_claim_only_and_document_only_permissions_are_separate
```

Это13methods, не13suites и не весь модуль. Current own executable: `/home/ramin/kidsmap/.tmp/mod-qa02-recheck-2026-10-15-r1/venv/bin/python`; runtime: `/home/ramin/kidsmap/docs/qa/mod-qa02-recheck-2026-10-15-r1/runtime.py`. При новом fix runtime путь явно записать и source/locales снова подтвердить до использования.

## Native acceptance после approval

1. **Основная матрица36cells:** admin/reviewer ×3реально выбранных языка ×6ширин. Native queue→detail, current/proposed main+cover+gallery; восемь реально decoded img с правильными URL и before/after. Галерея current1,2/candidate1,2, несмотря на исходный payload2,1. Таблица/подписи/снимки помещаются и читаются; mobilestack не обрезает фото. Reload сохраняет сравнение, read-only fingerprint неизменён. Tab/ShiftTab/Enter открывает полный снимок/возвращается, фокус виден; действия review остаются доступны.
2. **Реальный author flow:** собственные owner и volunteer с правомерными объектами. Через UI загрузить main/cover и минимум2gallery images, дождаться ready, сохранить draft→reload→submit→review. Порядок и подписи кандидата совпадают с тем, что увидел проверяющий. У владельца не появляется reviewer access. Если найдётся отдельный дефект editor/upload, не чинить без нового согласования.
3. **Решения, минимум RU/AZ/EN ×390/1440:** на отдельных собственных заявках native approve/reject, reason и reload; при approve публичная карточка действительно показывает принятые main/gallery/order; при reject current live остаётся прежним. Не подменять это direct ORM или service call. No private data.
4. **Медиа edge states, минимум3языка ×390/1440:** удаление/empty gallery, missing file, corrupt existing raster. В corrupt case сервер возвращает bytes, но browser decode fails; виден fallback и нет активной broken thumbnail link. Expected induced404/decode failures отделить от unexplained errors. Длинная escaped caption без HTML execution, gallery с перестановкой порядка. Для специальных damaged legacy fixtures setup отдельно пометить; пользовательские переходы настоящие.
5. **Границы безопасности/общие consumers:** reviewer без document permission получает прежний отказ private document download; anonymous/bare/volunteer не видит reviewer detail/media links. Ошибочный/stale action не меняет live; обычные organization/program/affiliation текстовые comparison/branch links читаются. Source no new routes/ACL. Console/network без необъяснённых ошибок; внешние requests блокированы/SIMULATED.

## Риски и NOT RUN

Публичные фото Place уже обслуживаются public media storage. Этот fix не делает private documents публичными и не обещает нового приватного хранилища для candidate images. Не переносить legacy-superadmin-only review permissions. Remote storage не тестируется реальным внешним запросом: QA только собственные локальные файлы. Риск локального responsive CSS ограничен detail comparison всех hub entities, поэтому есть shared text checks. Глобальные sidebar/queue layout findings не входят.

На PLAN этапе нет postpatch GREEN, native author upload/решений/private document download/полного08; production/commit/push/deploy/module09 NOT RUN. Следующий необходимый шаг — одобрение именно этого семифайлового scope.
