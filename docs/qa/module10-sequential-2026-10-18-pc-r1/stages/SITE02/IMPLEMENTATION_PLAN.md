# SITE02 Implementation Plan — authorized sequential module10 work

**Goal:** Saved localized About/empty-result text must appear publicly for AZ/RU/EN.
**Architecture:** Existing SiteSettings i18n/context values remain the source of truth; remove template branches that take precedence over them. Blank values retain existing context defaults; retain automatic HTML escaping.
**Scope:** src/catalog/templates/pages/about.html, src/catalog/templates/catalog/place_list.html, new src/catalog/testcases/test_site_qa02_public_copy.py. No model/schema/permissions/CSS/JS/PO change. Concrete root and affected template blocks reviewed; narrow branch-priority change only.
**Authorization:** User explicitly requested analysis and immediate fixes for the listed15findings in order; no repeated approval required. No commit/push/deploy/production.

- [ ] Run complete4method regression in own scratch against unchanged source; confirm context values are saved but AZ public text fails.
- [ ] Change About to if site_about_text first, then existing localized literals; change empty heading to if site_empty_results_text first, then AZ/localized literals. Existing context fallback is authoritative for all3languages; no copied fallback rules in JS/model.
- [ ] Copy exact reviewed regression module (test_site02_candidate.py) into the stated new test file; record before/after hashes/diff.
- [ ] Fresh GREEN4methods plus relevant existing public wiring tests with same envclear/DJANGO_TESTING=1, disposable PG/cache/media/current3locales/integrationsdisabled.
- [ ] Actual-source native admin-save→publicreadback in3languages; configured/blank/default/escaped copy; affected pages at360/390/768/1024/1280/1440, layout/focus/console/network. No injected styles, rewritten responses or fake DB equality.
- [ ] Verify source/previous packages/refs/index/foreign runtimes, record exact executed and NOT RUN; preserve synthetic fixtures/logs, append progress, continue SITE03 under same user authorization.
