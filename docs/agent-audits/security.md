# Security audit — 2026-09-06

Роль: `security-reviewer`. Независимое выполнение runtime subagent `/root/audit_security`, определение [agent.md](../../.agents/agents/security-reviewer/agent.md). Прочитаны AGENTS.md, shared architecture/source-of-truth/security/database/deployment/testing, audit contract; применены systematic-debugging и verification-before-completion. Scope: auth/OTP/OAuth, permissions, uploads/private media, JSON-LD/imports, redirects, runtime privileges/secrets. Записан только этот отчёт; application fixes, production requests, deployment и изменение данных не выполнялись.

## 1. Состояние области

- **LOCAL HEAD:** `df6fef3784a6bae6b7ddce90cd41a392d9f9e6bf`; **WORKTREE:** pre-existing dirty forms/views/settings/SEO/photo/phone changes и untracked Google bridge. Google и новый photo/phone flow нельзя считать активными на сервере.
- **PRODUCTION:** clean `86a0b8cf64a8835f310a608a3428c60f1fc5341a`, catalog migration0100, allauth отсутствует. Источник live evidence — root/orchestrator, [PRODUCTION_READ_ONLY](PRODUCTION_READ_ONLY.md) E1–E7; этот специалист самостоятельно по SSH не подключался.
- Source review независимо подтвердил границы. Свежие локальные проверки: реальный Django Client на одноразовой SQLite `:memory:` с CSRF; отдельный noDB JSON-LD serializer/template proof на WORKTREE, HEAD и production commit. Это не пентест production и не полная security certification.
- **Главный результат:** подтверждён локальный обход входа через повторное подтверждение уже verified email; live code/data prerequisites подтверждены root. Текущая эксплуатация третьими лицами не установлена. P0 не назначен.

## 2. Сильные стороны

- E1: DEBUG/TESTING выключены, HTTPS redirect, secure session/CSRF cookies, HttpOnly session, HSTS; PostgreSQL и Redis реально используются. Это полезные барьеры, но они не исправляют ошибку решения об аутентификации SEC-01.
- Local Google: `google_auth.py:88` POST start, middleware CSRF; fixed callback; server-approved process/scopes; settings PKCE и online tokens; проверка boolean verified email, conflict/inactive rejection, atomic linking и запрет переключения аккаунта уже вошедшим пользователем (`_resolve_google_user:130`). Нет сохранения OAuth tokens. `forms.py:807` допускает Google-only password reset только для текущего verified local email. Реальный Google login не проверялся и не активен.
- `services/auth_redirects.py:39` использует Django host/scheme validation, HTTPS requirement и исключает auth-loop routes; Google повторно валидирует state.next. `views.py:1747` logout требует POST; password change сохраняет корректную сессию через `update_session_auth_hash`. Reset использует Django token flow и generic success, а не выдаёт токен клиенту.
- `services/place_access.py:is_direct_place_manager` выдаёт доступ текущему owner; created_by остаётся fallback только при отсутствии owner. Direct manager permissions не включают publication. `repositories/django_repositories.py:276` ограничивает managed queryset; photo thumbnail берёт файл через scoped place/gallery. Не найден подтверждённый IDOR на этих просмотренных путях; исчерпывающий permission matrix не запускался.
- `services/image_uploads.py:21/:92`: byte/pixel/dimension limits, actual image decode/verify, format allowlist, WebP re-encode и удаление metadata; `photo_views.py:51/:74` требует authenticated POST, batch limit и user-bound retry key. Это LOCAL source protections, не доказательство обновления production image.
- Tracking CSRF-exempt endpoint `views.py:543` имеет origin/referrer/fetch-site проверки, rate guard и controller validation. Поэтому один `csrf_exempt` не классифицирован как CSRF bypass. Local phone POST явно CSRF-protected, no-store и использует proxy allowlist при чтении IP.
- Admin pricing JSON validation (`domain_admin/place.py:3935`) выполняет JSON/type/normalization checks и не пишет данные; маршрут обёрнут admin_view. Export проверяет object view/change permission. Проверенный CSV command `management/commands/import_places.py` читает операторский local path, не fetch URL; запускать его для аудита нельзя — он пишет. SSRF на этих просмотренных import paths не доказан.

## 3. Реальные проблемы

### SEC-01 — P1: anonymous login через already-verified email

**Environment:** WORKTREE и LOCAL HEAD; PRODUCTION source/data prerequisites подтверждены E7. **Confidence:** высокий; полный локальный HTTP/session proof, а не только service mock.

Полная цепочка: `views.py:1450 account_verify_email` доступен anonymous request; `forms.py:686 EmailVerificationForm` принимает переданный POST email и любые шесть цифр. Signed pending-registration/session ownership check отсутствует. Controller `verify_registration_email_code` передаёт этот email в service; `DjangoEmailVerificationRepository.get_by_email:164` выбирает `email__iexact` record. `services/email_verification.py:148` при `record.is_verified and user.is_active` возвращает `ok=True, user` **до** проверки hash/expiry/attempts. `views.py:1484–1485` интерпретирует это как доказанный вход и вызывает `auth_login`.

**Reproduction:** свежий synthetic active verified user, пустой code_hash, expiry=None, attempts_left=0; новый anonymous Django Client с `enforce_csrf_checks=True`, собственный CSRF с login GET, произвольный шестизначный код. POST302, `_auth_user_id == target.pk` true. Ни пароль, ни pending signup session не передавались. SQLite полностью в памяти; transport blocked; LocMem cache/email; отдельный temp media. Никаких существующих user records не читалось.

**Live scope:** root E7 подтвердил10 active verified records и matching production hashes service/views; service/controller/repository неизменны между production commit и HEAD. Это доказывает наличие code/data prerequisites, но не факт злоупотребления и не проверку конкретной личности/роли через атаку.

**Impact:** знание email подходящей записи может дать сессию её пользователя и все его разрешения. CSRF не помогает против злоумышленника, который получает собственный анонимный CSRF token. Новый Google bridge также создаёт verified records; поэтому его защита не закрывает этот общий local auth путь.

**Owner/handoff:** django-reviewer + security-reviewer + integration-reviewer; orchestrator немедленно уведомлён. Следующий шаг после утверждения scope: отделить idempotent “already verified” от разрешения создать сессию, определить single-use/pending registration proof и покрыть negative regression. Решения по invalidation/exposure assessment требуют отдельного конкретного плана; аудит ничего не изменяет.

### SEC-02 — P1: JSON-LD допускает выход из script context

**Environment:** WORKTREE, HEAD и production commit; E1 подтверждает sampled production SEO source hash. **Confidence:** высокий для output boundary, не установлен факт размещения вредоносной карточки.

`models/place.py:71` хранит name_ru как text; owner form принимает имена (`forms.py:943`, `:1430`), SEO использует `place.name_i18n` (`services/seo.py:397/:527`). `_build_breadcrumb_schema:74` и LocalBusiness `:537` сериализуют `json.dumps(..., ensure_ascii=False)` без HTML raw-text escaping. `templates/catalog/place_detail.html:12–13` вставляет JSON через `|safe` внутрь `<script type="application/ld+json">`; аналогичные sinks есть base:89/92, place_list:9/10, home:10, seo_landing:145/146.

**Reproduction:** AST-loaded реальная `_build_breadcrumb_schema` + реальная строка template через Django Engine, no DB. Inert closing-script marker даёт два HTML script elements вместо одного; `json.loads` при этом успешен. Повторено на всех трёх snapshots. JavaScript в браузере не выполнялся; marker содержит только комментарий. Первый вариант quoted marker ID экранировался JSON и не прошёл ID assertion, хотя уже создавал2script nodes; исправлен только test marker на unquoted ID, application source не менялся.

**Trigger/impact:** управляемая строка должна достичь публично отрисованного SEO payload (например, имя опубликованной карточки). Publication/moderation gate — реальный prerequisite; это не доказательство, что anonymous может немедленно опубликовать payload. Если строка попала в output, HTML parser завершает JSON-LD script, и следующий script может выполняться в origin сайта. Ни наличие malicious stored rows, ни live execution не проверялись.

**Owner/handoff:** SEO + Django + security + integration. После approval: единый HTML-safe JSON serializer для всех sinks, сохраняя корректный application/ld+json, плюс regression на closing tag/HTML metacharacters и rendered local browser proof. Простая проверка JSON validity недостаточна.

### SEC-03 — P1: секреты упакованы в активный image

**Environment:** production E4; source `Dockerfile:18 COPY . /app`, `.dockerignore:1–12` не исключает `.env*`. **Confidence:** высокий, boolean-only root probe подтвердил `/app/.env` и populated Django secret/DB URL-password/SMTP password settings; значения не выводились.

**Trigger/impact:** доступ к image/layers, registry или build artifacts раскрывает секреты вместе с приложением; Git ignore не защищает Docker context. Внешний доступ к image/registry и фактическая утечка не установлены. Наличие `.env` в image само по себе не доказывает HTTP download.

**Owner/handoff:** release-reviewer + security. Планировать исключение секретов из контекста, новую сборку, inventory прежних images/distribution и обоснованную rotation по exposure assessment. Не удалять images и не менять ключи в этом аудите. Root `.env#` — не подтверждённый credential leak; не путать с `.env`.

### SEC-04 — P1: приложение подключается к PostgreSQL как superuser

**Environment/evidence:** production E2; root получил привилегии через actual application DB connection, не через факт root SSH. Superuser/createdb/createrole включены. **Confidence:** высокий.

**Impact/trigger:** компрометация приложения или небезопасный DB path получает существенно больше прав, чем нужны обычным queries; может затронуть целостность/доступность всего PostgreSQL instance. Это privilege exposure, не воспроизведённая SQL injection или remote code execution. PostgreSQL port не опубликован на host (E4).

**Owner/handoff:** database-reviewer + release-reviewer + security. Согласовать разделение runtime/migration roles и grants с проверкой всех service paths на disposable PG; не отзывать права на работающем приложении без плана.

### SEC-05 — P2: private documents хранятся в публичном media subtree

**Environment:** source + production E4; **Confidence:** высокий для архитектурной границы, live exposure отсутствует в доказательствах.

`models/specialist.py:388` использует обычный FileField `protected_docs/specialists/`. `views.py:1814` проверяет staff/owner или public+verified diploma/certificate перед FileResponse. Однако `src/config/views.py:136 serve_media_file` и generic media URL, а также `deploy/nginx/kidsmap.az.conf /media/` alias отдают весь MEDIA_ROOT без исключения protected_docs. E4 подтверждает такой effective nginx config. При известном пути существующего файла Django authorization view обходится прямым URL.

**Live limit:** E3/E4: SpecialistDocument rows=0. Это latent defect перед активацией, не доказанная утечка существующих документов, не причина объявить SpecialistDocument dead. Private URL не запрашивался; файловые содержимые не читались.

**Owner/handoff:** release + Django + security, product owner для public/private contract. До будущего использования документов согласовать storage вне public root либо deny/internal serving на обоих слоях; regression direct path404 и authorized route в local environment.

## 4. Tech debt

- **SEC-06 / P2:** `email_verification.py:143–181` read/check/decrement и `DjangoEmailVerificationRepository.decrement_attempts:223` обычный read-modify-save без row locking/F update. При параллельных запросах возможна потеря decrement, resend cooldown тоже проверяется до send/save. Confidence средний: исходная race window конкретна, concurrent PG exploit не воспроизведён. Owner Django/DB/integration; проверять после SEC-01, не представлять как уже доказанный unlimited OTP bypass.
- `validate_pricing_import_view` полагается на admin_view (active staff), без отдельного `has_change_permission`; этот endpoint не сохраняет данные. Возможность несовпадения UI capabilities и validation permission — P3 review, не установлен write escalation.
- Auth control flow распределён между view/controller/repository/service и Google adapter; `ok` сейчас смешивает идемпотентный статус с правом логина. Конкретный ущерб учтён SEC-01, не дублировать его как отдельную архитектурную уязвимость.

## 5. Risks

- **SEC-07 / P2, source risk:** `views.py:1707 account_login` и `:1754 UserPasswordResetView` не имеют найденного application-level rate limit; rg по settings/auth controller/views/nginx template не выявил login/reset limiter. Возможны password guessing/SMTP abuse; наличие внешнего WAF/host-level controls не установлено, attack/load tests не выполнялись. Owner security/release/Django: bounded abuse-control design и isolated tests, без blanket lockout/DoS против легитимных пользователей.
- Production normalized duplicate email groups=2, accounts=6 (E3), unique normalized email index отсутствует. Это identity ambiguity и blocker local0101/Google deployment. Не выбирать владельца адреса автоматом; manual_review с DB/Django. SEC-01 действует и без дубликатов.
- E4 port8000 слушает all interfaces. External firewall reachability неизвестна; не объявлять подтверждённый proxy bypass. Release должен проверить boundary read-only по конфигурации в отдельном плане.
- Source review uploads/imports не покрывает все admin plugins, каждый file type и все client imports. SSRF/RCE/IDOR на непроверенных поверхностях остаются NOT TESTED, а не PASS.

## 6. Dead/legacy candidates

- SpecialistDocument и team tables с0rows: **UNKNOWN / latent functional surface**, не CANDIDATE-FOR-REMOVAL на основании counts.
- Root compatibility `config`/`catalog.admin` wrappers: **ACTIVE compatibility**, не дубли auth security logic.
- Старые image layers с `.env`: **exposure-assessment required**, не cleanup-authorized. Ни файлы, ни credentials, ни accounts не удалялись.
- Отдельная insecure JSON serializer реализация не “dead”: активно вызывается всеми перечисленными SEO payloads; исправление должно согласовываться как общий contract.

## 7. Tests gaps и выполненные проверки

**Executed здесь:** source/diff чтение; noDB JSON-LD proof для3snapshots; full actual Django Client OTP reproduction1case. Existing regression suites не перезапускались этим специалистом. Исторические77/186 tests не выдаются за текущую security coverage. Команды выполнены в `C:\kidsmap`, Python3.14/Django6.0.2, WORKTREE выше. Initial harness failure: полное очищение env удалило Windows SYSTEMROOT, вызвало WinError10106 до Django setup; исправлена только OS allowlist test harness. Final OTP command exit0, GET200/POST302/authenticated_as_target=true. JSON proof initial marker assertion fail описан SEC-02; final exit0,3/3 breakouts.

Ниже точные успешные Python bodies, исполненные PowerShell `@' ... '@ | .venv\Scripts\python.exe -`. Environment whitelist исключает унаследованные DB/Redis/Google/SMTP credentials; DB создаётся лишь в памяти. Это reproduction уязвимости: его assertions ожидают нынешнее плохое поведение, **не** будущие regression success criteria.

```python
import os, sys, tempfile, socket, json
safe_env = {key: value for key, value in os.environ.items() if key.upper() in {'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATH'}}
os.environ.clear()
os.environ.update(safe_env)
os.environ.update(DJANGO_TESTING='1', DJANGO_DEBUG='1', DJANGO_SECRET_KEY='audit-isolated-not-production', DJANGO_SETTINGS_MODULE='config.settings', DJANGO_ALLOWED_HOSTS='testserver', INDEXNOW_KEY='', GOOGLE_OAUTH_CLIENT_ID='', GOOGLE_OAUTH_CLIENT_SECRET='')
sys.path.insert(0, os.path.abspath('src'))
def blocked(*args, **kwargs): raise RuntimeError('network blocked for audit')
socket.create_connection = blocked
socket.socket.connect = blocked
from django.conf import settings
settings.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
settings.CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
settings.MEDIA_ROOT = tempfile.mkdtemp(prefix='kidsmap-security-audit-')
settings.ALLOWED_HOSTS = ['testserver']
settings.INDEXNOW_ENABLED = False
settings.LOCAL_ANALYTICS_STORAGE_ENABLED = False
settings.GOOGLE_ANALYTICS_MEASUREMENT_ID = ''
import django
django.setup()
from django.core.management import call_command
call_command('migrate', verbosity=0, interactive=False)
from django.contrib.auth import get_user_model
from catalog.models import UserEmailVerification
from django.utils import timezone
from django.test import Client
from django.urls import reverse
from django.utils.translation import override
user = get_user_model().objects.create_user(username='audit_synthetic_verified', email='synthetic-audit@example.invalid', password='not-submitted-in-request', is_active=True)
UserEmailVerification.objects.create(user=user, email=user.email, is_verified=True, verified_at=timezone.now(), code_hash='', expires_at=None, attempts_left=0)
client = Client(enforce_csrf_checks=True)
with override('ru'):
    login_url = reverse('account_login')
    verify_url = reverse('account_verify_email')
resp = client.get(login_url)
csrf = client.cookies['csrftoken'].value
assert client.session.get('_auth_user_id') is None
response = client.post(verify_url, {'email': user.email, 'code': '314159', 'form_action': 'verify', 'csrfmiddlewaretoken': csrf})
print(json.dumps({'case': 'SEC-OTP synthetic verified account arbitrary code', 'database': 'disposable in-memory SQLite', 'network': 'blocked', 'csrf_enforced': True, 'get_login_status': resp.status_code, 'post_verify_status': response.status_code, 'authenticated_as_target': client.session.get('_auth_user_id') == str(user.pk), 'fixture_code_hash_empty': True, 'fixture_attempts_zero': True}))
assert response.status_code == 302
assert client.session.get('_auth_user_id') == str(user.pk)
```

```python
import ast, json, subprocess
from pathlib import Path
from html.parser import HTMLParser
from django.template import Engine, Context
class Parser(HTMLParser):
    def __init__(self): super().__init__(); self.scripts=[]
    def handle_starttag(self, tag, attrs):
        if tag == 'script': self.scripts.append(dict(attrs))
for revision in ('WORKTREE', 'HEAD', '86a0b8cf64a8835f310a608a3428c60f1fc5341a'):
    path = 'src/catalog/services/seo.py'
    source = Path(path).read_text(encoding='utf-8') if revision == 'WORKTREE' else subprocess.check_output(['git','show',revision+':'+path]).decode()
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == '_build_breadcrumb_schema')
    ns = {'json': json}
    exec(compile(ast.Module(body=[node],type_ignores=[]), path, 'exec'),ns)
    marker = '</script><script id=audit-marker>/* inert audit marker */</script>'
    encoded = ns['_build_breadcrumb_schema']([{'name':marker,'url':'/local-fixture/'}])
    tpath = 'src/catalog/templates/catalog/place_detail.html'
    template_source = Path(tpath).read_text(encoding='utf-8') if revision=='WORKTREE' else subprocess.check_output(['git','show',revision+':'+tpath]).decode()
    sink = next(line.strip() for line in template_source.splitlines() if 'place_breadcrumb_schema_json|safe' in line)
    rendered = Engine().from_string(sink).render(Context({'place_breadcrumb_schema_json':encoded}))
    parser = Parser(); parser.feed(rendered)
    escaped = any(s.get('id') == 'audit-marker' for s in parser.scripts)
    print(json.dumps({'revision':revision,'proof':'actual breadcrumb serializer and actual template sink, AST-loaded noDB','json_valid':bool(json.loads(encoded)),'script_elements':len(parser.scripts),'inert_marker_broke_out':escaped}))
    assert escaped and len(parser.scripts)==2
```

**Not run / gaps:** live OAuth client/callback, production attack or private media fetch, regular account permission matrix in PostgreSQL, concurrent OTP/resend/linking, malformed upload/import matrix, dependency advisory scan, external firewall/image registry access, actual browser JSON-LD execution. No credentials/access request required for the completed isolated checks; absent live OAuth is out of this audit's scope.

**Required future regression:** anonymous already-verified with wrong/expired/empty challenge cannot authenticate; valid pending code single use; concurrent attempts/resend; unchanged inactive suspension; profile-email changes and duplicate email ambiguity; Google-created verified account cannot use the bypass; safe script serialization across all locales/schema types; direct protected path denies anonymous; owner/previous-owner/team/staff permission matrix; upload byte/pixel/type/path/multipart limits. Tests must assert secure intended behavior, not adjust assertions merely for green.

## 8. Recommendations

1. Orchestrator: вынести SEC-01 как первый конкретный decision item. Подтверждение статуса email не является свежим доказательством владения аккаунтом. Согласовать минимальный fix + negative tests + проверяемый deployment/response plan отдельно; Google release пока paused.
2. Параллельно спланировать SEC-02 serializer contract вместе с SEO владельцем, SEC-03 image exposure review с release, SEC-04 DB grants с database. Не объединять их в бесконтрольный production cleanup.
3. До Specialist documents activation закрыть SEC-05 на storage и reverse proxy, затем проверить authorization route и direct path на local fixtures.
4. SEC-06/07 и прочие gaps проверить на disposable PG/cache/media. Baseline auth tests не заменяют adversarial boundary cases. Не воспроизводить эти payloads на production.

## 9. P0 / P1 / P2 / P3

| Priority | Findings | Решение и границы |
|---|---|---|
| P0 | Нет подтверждённых | Факт текущей компрометации/аварии не установлен |
| P1, первым | SEC-01 | Полный local authentication bypass; root E7 подтверждает live prerequisites; срочный approval на конкретный fix scope |
| P1 | SEC-02 | Reproduced raw-script boundary, publication prerequisite; не live exploit |
| P1 | SEC-03, SEC-04 | Confirmed active image secret packaging и actual DB superuser; external compromise не доказан |
| P2 | SEC-05 | Latent private-media bypass, live documents0; blocker будущей активации |
| P2 | SEC-06, SEC-07 | Concrete source concurrency/throttling risks; exploitation/upstream controls не проверены |
| P3 | Validation permission consistency, security regression/documentation debt | Review вместе с назначенными owners; не удаление и не автоматический fix |

Все рекомендации переданы orchestrator для cross-review в MASTER_AUDIT. Этот отчёт не разрешает application или production изменения.
