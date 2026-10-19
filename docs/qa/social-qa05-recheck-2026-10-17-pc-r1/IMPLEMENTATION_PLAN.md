# SOCIAL-QA-05 Implementation Plan

> Выполнять checkbox tasks после одобрения конкретного однофайлового scope. Канонический lead frontend-reviewer, browser-qa и Django checks последовательно. Этот plan/diff не разрешает application patch.

**Goal:** убрать горизонтальное переполнение страницы отзывов о сайте у вошедшего автора, особенно768px, сохранив действия и остальные страницы.

**Architecture:** page-specific override для .site-reviews-page .review-form-grid в существующем site.css. Два поля получают две minmax(0,1fr) колонки; при≤760px остаётся одна. Generic grid/overflow/template/controller/JS не меняются.

**Tech Stack:** SSR Django6.0.2, Python3.12.15, PostgreSQL17.11, native Chromium155, CSS Grid; новых dependencies нет.

**Spec:** [guide PLAN05](../continuation-and-repair-prompts-2026-10-11.md#repair-SOCIAL-QA-05), [finding](../module09-2026-10-10-r1/findings/SOCIAL-QA-05.md), [repair prompt](../module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-05.txt), [свежий REPORT](REPORT.md).

## Global constraints

- Только SOCIAL-QA-05/P2, implementation approval PENDING. Сохранить approved dirty SOCIAL03–04, historical SOCIAL01–04 closures, чужие файлы/процессы и .cbmignore.
- C:\kidsmap, branch codex/module09-transfer-2026-10-16-r1, HEAD852938d96764ae315b92859e3651e5ea62054a36, index tree881e0c48c7d557c46221beb3b2410a157982f861; active_run:NONE автоматически не назначать.
- Без production/commit/push/deploy/reset/clean/stash/dirty checkout switch. Full ACCEPT09 один раз после всех SOCIAL tasks, global corpus отдельно; SOCIAL06–09 не начинать автоматически.
- Application scope ровно static/css/site.css. Templates/JS/controllers/services/models/routes/schema/PO/existing assertions и остальные findings вне scope.
- Только собственный DJANGO_TESTING=1 PostgreSQL/DB/cache/media/private-media/email, fictional fixtures, очищенный env, no .env/production credentials, external blocked/SIMULATED. Fresh RU/AZ/EN builder/verify и sole LOCALE_PATHS до django.setup; shared MO не менять.
- Body overflow-x:hidden — существующее AS-IS свойство; fix его не меняет и не добавляет clipping. Устраняется intrinsic grid minimum.
- Own runtime reuse только после ownership/isolation/source/MO proof. Старые prepare/PID/порты/сессии не считать автоматически действующими.
- До patch targeted RED; после patch meaningful native GREEN и небольшой affected subset. Успешные неизменившиеся full suites не повторять.

## Причина и точный файл

Site.css:6160 задаёт220/260/200px tracks +2gaps14px=708px. В site_reviews.html:158 grid содержит только2label. На768px min-content раздувает форму и внешнюю page: document822px, hero/toolbar right821.625, sort right804.625, grid right784.594. Guest без формы помещается. Generic collapse действует только≤760px.

В текущих active source templates literal search нашёл grid consumer в site_reviews.html. Graph coverage не полна; source search и actual DOM — основание scope. Generic rule сохраняется для потенциальных других consumers.

**Modify:** static/css/site.css, после .site-reviews-page-polished .review-form-wrap и перед комментарием Public reviews of catalog listings, около21964. Новых application файлов нет.

Полное добавление — [candidate-rules.css](candidate-rules.css), точный hunk — [proposed.diff](proposed.diff), [hashes/predicted after SHA](candidate-manifest.json). Приложение ещё не изменено:

~~~css
/* The site editor has two fields; zero track minimums prevent page expansion. */
.site-reviews-page .review-form-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (max-width: 760px) {
  .site-reviews-page .review-form-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
~~~

## Task1 — approval/source gate и RED

- [ ] Получить approval этого1file scope; сверить [source-entry.json](source-entry.json), HEAD/branch/index/dirty/active_run/sharedMO. Сохранить прежние изменения/evidence.
- [ ] Проверить own m09s05-plan-r1-app/pg, internal network, DB/cache/media/email, live template/static origins и свежие soleMO. При drift — новый уникальный profile и только affected fresh RED.
- [ ] При unchanged source использовать36cell native RED: author/guest×3langs×6widths,3source cells/24layoutFAIL на768;3backend baseline methods PASS. Они CSS defect не покрывают.
- [ ] SIMULATED client CSS probe7cells/49PASS — root-cause experiment, не post-patch GREEN. Удаление style возвращает исходную геометрию. Failed RU1024 animation-timing attempt сохранён, strict assertion не ослаблен.
- [ ] Выполнить apply-check без изменения исходников/index:

~~~powershell
git apply --check --ignore-space-change docs/qa/social-qa05-recheck-2026-10-17-pc-r1/proposed.diff
~~~

## Task2 — однофайловое исправление

- [ ] Применить только предложенный hunk:

~~~powershell
git apply --ignore-space-change docs/qa/social-qa05-recheck-2026-10-17-pc-r1/proposed.diff
~~~

- [ ] Только site.css отличается от entry1021; normalized after SHA соответствует candidate manifest. Generic grid и его media rule прежние. Page selector имеет более высокую specificity, поэтому получает собственный≤760 override.
- [ ] Не добавлять overflow-x:hidden/clip, fixed page width, уменьшение font-size, transform/zoom, JS-перенос полей. Не менять template; rating/name/text/submit/CSRF/handlers остаются прежними.

## Task3 — native GREEN/affected contracts

- [ ] Approved-source manifest/runtime parity. Новый browser context/session исключает cached CSS; не расширять scope на base template для cache-bust. Fresh soleMO до setup, actual static200/hash.
- [ ] Post-patch36cells author/guest×RU/AZ/EN×360/390/768/1024/1280/1440: documentWidth≤viewport+1, hero/toolbar/sort/reactions/form/grid/fields помещаются; прежние data/controls checks PASS. Outcome regression — [matrix-cell.js](matrix-cell.js). На768 все24прежних FAIL должны исчезнуть.
- [ ] Дополнительно RU/AZ/EN×760/761: две колонки выше760, одна ниже/на760; без ghost track/overlap. На390/768/1440 keyboard/focus/scroll,80символьное имя, длинный текст/переводы, rating picker и sorting. Снять viewport PNG после реального scroll к отзывам/форме и окончания finite entry animations; fullpage capture не доказывает видимость offscreen motion nodes.
- [ ] Actual native sorting GET → selected sort/readback; rating buttons меняют hidden value без перекрытия имени/textarea. На отдельном fresh fictional author native submit → pending review, reload и прежняя approved public projection. Valid/invalid CSRF/guest paths/response contracts сохранить.
- [ ] Native reaction на чужой fictional review → counter/DB readback; own/guest restrictions прежние. Loading/error/blocked transport только SIMULATED, без auto retry POST.
- [ ] Малый post-patch backend subset: те же3метода одним запуском через own runtime.py test/изолированную testDB, exact command pattern в [commands.md](commands.md):

~~~text
catalog.testcases.public.TestReviewEnhancements.test_site_reviews_page_can_sort_reviews_by_likes
catalog.testcases.public.TestReviewEnhancements.test_site_reviews_page_skips_blank_text_reviews
catalog.testcases.public.TestReviewEnhancements.test_site_review_reactions_update_counters
~~~

- [ ] Existing assertions не менять; они не заменяют native geometry. Small shared smoke Place review page и typed Activity/Specialist/Event pages390/768/1440 AZ/RU/EN, generic source unchanged/no unexpected new overflow. Новый style применяется только внутри site-reviews-page.
- [ ] Console/pageerrors/static404/icons/fonts/native PNG hashes/dimensions. Physical/other browsers/real screenreader/full WCAG/global UI отдельно NOT RUN без запуска. Новая причина вне scope — отдельный plan/approval; обычные итерации в этих site-specific CSS rules входят в согласованный scope.

## Task4 — evidence и остановка

- [ ] Новый уникальный fix-run REPORT/verification/source/commands-exits-counts/RED→GREEN/PNG, raw failed attempts/NOT RUN/SIMULATED. Проверить index/refs/active_run/MO/.cbmignore и foreign containers/artifacts.
- [ ] Закрыть только принятый SOCIAL05; добавить новую guide note, оставить историю/SOCIAL01–04 scoped closures. SOCIAL06–09/full ACCEPT09/global отдельно, без автоматического перехода.

## Self-review

Scope убирает третью жёсткую колонку двухпольного editor, сохраняет mobile collapse. Даны полный code/hunk/hashes, зависимости, action/state guards, long input/keyboard/scroll/shared consumers/CSS caching. Browser preview — SIMULATED hypothesis. Реализация05/post-patch GREEN NOT RUN, approval PENDING; production applicability UNKNOWN.
