# Security audit — 2026-09-08

Роль: `security-reviewer`; execution identity: `/root/audit_security`, самостоятельный runtime subagent orchestrator. Определение: `.agents/agents/security-reviewer/agent.md`. Режим AUDIT ONLY; изменён только этот отчёт. LOCAL HEAD: `d75b34f4db5d4ba484cf8392ff3ae0c9939031e2`. Проверенные application paths совпадают с HEAD; прежние agent-system изменения WORKTREE сохранены. PRODUCTION сегодня UNKNOWN, подключений не было. Исторические September 6 findings не считаются текущим runtime evidence.

Scope: OTP/Google/password reset, redirect/CSRF, volunteer/owner/admin ACL, изображения/private media, admin JSON import и JSON-LD. DB privileges, image history и внешний OAuth deployment передаются release/database review; здесь не проверялись.

## 1. Состояние области

Подтверждены две опасные ошибки в цепочках source: повторная проверка уже подтверждённого email выдаёт пользователя для входа без проверки challenge; сериализация JSON-LD не защищает границу HTML script. Ещё две ограниченные проблемы: private документы расположены в публичном media namespace; admin search suggestions не проверяет права модели.

Codebase Memory использован до структурного source discovery: `list_projects`, `index_status`, `get_architecture`, `search_graph(query="verify_email")`, `trace_path(function_name="account_verify_email", direction="outbound")`. Корень совпадает; full index, generations `2026-09-08T05:40:34Z` и `2026-09-08T05:54:13Z`. Coverage `metadata_match` для auth/views/seo/access/volunteer/photo/admin/import JS; `place_detail.html` partial, `deploy/` excluded. Все критические выводы проверены чтением source. Graph trace также связал несколько одноимённых чужих symbols: такие edges не использованы как доказательства.

## 2. Сильные стороны

- Google bridge фиксирует login process и callback, требует подтверждённый email, отклоняет неоднозначные/inactive identity, использует транзакцию и блокировки, не сохраняет provider tokens: `src/catalog/google_auth.py:89–190`, `src/config/settings.py:69–83`. Это оценка приложения; реальный provider/state/config не проверены.
- Redirect helper ограничивает host/scheme и исключает auth loops на AZ/RU/EN: `src/catalog/services/auth_redirects.py:26–56`. Google дополнительно перепроверяет redirect из state.
- Volunteer gate не сводится к скрытым кнопкам: `volunteer_middleware.py:13`, `services/staff_roles.py:6`, `services/volunteer_places.py:55`. Scope требует active staff volunteer, свой `created_by`, отсутствие owner/deletion/temporary. Save/review повторно проверяют объект; signed base snapshot и revision version предотвращают очевидные stale writes. Review требует active staff superuser (`:153`); PostgreSQL concurrency отдельно NOT RUN.
- Owner handover убирает standing grant creator: `services/place_access.py:75`, `repositories/django_repositories.py:276`. Volunteer явно исключён из owner permission helpers. Фото thumbnail выбирает Place из managed queryset и gallery из этого Place (`photo_views.py:24`).
- Image normalization проверяет декодируемый формат, MIME mismatch, байты/пиксели/размеры, повторно кодирует WebP и очищает metadata: `services/image_uploads.py:105`. Batch limit есть в `photo_views.py:95`.
- Import validation обёрнут в admin view, использует POST и серверную нормализацию; JS отправляет CSRF token (`domain_admin/place.py:3812,3935`; `static/admin/js/kidsmap_place_json_import.js:388`). Export проверяет view/change permission (`place.py:3967`). В этих двух файлах серверный fetch импортируемого URL не найден. Geocoding repository использует фиксированный Google endpoint и query encoding (`repositories/geocoding_repositories.py:13–37`); доказанного SSRF на этом пути нет.
- CSRF-exempt tracking имеет origin и rate safeguards (`views.py:210–262,616`), поэтому само исключение не оформлено как CSRF finding. Password reset сохраняет общую форму ответа; Google-only eligibility проверяет соответствие текущего и подтверждённого email (`forms.py:807–827`).

## 3. Реальные проблемы

### SEC-01 — P1: подтверждённый email ошибочно считается доказательством нового входа

Environment: LOCAL HEAD/source. Confidence: HIGH в цепочке кода; runtime и production UNKNOWN.

Источник: `src/catalog/services/email_verification.py:143–149` выбирает verification по email и при `record.is_verified && user.is_active` возвращает `ok=True, user=user` **до** hash/expiry/attempts checks. `src/catalog/views.py:1550–1556` передаёт этот результат в `auth_login`; анонимный route зарегистрирован в `src/catalog/urls.py:101`. `EmailVerificationForm.clean_code` проверяет формат, не владение challenge (`forms.py:698–724`). Repository выбирает email без привязки к заявителю (`django_repositories.py:164`).

Конкретное условие: существует active User с verified UserEmailVerification, а новый анонимный запрос предъявляет email записи и код допустимого формата. Состояние «email когда-то подтверждён» открывает ветку успешной аутентификации независимо от правильности текущего кода. Это позволяет получить права затронутого аккаунта; наличие привилегированных затронутых аккаунтов не проверялось. Обычное завершение OTP оставляет такую запись (`django_repositories.py:205`); Google flow тоже создаёт verified запись с пустым hash и без challenge (`google_auth.py:186–189`). Поэтому Google-only пароль не устраняет проблему.

Verification: source input → repository → early success → login проверен; свежий full-request reproduction NOT RUN. Никаких production попыток, private-record подсчётов или доказательств инцидента. P1 передан orchestrator сразу после source verification.

Owner: django-reviewer + security-reviewer; integration-reviewer — negative regression. Следующий шаг после одобрения scope: отделить idempotent «уже подтверждено» от разрешения создавать session; проверить used/expired/exhausted challenges, обычные и Google-created records, сохранение корректного первого подтверждения.

### SEC-02 — P1: raw JSON-LD допускает выход из HTML script

Environment: LOCAL HEAD/source. Confidence: HIGH в serializer/template boundary; доступность конкретного stored input в production UNKNOWN.

Источник: `Place.name_az/name_ru/name_en` — обычные CharField (`src/catalog/models/place.py:69–74`). Owner form переносит название в модель (`forms.py:1430,1599`); volunteer form — в candidate (`volunteer_forms.py:88`). Название попадает в schema (`services/seo.py:397`), breadcrumb (`:527`) и catalog item list (`:317`). `_build_breadcrumb_schema`, `_build_item_list_schema` и detail payload используют `json.dumps(..., ensure_ascii=False)` (`:75,110,537`); controller передаёт строку шаблону (`controllers/place_controller.py:848–865`). `templates/catalog/place_detail.html:12–13` и `place_list.html:9–10` вставляют её через `safe` внутри script.

Конкретное условие: сохранённое название содержит HTML script terminator и попадает на rendered detail/list. JSON encoding не экранирует HTML delimiters; HTML parser завершает data script до конца JSON. Следующая разметка интерпретируется браузером как HTML, создавая stored XSS surface на origin сайта. Owner/volunteer публикация проходит отдельную модерацию: не утверждается, что анонимный draft автоматически публичен. В проверенных settings/nginx source CSP не найден; effective production headers UNKNOWN.

Verification: source chain и serializer behavior проверены; полноценный HTTP/browser reproduction NOT RUN, выполнение JS не проверялось. Не следует считать валидность JSON доказательством безопасности HTML. P1 передан orchestrator.

Owner: django-reviewer + seo-reviewer + integration-reviewer. Следующий шаг после одобрения: единый HTML-safe JSON serializer для всех JSON-LD consumers и regression на сохранение JSON semantics и невозможность выхода из script; не полагаться только на модерацию или field stripping.

### SEC-03 — P2: private document ACL обходится на уровне namespace media

Environment: LOCAL HEAD/source; deployed storage/nginx и наличие файлов UNKNOWN. Confidence: HIGH для source mismatch, текущая утечка не доказана.

Источник: `src/catalog/models/specialist.py:388` сохраняет FileField в `protected_docs/specialists/` через обычное storage. `src/catalog/views.py:1886–1910` проверяет staff/owner либо verified-public diploma/certificate перед FileResponse. Но `deploy/nginx/kidsmap.az.conf:108–114` раздаёт общий `/media/` без исключения protected_docs. Аналогичный общий Django путь: `src/config/urls.py:62–71`, `src/config/views.py:136–145`; ответ дополнительно public-cacheable.

Конкретное условие: документ существует в MEDIA_ROOT, путь известен, включён generic nginx/Django media serving. Прямой media URL обходит object ACL и specialist feature gate; конфиденциальный файл может быть доступен без document view. Непредсказуемое имя не заменяет проверку доступа.

Verification: storage → namespace → serving wiring прочитан. Private download, file inventory, live nginx и runtime fixture NOT RUN. September 6 counts не используются как текущие. Owner: release-reviewer + django-reviewer. Следующий шаг: согласовать private storage вне public namespace, защищённую выдачу и negative checks обеих serving layers.

### SEC-04 — P2: admin suggestions раскрывают данные без Place permission

Environment: LOCAL HEAD/source. Confidence: HIGH в отсутствующем model gate; наличие restricted staff в production UNKNOWN.

Источник: `src/catalog/domain_admin/place.py:3839–3842` оборачивает `search_suggestions_view` только в `admin_site.admin_view`. Метод `:4307–4358` не вызывает `has_view_permission`/`has_change_permission`; ищет среди всех non-deleted Place, включая непубличные, по названию, адресу, телефону и owner email/username. В ответ включаются address, phone1 и owner username (`:4336–4354`). Прочитан installed Django `contrib/admin/sites.py:202,233`: стандартный admin wrapper проверяет active staff, а не конкретную модель. Custom override этой границы в проверенном src не найден.

Конкретное условие: active staff, не volunteer, не имеет view/change Place, но запрашивает suggestions с поисковой строкой длиной от двух символов. Scope недостаточен, чтобы скрыть matching draft metadata. Volunteer middleware блокирует этот route: это **не** подтверждённый volunteer A/B bypass. Штатные moderator/content-manager presets содержат view_place; finding касается custom/restricted staff или отозванных разрешений.

Verification: route/wrapper/query/output source проверены, runtime negative request NOT RUN. Owner: django-reviewer + security-reviewer. Следующий шаг: одинаковый model permission guard у changelist и AJAX suggestions; добавить отрицательную проверку restricted staff и сохранить volunteer denial.

## 4. Tech debt

Auth объединяет факт подтверждения адреса и разрешение войти в один `EmailVerificationResult.ok/user`: SEC-01 показывает цену неоднозначного контракта. JSON serializers распределены по SEO helpers и безопасны для JSON transport, но используются в другом output context (SEC-02). Custom admin endpoints проверяют permissions вручную и неравномерно (SEC-04).

## 5. Risks

- Password login/reset в проверенных `views.py`, `forms.py` и repository nginx не имеют отдельного application rate-limit. Возможны credential guessing и email abuse; upstream/WAF controls и реальная интенсивность UNKNOWN. Это hardening risk, не новый доказанный auth bypass.
- OTP attempts decrement — read-modify-save (`django_repositories.py:223`); send/check lifecycle не использует явный общий row lock. Потерянные decrement/повторное consumption при конкуренции — риск, без fresh concurrency proof не объявляется exploit.
- Profile email можно менять отдельно от verification identity (`controllers/auth_controller.py:106`). Google-only reset уже проверяет соответствие адреса; broader identity lifecycle и ambiguity требуют отдельной acceptance matrix.
- Приватная выдача volunteer photo имеет ACL/no-store, но сам файл хранится в общем Place storage. Требование конфиденциальности draft images на уровне storage нужно явно определить; source ACL не означает private storage.

## 6. Dead/legacy candidates

Удаление не предлагается. Обычная OTP регистрация, Google bridge, owner creator fallback, private document view и generic media serving имеют реальную wiring. Historical security/deployment knowledge — DATED, а не текущие production facts. Old `.dockerignore`/active-image claims не переиспользованы: это самостоятельный release review.

## 7. Tests gaps

Executed personally:

- `git rev-parse HEAD` → указанный HEAD; `git diff --quiet HEAD -- src static templates deploy requirements.txt Dockerfile .dockerignore` → без application diff, exit 0.
- MCP discovery/coverage и bounded `rg`, `sed`, `nl` source reads перечисленных файлов. Первый `trace_path` запрос с неверным parameter вернул error; повтор с `function_name` прошёл. Нет выводов из отсутствующих graph edges.
- `python3 -` с stdlib AST/JSON/HTMLParser проверил только actual breadcrumb serializer и HTML boundary; настройки Django/БД не загружались, файлов/data не создавалось, сеть не использовалась. Результат: JSON валиден, delimiters сохранены, parser видит дополнительный script element. Это не browser execution и не full-request reproduction. Attack input в отчёт не включён.

NOT RUN personally: Django suites, full-request auth/injection reproductions, browser tests, PostgreSQL concurrency, production endpoints/SQL/files/config, реальный Google OAuth, dependency vulnerability scan. После сообщения orchestrator о platform cyber filter дальнейшие auth/injection runtime reproductions прекращены; findings остаются source-based. Подробный test command/snapshot/count у QA берётся только из её итогового отчёта, не заявляется личным выполнением здесь.

Existing tests inspected, not executed here: `auth_flow.py` first verification/expiry, `test_google_auth.py` CSRF/state/replay/inactive/conflict/reset, `test_volunteer_admin.py` ownership/CSRF/handover/stale revision, `test_volunteer_dashboard.py` foreign IDs/count scope, `image_uploads.py`, `photo_workflow.py`. `testcases/admin.py:797` проверяет положительный suggestions response, не denial restricted staff. Наличие тестов не означает PASS; isolated SQLite не доказывает PostgreSQL race safety.

Нужные gaps: used OTP cannot authorize new session; Google-created verification must not authorize OTP login; HTML output context для всех schema strings; protected documents недоступны по generic media; restricted staff suggestions denied; race-sensitive OTP/volunteer checks на disposable PostgreSQL.

## 8. Recommendations

Orchestrator: включить SEC-01 и SEC-02 как P1 с source evidence и текущей runtime границей. До следующего auth/publication release согласовать узкий implementation plan и acceptance. SEC-03 передать совместно Django/release, SEC-04 — Django/admin. Не продолжать production проверки, исправления, миграции или deploy по одному этому отчёту. Решение о сроках — после review конкретного scope пользователем.

## 9. P0/P1/P2/P3

| Приоритет | ID | Решение |
|---|---|---|
| P0 | Нет | Свежая компрометация/авария не установлена |
| P1 | SEC-01 | Verified email branch разрешает новую session без проверки challenge |
| P1 | SEC-02 | Stored name → raw JSON-LD → HTML script boundary |
| P2 | SEC-03 | Private documents в public media namespace; live exposure UNKNOWN |
| P2 | SEC-04 | Restricted non-volunteer staff suggestions обходят model permission |
| P3 | Без отдельного finding | Консолидация auth result/output serializer/admin permission contracts |

Никаких application fixes, deletions, commits, pushes или production действий выполнено не было.
