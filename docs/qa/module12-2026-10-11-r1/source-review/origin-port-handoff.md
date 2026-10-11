# Fresh origin/port source handoff

Execution `/root/analytics_source`; AUDIT ONLY, source-review ownership. Parent reported native same-origin requests from its isolated `localhost:8829` stand return `403 forbidden_origin`; attribution: **parent native browser**, not independent browser execution here.

Verified root cause in actual WORKTREE and HEAD:

- `src/catalog/views.py:234–241`, `_allowed_tracking_hosts`: splits request host at first `:`, yielding `localhost`; similarly removes port from each configured trusted origin.
- `src/catalog/views.py:245–265`, `_has_allowed_tracking_origin`: passes full Origin (or full Referer fallback) to Django `url_has_allowed_host_and_scheme` with that hostname-only set.
- Installed Django 6.0.2 helper `.venv/Lib/site-packages/django/utils/http.py:275–305`: tests `url_info.netloc in allowed_hosts` at line303. Netloc for legitimate `http://localhost:8829` is `localhost:8829`, unequal to `localhost`.
- Endpoint `views.py:640–644` records rejection and returns403 before the controller/storage. Result does not prove a click-payload/privacy/alias bug; those downstream assertions were blocked by this single ingress defect.

Command (DJANGO_TESTING set; no Django.setup/HTTP/DB):

```powershell
$env:DJANGO_TESTING='1'
.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/source-review/origin_checks.py
```

Exit0; seven source-function implementation checks, app matches HEAD after newline normalization. `origin-checks.json` records actual app/helper hashes, definitions and selected public synthetic cases. Same local Origin with8829 returnsFalse; portless local Origin True; ported same-host Referer False; configured trusted ported origin False; evil.example remainsFalse. Initial source-read commands with a nonnumeric Select-Object First argument failed and were corrected; they did not mutate files or influence these results.

Classification: reproducible **pre-existing HEAD application validation failure on the audited nondefault-port stand**, not environment unavailable. Production/custom-port use UNKNOWN, never inferred. Likely P2: legitimate local/nondefault-port contact analytics rejected, independent storage retains server views but loses click actions. Parent assigns final ID/severity after native evidence. Portless production delivery remains NOT RUN.

## Continue independent backend checks with QA-only transport adapter

For only the own stand URL `http://localhost:8829/{lang}/events/track/`, POST, and only headers whose original parsed origin equals the own stand, use Playwright request interception to rewrite Origin to `http://localhost` and same-origin Referer to the same path with port omitted. Keep all remaining headers/payload/cookies unchanged. Foreign/malformed-origin scenarios bypass this adapter and must retain their actual denial. Do not change app middleware, settings rules, existing assertions or endpoint code.

This changes transport semantics: mark **SIMULATED transport** on every dependent private-ID/aliases/repeats/invalid-payload/ingress-count assertion, capture before/after aggregates and adapted header booleans. Preserve the initial native403 evidence. Real unadapted CTA acceptance stays FAIL under the ingress defect; downstream initially blocked checks stay NOT RUN unless separately executed under the adapter. Adapter success cannot replace the native failure.

Named handoff: `/root` for native actual phone/contact clicks and final finding; `integration-reviewer` for independent isolated controller assertions and adapter coverage. No application fix made.
