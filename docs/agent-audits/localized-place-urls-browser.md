# Localized Place URLs — rendered browser verification

Date: 2026-09-14. Role: browser-qa, definition `.agents/agents/browser-qa/agent.md`. Approved LOCAL implementation verification. LOCAL HEAD `ef91dbe761f340a2c4d37bdc0b96638522aa6edf`; tests run against evolving dirty WORKTREE, not HEAD or production. Production not contacted.

## Environment and executed checks

Real Chromium1228 / Playwright on `http://127.0.0.1:8769`, disposable PostgreSQL urltest55439 and synthetic accounts supplied by parent. DJANGO_TESTING=1 and isolated settings supplied by parent. All external browser requests aborted. Browser launch required sandbox escalation because sandbox denied Chromium socket operations; automatic review allowed local browser execution. CLI daemon attempt failed; used existing standalone Playwright script, no @playwright/test.

- Public AZ/RU/EN ×390/768/1024/1280/1440: actual canonical, hreflang and desktop language-link targets match `/place/1-oyuncaq-muzeyi/`, `/ru/place/1-muzei-igrushek/`, `/en/place/1-toy-museum/`.
- Admin permanent add (`?type=permanent`) and edit ×3 locales ×5 widths:30 cases, no horizontal overflow. Prompt contains new three-language names/automatic URLs section; copy, edit/reset and Escape close pass in every locale.
- Volunteer add ×3 locales ×5 widths:15 cases, no overflow; same instruction copy/reset verified.
- Real admin JSON names import, confirmation modal, save, localStorage clear and reload: three imported names persist, old URL triplet stable. Parent independently verified database all three names changed and all three slugs unchanged. First save attempt failed on incomplete synthetic location fixture; fixed fixture then reran successfully. Reload without clearing localStorage is insufficient evidence of persistence.
- URL copy produces absolute local-origin address; displayed path is relative and read-only (no editable inputs).
- Two browser navigations to old RU legacy address end at localized RU200; no redirect loop.
- No pageerrors, no local static404 in matrix. Initial missing synthetic photo404 fixed by parent; post-login `/accounts/profile/`404 remains unrelated to localized URL controls.

## Findings and resolution

1. RU URL block initially rendered AZ strings because RU gettext entries missing, default-AZ fallback. Reproduced screenshot `output/playwright/url-admin-edit-ru-390.png`. Admin owner added RU identity entries and a render regression; final rerun recorded below.
2. Names-only JSON import erased existing tariffs. Reproduced real save plus parent DB check, then added RED browser assertion `Partial JSON must preserve existing tariffs` (`[]` vs fixture tariff). Admin owner changed importer to normalize only explicit pricing_plans/tariffs keys; explicit[] retains clear semantics. Final GREEN recorded below.
3. Public1024 overflow with blocked external icon fonts: header `.km-header-inner` exceeds viewport, icon `expand_more` renders as wide text (about120px), forcing right header past viewport. Other12 public viewport cases had no overflow. This run cannot establish production layout with fonts loaded. No localized URL layout code implicated; existing header was not edited by browser role.

## Reproduction and artifacts

Reusable command (local-only configuration file contains disposable session and add/edit paths, not committed):

```bash
PLACE_URL_BROWSER_ORIGIN=http://127.0.0.1:8769 PLACE_URL_BROWSER_CONFIG=/tmp/url-browser-config.json PLAYWRIGHT_MODULE=/home/ramin/.nvm/versions/node/v20.20.2/lib/node_modules/@playwright/cli/node_modules/playwright CHROMIUM_EXECUTABLE=/home/ramin/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome node scripts/test_localized_place_urls.cjs
```

Additional exact executed commands: `node /tmp/url-browser-matrix.cjs` (45 public/admin cases); `node /tmp/url-browser-volunteer.cjs` (15 volunteer add cases); `node /tmp/url-browser-flow.cjs` (import/save/reload/copy/redirect). Scratch scripts contain only synthetic local fixture references; screenshots under ignored `output/playwright/url-*.png`. Matrix output `/tmp/url-browser-results.json`.

## Boundaries

No production migrations/deployment, search engine crawl, real external map/auth/tracking, or cross-engine browser coverage. Blocked-font layout findings do not prove production defect. No full keyboard/accessibility audit; dialog Escape and interactive copy/reset exercised. Snapshot/source changes required server restart because runserver used --noreload; parent coordinated restarts.

## Final rerun evidence

- `node /tmp/url-browser-volunteer-edit.cjs`:15 volunteer edit207 cases AZ/RU/EN ×5 widths PASS, no overflow; instruction copy/reset pass. Total75 matrix cases across public/admin add/edit/volunteer add/edit.
- Reusable command above final exit0 PASS after adding three pricing assertions: omitted pricing preserves populated fixture tariff, explicit `pricing_plans:[]` clears only temporary form state, legacy `price_per_lesson:25` creates one normalized plan priced25. No saving this regression's temporary changes.
- `node /tmp/url-browser-final-label.cjs`: final RU rendered block has «Адреса карточки», «Скопировать», «Открыть», saved-status Russian text after parent restarted gettext cache. Visually inspected final mobile screenshot `output/playwright/url-admin-edit-ru-final-390.png`.
- Same final probe allowed **only** fonts.googleapis.com/fonts.gstatic.com in addition to localhost, all other integrations still blocked. `document.fonts.check('24px "Material Symbols Rounded"')` true. Authenticated public RU1024 scroll width1025: large missing-font overflow resolved, residual1px header overflow remains. Screenshot `output/playwright/url-public-fonts-1024.png` visually inspected. P3 existing header polish recommendation; no unrelated layout edit. This font-enabled probe was RU1024 only, not all75 cases.

Changed files owned by browser role: this report and `scripts/test_localized_place_urls.cjs` (language-neutral new-preview state, absolute clipboard/read-only assertions, tariff omission/clear/legacy compatibility checks, race-free response wait). No application implementation edits, no commit/push.

### Final screenshot correction and contrast check

Parent review found the earlier `url-admin-edit-ru-final-390.png` had captured an empty scrolled area; that earlier artifact is **not** visual proof. Recaptured after explicitly scrolling the URL block to220px below the sticky section navigation and waiting for layout; inspected both the replaced full viewport screenshot and new cropped `output/playwright/url-admin-edit-ru-final-block-390.png`. Both now visibly show all three URLs, Russian labels, copy/open controls and saved-status text without clipping.

Post parent CSS `color:inherit` change: computed URL `<code>` text RGB(30,41,59), white section background RGB(255,255,255),12.25px. WCAG relative-luminance contrast approximately14.63:1. Pink Bootstrap code text no longer appears. This was a scoped real-browser visual/color probe; no functional JS change, so full functional matrix was not repeated. Command: `node /tmp/url-browser-final-label.cjs`, exit0.

Same final font-enabled RU1024 probe now reports scrollWidth1024 and overflow=false. Earlier1px measurement was not reproducible on this final pass; treat it as a transient/unresolved measurement, not a confirmed remaining defect. No header edits were made by browser role.
