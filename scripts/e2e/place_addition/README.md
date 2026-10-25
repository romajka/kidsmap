# Permanent-place browser acceptance

Runs the actual administrator and owner forms, CSRF, uploads, PostgreSQL saves,
moderation and public pages. All data is fictional. No production profile is accepted.

First run `scripts/run_isolated_quality.py` with a new disposable Unix-socket
PostgreSQL profile. Use the same `--profile-root` and `--socket-dir` below.
The profile must attest `qa_stage04` and have isolated media, cache, email and locales.

```bash
python scripts/e2e/place_addition/seed.py --profile-root "$QUALITY_PROFILE_ROOT" --socket-dir "$QUALITY_SOCKET_DIR" --output .tmp/place-addition-e2e/fixture.json
python scripts/e2e/place_addition/serve.py --profile-root "$QUALITY_PROFILE_ROOT" --socket-dir "$QUALITY_SOCKET_DIR" --port 8898
# In a second terminal, with Playwright 1.62.1 and its Chromium installed:
node scripts/e2e/place_addition/run.cjs --fixture .tmp/place-addition-e2e/fixture.json --group full --output .tmp/place-addition-e2e/results
python scripts/e2e/place_addition/verify.py --profile-root "$QUALITY_PROFILE_ROOT" --socket-dir "$QUALITY_SOCKET_DIR" --fixture .tmp/place-addition-e2e/fixture.json --results .tmp/place-addition-e2e/results/results.json
```

`fixture.json` contains synthetic login credentials; keep it in ignored local QA
storage. Upload only `results/` to CI artifacts. `seed.py` creates fixtures and
records their original business state. Do not reseed between the browser run and
preservation verification. `verify.py` uses an explicit read-only transaction.

The runner checks the server's boot-time source manifest against the fixture and
local files. After application changes, rebuild locales, restart the QA server and
create a new fixture snapshot before the next acceptance run.

Groups: `smoke`, `create`, `publish`, `visual`, `pricing`, `json`, `regression`,
`limits`, `compact`, `guidance`, `full`. Only `full` runs every group. Failures return a nonzero exit code
and retain screenshots/results; a successful subgroup is not full acceptance.
Optional runtime paths: `KIDSMAP_PLAYWRIGHT_MODULE`, `KIDSMAP_BROWSER_EXECUTABLE`.
`KIDSMAP_BROWSER_ENGINE=chromium|firefox|webkit` chooses an SDK engine; leaving
the executable override unset uses that SDK's matching installed revision.
The actual engine and version are recorded in `results.json`.

Coverage includes both roles, creation/publication in RU/1440, AZ/390, EN/768,
42 language/viewport layouts, canonical product and price types, four place price
policies, tariff limits/reordering, JSON round trip, ownership denial, no-op saves,
upload failure/retry and invalid files. The compact group verifies hidden phone
country, AZ local calling numbers with international WhatsApp, all WhatsApp modes,
published contact revisions through real moderation, optional disclosures and full
USD/EUR tariff preservation when editing contacts. Assertions are recorded per scenario.
The guidance group covers required-field checks, trusted phone insertion rejection,
Unicode/length/line counters, exact tariff-field errors, current-form preview in a
new tab with two distinct decoded uploads, save/edit after preview, failed check
retry and an edit racing an in-flight check. Shared adoption contract:
`docs/ui/editor-interaction-contract.md`.

Additional `roles` group requires `seed_roles.py --fixture <existing fictional fixture>
--output <new private role fixture>` with the same isolated profile/socket arguments.
It adds two synthetic volunteer accounts without reseeding the protected places.
The role journey uses actual volunteer/owner/admin forms, full candidate review,
return with reason, correction/resubmission, approval, final rejection, public
isolation, catalog/home/profile and subsequent editing. `verify_roles.py` checks
the resulting three controlled cards/revisions through SQL READ ONLY. Run the
ordinary `verify.py` afterward against the original fixture to recheck preservation.
CI runs `full` and then `roles` separately; a successful role run is not a new full run.
New owner publication candidates use the unified moderation center; ownership
requests remain a distinct queue. Home rails are ranked/recommended, not a promise
that every new card remains on the home page.
Several matrix IDs cover more variants than this automation executes; consult
the dated QA report before treating an entire ID as accepted.

External network is blocked. Real map-provider integration, mobile OS keyboard/file
picker and physical-device checks require separate acceptance. A smoke run in a
second engine establishes only the scenarios actually recorded in that run.
Desktop viewport screenshots do not establish physical-device results.
# Refinement acceptance

`--group refinement` checks the continuous owner form: compact age choices, no intermediate navigation, no schedule counters, translated notes, sustained error focus, pricing footer alignment and custom public links. It renders AZ/RU/EN at 360, 390, 768, 1024, 1280 and 1440px, then saves a new owner card, previews its named link, submits it and approves it through the real moderation center. The link must appear on the same public card afterward. It is a separate CI step after the role journey.

Custom public links use the additive migration `0146_place_public_links`. Existing fixture baselines without the new column explicitly expect the empty migration default; all other preservation checks remain unchanged. A missing field in an older edit preserves saved links; an explicit empty list removes them through the candidate workflow. JSON prompts document the five-link limit and named HTTP(S) URLs.

## Feedback acceptance (2026-10-25)

`--group feedback` requires the role fixture. It checks live counters (including unlimited descriptions and restored text), recommended translations with a keyboard-accessible explanation, publication-required markers, three phone slots without renumbering saved values, separate messengers/social links, and all five schedule presets with serialized-day assertions. Free-entry pricing changes the visible wording to paid services while preserving the exact tariff JSON. Actual computed chevrons, padding and gaps are asserted.

The owner matrix covers AZ/RU/EN at 360, 390, 768, 1024, 1280 and 1440px; admin and volunteer cover the same languages at 390 and 1440px. It then saves/reopens an owner card with three phones, international WhatsApp and Telegram, previews it privately, submits it, inspects and approves it through the moderation center, and checks the public catalog/detail. Google uses the configured site provider; tests block external traffic and verify usable fallback controls without silently requesting OSM tiles. Physical devices and a real configured Google SDK require separate acceptance.
