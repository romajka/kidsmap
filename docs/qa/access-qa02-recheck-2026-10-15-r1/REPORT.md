# ACCESS-QA-02 — свежий PLAN, finding OPEN

2026-10-15, Asia/Baku. **Отказ от приглашения отсутствует в UI.** Два новых приглашения созданы владельцем через настоящие формы места/организации. Получатель видит только Accept и Mark read. RU/AZ/EN×360/390/768/1024/1280/1440:36FAIL отсутствия отказа,72PASS существующего accept/keyboard/геометрии. [Concrete implementation plan](IMPLEMENTATION_PLAN.md) ожидает отдельного scope approval; приложение, существующие assertions/CI/schema не изменены.

Один `/root`, канонические kidsmap-orchestrator/django-reviewer/security-reviewer/browser-qa последовательно, не независимые subagents. Skills systematic-debugging/writing-plans, для native UI playwright и применимые KidsMap design rules. Режим PLAN из guide; «дальше» не расширяет ранее approved01/CSS scope.

## Snapshot / source

Фактический root `/home/ramin/kidsmap`; branch `task33-progress`; HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51` + существующий dirty WORKTREE; `active_run: NONE`. [Entry](entry.json):27835baseline file hashes, включая3shared MO;5предыдущих process identities;56container identities. [Verification](verification.json) сравнивает snapshot/чужие files/контейнеры/актуальный own process. Production не исследовался; это не production evidence.

Codebase Memory callable: исторический alias C-kidsmap отсутствует, реальный project `home-ramin-kidsmap`, root совпал. Graph ready; generation2026-10-14T14:14:39Z;6critical paths metadata_match/no_recorded_issue, best effort, ignored metadata inventory truncated. Inbound decide_invitation: JSON API и repository reject/cancel. Отрицательные выводы подтверждены чтением controller/template/routes. [Provenance](graph-provenance.json), без graph cache.

## Причина / планируемые файлы

`src/catalog/templates/pages/account_notifications.html` выводит accept/read, `src/catalog/controllers/workflow_notifications.py` не содержит reject, в `src/catalog/urls.py` нет notification reject route. Canonical `business_team.decide_invitation` уже выполняет отказ, оба типа проверены current HTTP transition.

План: native локализованный отказ и CSRF POST adapter только через notification_id. Свежий recipient scope, строгий kind/type/version, expiry/email/owner/ownership_version под canonical parent/invitation locks; вызов существующего service. Без произвольного target из body и новых прав. Existing service reject проверяет actor/email/PENDING, но не expiry/ownership; новый adapter не может полагаться лишь на status или GET eligibility. Это source-design requirement, не заявленный exploit старого API.

Ровно4application/test files: controller, account_notifications template, urls и новый `src/catalog/testcases/test_access_qa02_invitation_decline.py`. Без нового CSS/JS/PO/schema и редизайна общего аккаунта. Точные paths, алгоритм, минимальный test code, stale/concurrency/security/locale/native acceptance и stop conditions — в [плане](IMPLEMENTATION_PLAN.md). Пока ни один из этих файлов не изменён.

## Свежие проверки

Всего **122observations:86PASS/36FAIL**, не122независимых end-to-end теста. Native owner3PASS сохранены через interruption с неизменным source и сохранившейся fixture DB;108matrix/11API выполнены в новой resumed browser session. [Observation rows](observations.json).

- [Owner UI3](owner-invites.js.result.json): native login→place form POST302; organization form AJAX POST200/PENDING; recipient login/inbox с2current accept forms. ORM только для3fictional users и1Place/1Organization, invitation transition не seeded.
- [Inbox108](inbox-matrix.js.result.json):18cells,36FAIL decline (2types×18),72PASS current accept/keyboard/fitting controls. Native focus на accept имеет outline auto1px, focus-visible=true. Скриншоты показывают отсутствие control; native decline по этой причине **NOT RUN**, его не подменяли программным click/ORM.
- [Existing API11](existing-reject-api.js.result.json): оба типа GET405, CSRF403, wrong nested target403, current JSON POST200/REJECTED, replay409; actual inbox reload убрал обе consumed accept forms. Это реальный session/CSRF HTTP из browser request context, **не** native decline через отсутствующую кнопку. Snapshot/API IDs только вымышленные. Existing API не исправлялся.
- [Targeted existing tests](targeted-existing-tests.txt):2unchanged methods PASS, exit0,4.718s: WorkflowIntegrationTests.test_invitation_inbox_post_only_recipient_scoped_and_revocation_suppresses_mail и test_changed_email_cannot_read_old_address_notification. Другие backend suites не запускались.
- [Local delivery](local-delivery-r2.txt):2реальных own filebased письма приглашений; explicit own delivery tick. [Before API READ ONLY](readonly-readback.txt):2PENDING,0grants,2notifications,2sent/2files. [After rejection delivery](local-delivery-after-reject.txt) и [final READ ONLY](readback-final.txt): terminal statuses, grants/event/mail aggregates. Ссылки/пароли/письма не копируются в Git.
- Backend socket connect/connect_ex разрешён только к своему PostgreSQL; actual external-connect probe denied. Browser external requests abort. Matrix pageerrors0/localBadResponses0,1external-blocked console/request diagnostic; это не локальный asset failure. API403/405/409 — ожидаемые negative cases, не green network counters.

Финальный `.venv/bin/python docs/qa/access-qa02-recheck-2026-10-15-r1/verify.py`: native exit0,27834/27835baseline files unchanged, одно ожидаемое изменение — добавленная guide note; missing/unexpected/new-other paths0;56старых container identities/ports/state совпали;3shared MO сохранены; own runtime source match;22PNG,4JS syntax,28local artifact links и git diff --check PASS. Этот gate подтверждает готовность плана/evidence, не исправление36FAIL и не сохранность потерянных процессов. Точные argv/exits/seconds в [commands.jsonl](commands.jsonl). CLI exit0 при36semantic FAIL не означает acceptance. Meaningful new decline regression RED→GREEN и native decline acceptance запланированы после approval; full module corpus не повторялся.

## Изоляция и running source

Новый own container/volume `access-qa02-recheck-2026-10-15-r1-pg`, image postgres17-alpine, bind127.0.0.1:37267, DB/user `access_qa02_recheck_r1`, test DB `test_access_qa02_recheck_r1`. HTTP127.0.0.1:57239, актуальный PID/argv — [server.json](server.json). Секреты вновь сгенерированы в ignored `.tmp/access-qa02-recheck-2026-10-15-r1` с0700/0600; собственные cookies/LocMem/cache/media/private-media/filebased email. Никакой checkout .env/production credentials не читались и не подключались.

Inherited env очищается; DJANGO_TESTING=1 до settings/django.setup. Current RU/AZ/EN PO собраны helper scripts/build_isolated_locales.py в fresh own directory, sole LOCALE_PATHS проверен до setup. [Manifest](locale-manifest.json), [compiler](locales-build.txt), [verify](locales-verify.txt); shared MO не переписаны. Own runtime source:14startup file hashes, actual imported controller/service module paths, cached notifications template origin и source SHA, /proc argv/cwd + final disk/served template match. [Resumed source](runtime-source-resumed.json), [final source](runtime-source-final.json).

Actual native browser149.0.7827.55 по browser.version(); session после прерывания `accessqa02recheckr1b`. Native browser behavior, source inspection и readback перечислены отдельно.

## Прерывание / environment и сохранность

[Interruption record](interruption.json): после explicit turn interruption старый own HTTP PID2032510 и session accessqa02recheckr1 оказались недоступны. Все5captured previous process identities тоже оказались недоступны; причина **UNKNOWN**, их preservation **NOT VERIFIED**. Их не убивал/не перезапускал/не восстанавливал. Docker own PG identity и данные сохранились; migrate/reseed/reinvite не повторялись. Поднят только own HTTP после проверки свободного port/source и новая own browser session.

Own resume readiness проверял только10s и завершился exit1 до готовности процесса. Позже **тот же** процесс ответил source-match; второй restart не делался. Первый own delivery launcher ошибочно resolve() разыменовал venv/python в системный Python и получил ModuleNotFoundError(django) до DB work, exit1. Исправлен только own launcher path; [raw](local-delivery.txt) и receipts сохранены. Зависимости/application/assertions не менялись. Повторные own delivery/readback и2targeted methods exit0.

Это environment/QA-harness failures, не application regression и не повод ослаблять проверки. File/shared-MO/container preservation проверены отдельно в final gate; исчезнувшие processes не объявляются PASS. Baseline current reports/принятый ACCESS01/historical module02–07 не переписаны. Guide получает одну новую текущую PLAN note, предыдущая01 note сохранена.

## PNG / пределы

[PNG manifest](png-manifest.json):3native owner/recipient captures до interruption +18current inbox captures после него +1post-API inbox=22PNG, SHA/dimensions. Просмотрены originals RU360/AZ390/EN1440. Footers/contact strings сайта видимы как existing source content; внешние связи не открывались. Уведомления имеют текущую простую native стилизацию; общий редизайн аккаунта не включён в02.

ACCESS-QA-02 **OPEN**. Native decline, новые adapter negative/concurrency tests, stale/expiry/owner/email race, long-data new-control acceptance, explicit network abort нового POST — NOT RUN до implementation. Existing current HTTP reject proof не заменяет их. Native accept terminal transition в этом recheck не повторён: UI action availability +2existing targeted guards, полный accept path послеpatch обязателен.

ACCESS01 LOCAL PASS retained; ACCESS03=ORG02 имеет prior module02-r2 acceptance и не исправляется по старому FAIL. ACCESS04/05, ACCEPT-07/full07, global corpus, external SMTP/CDN/OAuth, physical devices/Firefox/Safari/screen reader и production — **NOT RUN**. Ни commit/push/deploy/reset/clean/stash/active_run assignment, ни module08 не выполнялись.

[Next prompt](next-prompt.txt): одобрение конкретного плана02, затем только его реализация/целевые проверки. До отдельного approval приложение не менять.
