# Browser QA — 2026-09-08

Role: `browser-qa`; execution identity: `/root/audit_browser`, independently executed runtime checks. Definition: `.agents/agents/browser-qa/agent.md`. AUDIT ONLY; no application edits. LOCAL HEAD `d75b34f4db5d4ba484cf8392ff3ae0c9939031e2`, existing dirty agent/report work preserved. PRODUCTION: UNKNOWN, not contacted.

## 1. Состояние области

Real Chromium via Playwright MCP and installed Playwright library, isolated root-managed Django `http://127.0.0.1:8765`. Root supplied disposable SQLite/media and synthetic accounts. Browser route interception allowed localhost HTTP only; external fonts/CDN requests aborted. No production login/data, auth bypass, injection or publication. Normal local login and one synthetic favorite mutation only. Browser did not stop root server.

80 unique layout cases at viewport height900, widths390/768/1024/1280/1440:

| Surface | Actual routes | Languages | Cases |
|---|---|---|---:|
| Public home | `/`, `/ru/`, `/en/` | AZ/RU/EN | 15 |
| Catalog | `/catalog/`, `/ru/catalog/`, `/en/catalog/` | AZ/RU/EN | 15 |
| Detail | `/place/1-audit-usaq-merkezi-1/` and RU/EN prefixed equivalents | AZ/RU/EN | 15 |
| Authenticated favorites | `/account/favorites/` and RU/EN prefixed equivalents | AZ/RU/EN | 15 |
| Admin dashboard/edit | `/admin/`, `/admin/catalog/place/1/change/` | RU rendered | 10 |
| Volunteer dashboard/add | `/admin/volunteer/`, `/admin/volunteer/add/` | RU rendered | 10 |

Layout cases mean DOM measurement, not 80 individually reviewed screenshots or complete workflows. Screenshots visually inspected: catalog768, admin form390, volunteer form1440. Public MCP matrix: no pageerror, no HTTP≥400 response, no broken image among inspected image elements. Staff pages: no pageerror; intentional blocked Google fonts and volunteer Leaflet separated from application HTTP errors. The local `/accounts/profile/`404 is BR-003. Initial failed CLI launch was environment-only (missing bundled browser, then sandbox socket denial); installed Chrome under approved escalation completed both scripts with exit0.

## 2. Сильные стороны

- Public home/detail at390/768/1280/1440 showed no document overflow across AZ/RU/EN in the blocked-CDN environment. At1024 see BR-004.
- Admin dashboard and volunteer dashboard/add had no document overflow across all five widths.
- Mobile drawer390 opens, focuses close button, sets `aria-expanded=true`, closes on Escape and returns focus to burger (`aria-expanded=false`). Dialog has `aria-modal=true`. Focus trap exhaustiveness was not tested.
- Owner normal login with explicit favorites `next` lands correctly. Clicking English fixture detail favorite changed accessible name to `Remove from favorites`; its card appeared in `/en/account/favorites/`.
- Local image assets rendered. Volunteer map explicitly reports unavailability when Leaflet is blocked instead of throwing pageerror.

## 3. Реальные проблемы

**BR-001 — P2: decorative catalog orb creates horizontal document overflow.** Environment: isolated LOCAL runtime. Across AZ/RU/EN catalog, width768 → scrollWidth803; width1280 →1315. `.faq-hero-orb1` right edge≈803 at768. Diagnostic temporary DOM `display:none` for that orb immediately reduced document width803→768 (no source/save changes). Source: `static/css/pages/catalog_places.css:1773` forces hero `overflow:visible`; `:1796` orb340px with `right:-50px`. High confidence, reproducible independent of font glyph widths. Impact: unnecessary horizontal scrolling and displaced viewport content. Owner: public frontend. Next: clip decoration independently of hero dropdowns, then recheck full locale/width matrix. Evidence: E1.

**BR-002 — P2: admin Place edit is wider than mobile viewport.** Environment: LOCAL `/admin/catalog/place/1/change/`, RU, synthetic published fixture. Width390 → document804; width768 →829. At390 multiple `.km-pf-field__control`/textarea right edges635, audit inline table right741. At1024/1280/1440 document equals viewport. This is not the public Material Symbols header failure: staff uses different controls and local icon fonts. High confidence in rendered defect, root CSS cause not isolated. Impact: staff needs horizontal scrolling to reach portions of editor. Owner: admin frontend; next inspect minimum sizes/long content and constrain form/table overflow locally. Evidence E2/E3.

**BR-003 — P2: direct admin login ends at a404.** Environment: LOCAL normal synthetic staff login from `/admin/login/` without `next`. Valid admin and volunteer credentials were accepted, navigation ended at `/accounts/profile/`, which returned404. Subsequent authorized `/admin/` or `/admin/volunteer/` returned200, so login succeeded but its landing route failed. Reproduced admin twice, volunteer once. High confidence for this explicit trigger; login through a protected page with populated `next` was not separately checked. Impact: confusing broken first screen for direct-login users, dashboard remains reachable. Owner: Django/auth reviewer. Next: verify LoginView redirect configuration and explicit safe default. Evidence E2/E3; do not extrapolate to production.

**BR-004 — P2 conditional resilience: blocked icon-font stylesheet exposes ligature text and enlarges header.** Environment intentionally aborts Google Fonts. `src/catalog/templates/base.html:50` loads Material Symbols from Google. Font inventory contained only local `Chiron GoRound TC Public`; `expand_more` rendered as wide text (chevron≈116px). At1024 home/catalog/detail document widths AZ1232/RU1225/EN1170. Authenticated favorites1024 measured AZ1383/RU1366/EN1326; at1280 AZ1309/RU1291. These are verified degraded-network outcomes, NOT normal online layout findings or observed Google outage. Owner: public frontend. Next: decide local font/icon fallback, test with approved local font asset. Evidence E1/E3, template source. No external stylesheet fetched to eliminate this condition.

**BR-005 — P3: AZ/EN drawer retains Russian helper text and accessible names.** Actual390 DOM on `/` (`lang=az`) and `/en/` (`lang=en`) shows “Войдите для сохранения избранного и управления местами”, “Бесплатное размещение для организаторов”, “Язык сайта”. Dialog/close aria labels also remain Russian. Source `src/catalog/templates/includes/header.html:271,292,335,355,445` uses translation tags; issue is runtime translation coverage, not absence of tags. High confidence. Impact: mixed-language mobile UI and screen-reader names. Owner: public frontend/localization; next complete catalogs and confirm actual rendered AZ/EN. Evidence E4.

**BR-006 — P2: volunteer add has no visible price-mode selector.** `/admin/volunteer/add/`: `[name=price_mode]` is hidden input with value `tariffs`; visible Price/Age section offers tariff creation but no free/events-mode controls. Readiness hint asks to add a tariff “или выберите подходящий режим цены (бесплатно / вход бесплатно / по мероприятиям)”, so it instructs a selection the rendered form does not expose. High confidence for default add form; successful saving of alternative modes not attempted. Owner: volunteer/admin frontend with business-rule reviewer. Next: verify intended volunteer permissions and expose authorized mode selection, avoiding duplicated backend enums. Evidence E2 and screenshot `volunteer-form-1440.png`.

## 4. Tech debt

CDN-dependent icon rendering lacks robust layout bounds in tested offline state (BR-004). Staff mobile form and shared public header require separate acceptance suites. Existing DOM/translation tags cannot replace real locale render assertions. Volunteer pricing instruction/control mismatch needs one maintained interaction contract.

## 5. Risks

External integrations intentionally unavailable: Google Maps/Leaflet tiles, Google login, third-party fonts, real analytics. External failures are environment outcomes, not proven production defects. Initial owner login through admin form was correctly unsuitable for a nonstaff account; this was discarded and owner retested through public login. Initial staff screenshots after viewport sweeps can reflect resized sidebar state; no sidebar-overlay finding inferred from those images. Fixture title/phone/records are synthetic. No private records or credentials copied into report.

## 6. Dead/legacy candidates

None established by this browser audit. Do not delete CSS, routes, pricing fields or compatibility markup from these observations.

## 7. Tests gaps

Executed commands: `node /tmp/kidsmap-audit-20260908-browser/auth-smoke.cjs` and `node /tmp/kidsmap-audit-20260908-browser/focused.cjs`, installed Chrome, approved sandbox escalation, final exits0. Public45-case sweep and drawer/filter interactions executed through `mcp__playwright__browser_run_code_unsafe`. Favorites15 cases and staff20 cases have file-backed measurements. Auth smoke owner's first5 cases were redirected login pages and are explicitly excluded from the80 valid cases; focused public-owner run replaces them.

Evidence inventory, local ephemeral artifacts:

- **E1:** MCP public45-case transcript; `/tmp/kidsmap-audit-20260908-browser/catalog-az-768.png`; diagnostic803→768 orb result.
- **E2:** `/tmp/kidsmap-audit-20260908-browser/auth-results.json`; admin/volunteer screenshots and synthetic DOM text in same directory.
- **E3:** `/tmp/kidsmap-audit-20260908-browser/focused-results.json`; `admin-form-390.png`, `admin-fields-390.png`, `favorites-en-1440.png`.
- **E4:** MCP AZ/EN390 drawer DOM transcript; `drawer-az-390.png`.

NOT RUN: full staff AZ/EN locale matrix; all content states;320/360; contrast audit; screen reader; exhaustive focus trap; sticky overlap scrolling; submit/save/readiness validation; owner wizard; tariff-currency editing; malformed-input/security probes; upload; real maps/OAuth/analytics. Mobile Filters button clicked and document stayed390, but semantic/focus/submit behavior was not completed: no claim of filter acceptance. No automated regression suite added or run by this role.

Graph: list_projects selected `/home/ramin/kidsmap`, index ready8400nodes/31445edges; architecture summary inspected. Template parsing gaps and graph coverage are not exhaustive; source literals inspected directly for cited CSS/templates. DOM defects do not rely on absence in graph.

## 8. Recommendations

Django/auth reviewer: verify BR-003 landing default. Admin frontend: isolate BR-002 mobile constraints and BR-006 volunteer pricing controls. Public frontend: fix BR-001 decoration containment, decide BR-004 local icon fallback, complete BR-005 translations. These are recommendations only; require concrete authorized implementation scope before application edits. Preserve screenshot distinctions between blocked CDN and normal assets.

## 9. P0/P1/P2/P3

| Priority | Findings |
|---|---|
| P0 | None confirmed |
| P1 | None confirmed |
| P2 | BR-001, BR-002, BR-003, BR-006; BR-004 conditional on unavailable external icon font |
| P3 | BR-005 |

No production conclusion. Browser runtime complete; root informed local server can be stopped by its owner.
