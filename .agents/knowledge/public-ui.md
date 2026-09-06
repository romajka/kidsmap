# Public UI KidsMap

Срез: 2026-09-06. Источник AS-IS — текущий локальный код, включая dirty/untracked изменения.
Production имеет отдельный baseline `86a0b8c`; наличие файла локально не доказывает его деплой.
Сопоставление окружений: [deployment.md](deployment.md). Общие контракты: [source-of-truth.md](source-of-truth.md).

## Архитектура и владельцы

- Public UI — Django server-rendered templates и vanilla JavaScript/CSS. SPA/build pipeline в обследованном checkout не обнаружен.
- Общий shell: `src/catalog/templates/base.html`; основные страницы — `catalog/` и `pages/` под этой же папкой.
- URL: `src/catalog/urls.py`; root/i18n registration: `src/config/urls.py`.
- Язык по умолчанию AZ без префикса: `src/config/settings.py:433`; RU/EN — локализованные варианты.
- LocaleMiddleware: `src/config/settings.py:310`; gettext-каталоги: `locale/`.
- Frontend-public владеет templates/CSS/JS и UX. Формы, доступ, сохранение, readiness — зона Django.
- Staff admin — отдельная поверхность, см. [admin-ui.md](admin-ui.md).

## Карта источников

| Поверхность | Источник |
| --- | --- |
| Shell, header, footer, messages, analytics bridge | `src/catalog/templates/base.html` |
| Главная | `controllers/home_controller.py:37`; `templates/pages/home.html` под `src/catalog/` |
| Каталог и фильтры | `src/catalog/controllers/place_controller.py:96`, `:136`; `templates/catalog/place_list.html` |
| Карточка места | `src/catalog/controllers/place_controller.py`; `src/catalog/templates/catalog/place_detail.html` |
| Общая карточка | `src/catalog/templates/catalog/includes/place_card.html` |
| Событие | `src/catalog/views.py:1120`; `src/catalog/templates/catalog/event_detail.html` |
| SEO landing | `src/catalog/controllers/seo_controller.py`; `src/catalog/templates/catalog/seo_landing.html` |
| Account/auth | `src/catalog/templates/pages/account_*.html`; `src/catalog/templates/auth/` |
| Owner формы | `src/catalog/controllers/owner_places_controller.py`; `src/catalog/forms.py`; `templates/pages/owner_*.html` |
| Общий стиль | `static/css/site.css`, подключён `base.html:51`; `static/css/pages/`, `components/` |
| Motion | `static/js/motion.js`; `static/css/motion.css`, последний CSS layer в `base.html:97` |

Пути `controllers/` и `templates/` в таблице относятся к `src/catalog/`, если не указано иное.

## Карты и интерактивные данные

- `static/js/google_maps_markers.js` — общий слой Google markers.
- `static/js/catalog_map.js` и `home_map.js` — разные публичные карты; не заменять одну другой по совпадению функций.
- Catalog map payload: `src/catalog/controllers/place_controller.py:728`; загрузка через `place_list.html:693` (`json_script`).
- Home map payload: `src/catalog/templates/pages/home.html:327`; scripts: `:2770`.
- HTML escaping у catalog map: `static/js/catalog_map.js:99`; восстановление focus: `:473`, `:974`.
- Это подтверждение наличия механизмов, а не полный browser/accessibility PASS.
- Owner picker: `static/js/owner_place_map_picker.js`; local permanent wizard подключает Leaflet1.9.4 CDN.
- Browser Maps API key и OAuth Client — разные настройки/назначения; не подменять одну другой.

## LOCAL: незавершённая интеграция в Git

- `permanent_place_form.html`, `services/permanent_place_rules.py`, `permanent_place_wizard.py`, JS permanent_place_* — локальные untracked файлы на момент discovery.
- Wizard получает publication rules с сервера: `src/catalog/templates/pages/permanent_place_form.html:13`.
- Локальные phone reveal/photo workflow меняют cards/detail/maps/base; Google auth меняет login/register.
- Эти файлы вместе с dirty forms/controllers не считать доступными на production только по локальному чтению.
- Старые `owner_place_wizard.js` и owner templates не удалять: нужны проверка route/template selection и production usage.
- `docs/PERMANENT_PLACE_FIELD_MATRIX.md:3` описывает dirty дерево; `:180` automatic district suggestion помечен FUTURE/PLANNED.
- `PERMANENT_PLACE_IMPLEMENTATION_REPORT.md` — отчёт локальной реализации, не deployment evidence.

## Контракты изменений

- Не создавать в JS собственную трактовку tariffs/free/on-request, возраста или расписания.
- Readiness, public visibility, pricing и schedule брать из backend source-of-truth; UI показывает результат.
- Не превращать admin-only поля в owner input без backend/security review.
- Не менять локализованные URL и query semantics ради layout без SEO handoff.
- Не показывать скрытый телефон в HTML/map/JSON-LD в обход выбранного phone reveal контракта.
- Навигация, модальные окна и формы требуют проверки клавиатурой, error/loading/empty states.

## Риски и проверки

| Приоритет | Наблюдение | Уверенность |
| --- | --- | --- |
| P1 | JSON-LD `json.dumps` → `safe` в script допускает закрытие script; детали в seo.md | Высокая, isolated render |
| P2 | Browser/JS scripts не включены в `.github/workflows/deploy.yml` | Высокая, source |
| P3 | `site.css` около662KB, base.html около59KB; глобальные styles/inline JS усложняют изоляцию | Высокая для размера; runtime impact не измерен |

Минимальная browser matrix: 375/768/1024/1440px, AZ/RU/EN; каталог, карточка, auth и затронутые owner flows.
Проверять Console, Network/static404, overflow, focus, map empty/error, filter reset, back/forward.
Существуют `scripts/test_footer_overflow.sh`, `scripts/test_mobile_navigation.sh`, но требуют внешнего Playwright wrapper.
Source review не заменяет browser QA. Для production — GET/просмотр; не сохранять формы, не отправлять отзывы/CTA tracking специально.
Сценарии записи проверять на изолированных тестовых данных по workflow QA.
