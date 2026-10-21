# Specialist self onboarding implementation plan

**Goal:** обычный пользователь добавляет себя через «Я специалист», видит анкету и проверку в личном кабинете, получает управление только после подтверждения личности.
**Authorization:** пользователь согласовал этот сценарий и поручил «да исправь как ты видишь это». Реализация локальная, без публикации и production.
**Architecture:** сохранить SpecialistProposalDraft и существующий SpecialistClaim; выбор self/other хранить как намерение в payload, без предоставления прав. При отправке self создать pending claim в существующей транзакции; старые payload без выбора остаются other. Никаких миграций.
**Spec:** согласованные четыре шага в текущем чате.

## Confirmed findings
- SELF-SPEC-01: навигация предлагает пустой кабинет каждому пользователю.
- SELF-SPEC-02: добавление себя описано как предложение чужого профиля.
- SELF-SPEC-03: отправка анкеты не отличает себя от другого человека.

## Exact files
- `src/catalog/context_processors.py`: состояние навигации, только account routes.
- `src/catalog/controllers/specialist_workspace.py`: пустой вход, подписи и статусы заявок, сохранение выбранного сценария.
- `src/catalog/services/specialist_proposal_drafts.py`: self/other intent и pending claim при self-submit, idempotency.
- `src/catalog/templates/pages/includes/account_navigation.html`: кабинет только подтверждённому специалисту, заявки при наличии.
- `src/catalog/templates/pages/account_dashboard.html`: добавление своей анкеты и доступ к существующей заявке.
- `src/catalog/templates/pages/owner_listing_type_select.html`: «Я специалист — добавить свой профиль».
- `src/catalog/templates/pages/owner_specialist_create.html`: явный выбор себя/другого, понятные пояснения.
- `src/catalog/templates/pages/specialist_workspace.html`: до подтверждения показывать анкеты, убрать пустые технические блоки.
- `static/js/specialist_recovery.js`: сохранять и восстанавливать self/other вместе с несохранёнными полями; native radio semantics.
- `static/css/pages/specialists.css`: оформление выбора в существующем стиле.
- `locale/{ru,az,en}/LC_MESSAGES/django.po`: переводы новых строк.
- `src/catalog/testcases/test_specialist_self_onboarding.py`: сценарии пользователя, idempotency, запрет раннего управления, отказ/подтверждение.
- `docs/qa/specialist-self-2026-10-20/`: команды, результаты и browser evidence.

## Steps
- [x] Сохранить исходные версии dirty-файлов в ignored scratch; не менять чужие изменения.
- [x] RED: проверить отсутствие пустого кабинета, сохранение self intent и создание pending claim только при отправке.
- [x] Реализовать согласованный путь; existing/legacy proposals по умолчанию other; backend ACL оставить строгим.
- [x] GREEN: targeted и связанные specialist suites в disposable DB/cache/media/email, `DJANGO_TESTING=1`.
- [x] Проверить настоящий браузер, RU/AZ/EN, desktop/mobile, draft/resume/submit/status/confirmed profile, console/overflow.
- [x] Сохранить evidence, перечислить NOT RUN, без commit/push/deploy.

Snapshot: LOCAL HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`, upstream divergence 0/0; worktree dirty. Graph ready, templates partially parsed and inspected directly. Existing task33 stage state not modified.
