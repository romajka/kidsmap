# MOD-QA-01 — план навигации очереди модерации

**Статус: CONFIRMED OPEN, реализация ожидает отдельного одобрения.**

Путь: `/home/ramin/kidsmap/docs/qa/mod-qa01-recheck-2026-10-15-r1/IMPLEMENTATION_PLAN.md`.

Для исполнителя: выполнять последовательно в одобренном scope с применимыми TDD/verification/UI skills. Пользовательский запрет commit/push/deploy и правила canonical roles имеют приоритет над общим шаблоном skill.

**Цель:** дать доступ ко всем страницам очереди через клавиатуру и ссылки, сохранив фильтры, ACL, counts и порядок.

**Архитектура:** backend уже отдаёт Django Page. Добавить локальный nav в активный hub template; встроенный querystring меняет только page и сохраняет QueryDict. Использовать существующие классы и RU/AZ/EN переводы. Общий pagination.html не менять: он используется другой страницей и сейчас теряет фильтры.

**Стек:** Django6.0.2, server-rendered HTML, существующий admin CSS. Спецификация: guide PLAN MOD-QA-01 и historical module08 finding/repair prompt; свежие evidence в [REPORT](REPORT.md).

## Подтверждённая причина

Admin и staff reviewer с catalog.change_place: RU/AZ/EN ×360/390/768/1024/1280/1440,36cells.32pending предложения: первая страница25строк, ссылок page=2 нет; ручной URL page2 даёт другие7строк.72source FAIL observations — отсутствие pager/его клавиатурного пути, одна причина MOD-QA-01 P2. Реальный переход по отсутствующей ссылке NOT RUN. Candidate/live fingerprints не менялись.

View moderation_hub_index уже вызывает Paginator(rows,25).get_page(...). Активный `hub_index.html` заканчивает таблицу и не использует page.has_next/has_previous. [4regression methods](proposed_pagination_tests.py):6ожидаемых locale subtestFAIL,0ERROR;2остальных метода PASS. Existing assertions не менялись.

## Точные application-файлы

1. **Изменить** `/home/ramin/kidsmap/src/catalog/templates/admin/volunteer/hub_index.html`:7строк nav после таблицы перед endblock, только при page.has_other_pages. Предыдущая/следующая ссылка, видимый номер/число страниц, aria-label и aria-current; rel prev/next, стандартные клавиатурные ссылки. href через `{% querystring page=page.next_page_number %}` / previous_page_number. Существующий класс km-volunteer-actions уже умеет flex-wrap; новый CSS/JS не нужен по текущим данным.
2. **Создать** `/home/ramin/kidsmap/src/catalog/testcases/test_mod_qa01_hub_pagination.py`:4метода из [точного предложения](proposed-test_mod_qa01_hub_pagination.py). Проверяются page1→2 /page2→1 links,32=25+7 distinct rows, сохранение entity/status/new_or_edit/author/from/to и повторных author values без duplicate page, empty/invalid/out-of-range semantics, denied roles/GET-only/no candidate changes.

[Готовый diff](proposed-MOD-QA-01.diff), git apply --check exit0. [Source/diff SHA](plan-source.json). **Не применён**; новый app test-file отсутствует. Backend `volunteer.py`/moderation_hub.py, shared pagination partial, CSS/JS/PO/MO source, ACL/query/sort/counts, migrations/schema/CI и existing tests не входят в scope.

## Почему достаточно двух файлов

Native process подтвердил template origin и source hashes. Три используемых msgids уже корректны в свежих собственных MO: Страницы/Назад/Далее → Səhifələr/Əvvəlki/Növbəti → Pages/Previous/Next. Request context processor включён в current settings. Context7/official Django6.0 [querystring docs](https://docs.djangoproject.com/en/6.0/ref/templates/builtins/#querystring) подтверждают default request.GET, повторные значения и замену page. Новый helper/backend context не нужен.

## Реализация после одобрения

- [ ] Новый unique fix-run; свежий snapshot/проверка plan+diff SHA, принадлежности own profile и текущего source. Сохранить весь dirty WORKTREE/active_run/чужие processes/containers/artifacts.
- [ ] Новый собственный DJANGO_TESTING=1 PG/DB/cache/media/private-media/email, fictional queue32pending+single/empty controls. Clean env без .env/production credentials, external app requests disabled. Fresh current RU/AZ/EN builder/manifest/sole LOCALE_PATHS до django.setup; shared MO не трогать.
- [ ] Добавить только предложенный test-file и увидеть те же6RED subfailures; assertions не менять. Затем применить только nav diff; inverse7строк возвращает entry template. Не менять shared paginator partial или backend «заодно».
- [ ] Запустить те же4метода GREEN и существующий целевой `catalog.testcases.test_task33_volunteer_hub.VolunteerHubTests.test_hub_filters_and_counts_include_all_content_and_links`. Не повторять полный module07/все модули; full module08 один раз после завершения всех его задач.
- [ ] Реальный браузер: admin/reviewer, RU/AZ/EN ×360/390/768/1024/1280/1440; filter form→page1→Tab/Enter Next→page2→Shift+Tab/Enter Previous→page1. Видимые focus/номер страницы/ссылки, новые7строк, сохранение всех применимых фильтров и выбранных значений после reload. Отдельно single-page/empty/out-of-range/invalid filters; отсутствие лишних next/previous и unchanged query/count/order.
- [ ] Console/pageerror/network, PNG mobile/desktop и pager geometry. Сравнить candidate/live fingerprint до/после GET, убедиться в прежних403/redirect и405. Исторические generic admin sidebar/layout findings не исправлять в этом scope.
- [ ] Итоговый scoped REPORT/verification с exact commands/exits/counts, source/PNG/preservation proofs и NOT RUN. Закрыть только MOD-QA-01 после GREEN. Следующий ID — отдельный PLAN/approval.

## Риски и границы

Querystring по умолчанию сохраняет все GET values, включая повторные; page должен заменить прежнее значение, а не дублироваться. Проверить HTML escaping через фактические href/parse_qs. При пустой/одной странице nav не нужен; улучшение отдельного empty-state текста не входит в этот план. Не превращать span текущего номера в неработающую ссылку. Если новое nav не помещается/нужна другая причина или файл — показать расширение отдельно, не менять CSS автоматически.

Текущее «дальше» разрешило PLAN нового модуля. Одобрения module07 не распространяются на эти application-файлы. До отдельного одобрения нет реализации/закрытия01. Production/module08 full/прочие MOD IDs NOT RUN; без commit/push/deploy/reset/clean/stash/active_run assignment.
