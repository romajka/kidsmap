# Exact own-profile commands / exits

See raw logs and explicit RED/harness distinctions in REPORT.md. Browser native CLI0 means harness completed; accepted assertions are separately verified.

```json
{"argv": ["/home/ramin/kidsmap/.venv/bin/python", "-m", "venv", "/home/ramin/kidsmap/.tmp/offer-qa03-fix-2026-10-13-r1/venv"], "exit": 0}
```

```json
{"argv": ["docker", "run", "-d", "--name", "offer-qa03-fix-2026-10-13-r1-pg", "-p", "127.0.0.1:52167:5432", "--env-file", "/home/ramin/kidsmap/.tmp/offer-qa03-fix-2026-10-13-r1/pg.env", "-v", "offer-qa03-fix-2026-10-13-r1-pg-data:/var/lib/postgresql/data", "postgres:17-alpine"], "exit": 0}
```

```json
{"argv": ["/home/ramin/kidsmap/.tmp/offer-qa03-fix-2026-10-13-r1/venv/bin/python", "/home/ramin/kidsmap/scripts/build_isolated_locales.py", "build", "--output", "/home/ramin/kidsmap/.tmp/offer-qa03-fix-2026-10-13-r1/locales", "--locales", "ru", "az", "en", "--compiler", "native"], "exit": 0}
```

```json
{"argv": ["/home/ramin/kidsmap/.tmp/offer-qa03-fix-2026-10-13-r1/venv/bin/python", "/home/ramin/kidsmap/scripts/build_isolated_locales.py", "verify", "--manifest", "/home/ramin/kidsmap/.tmp/offer-qa03-fix-2026-10-13-r1/locales/manifest.json"], "exit": 0}
```

```json
{"argv": ["/home/ramin/kidsmap/.tmp/offer-qa03-fix-2026-10-13-r1/venv/bin/python", "/home/ramin/kidsmap/docs/qa/offer-qa03-fix-2026-10-13-r1/runtime.py", "prepare"], "exit": 0}
```

```json
{"argv": ["/home/ramin/kidsmap/.tmp/offer-qa03-fix-2026-10-13-r1/venv/bin/python", "/home/ramin/kidsmap/docs/qa/offer-qa03-fix-2026-10-13-r1/runtime.py", "check"], "exit": 0}
```

```json
{"argv": [".tmp/offer-qa03-fix-2026-10-13-r1/venv/bin/python", "docs/qa/offer-qa03-fix-2026-10-13-r1/runtime.py", "test", "catalog.testcases.test_offer_qa03_error_targets", "--verbosity=2"], "exit": 1, "seconds": 67.025}
```

```json
{"argv": [".tmp/offer-qa03-fix-2026-10-13-r1/venv/bin/python", "docs/qa/offer-qa03-fix-2026-10-13-r1/runtime.py", "test", "catalog.testcases.test_offer_qa03_error_targets", "--verbosity=2", "--keepdb"], "exit": 1, "seconds": 82.64}
```

```json
{"argv": [".tmp/offer-qa03-fix-2026-10-13-r1/venv/bin/python", "docs/qa/offer-qa03-fix-2026-10-13-r1/runtime.py", "test", "catalog.testcases.test_offer_qa03_error_targets", "catalog.testcases.test_task33_pricing.GroupPricingTests.test_target_scoped_roundtrip_and_foreign_ids", "catalog.testcases.test_task33_pricing.GroupPricingTests.test_group_age_conflict_and_currency_are_not_silently_coerced", "catalog.testcases.test_task33_pricing.GroupPricingTests.test_json_ui_validator_distinguishes_v1_from_nested_v2", "catalog.testcases.test_task33_place_continuous.ContinuousPlaceFormTests.test_group_age_conflict_and_foreign_group_id_are_rejected", "catalog.testcases.test_task33_place_continuous.ContinuousPlaceFormTests.test_published_group_price_edit_is_candidate_until_approval", "--verbosity=2", "--keepdb"], "exit": 0, "seconds": 17.581}
```

```json
{"argv": [".venv/bin/python", "/home/ramin/kidsmap/docs/qa/offer-qa03-fix-2026-10-13-r1/drive.py", "browser.js"], "native_cli_exit": 0, "result": "browser.result.json"}
```

```json
{"argv": [".venv/bin/python", "/home/ramin/kidsmap/docs/qa/offer-qa03-fix-2026-10-13-r1/drive.py", "diagnostic.js"], "native_cli_exit": 0, "result": "diagnostic.result.json"}
```

```json
{"argv": [".venv/bin/python", "/home/ramin/kidsmap/docs/qa/offer-qa03-fix-2026-10-13-r1/drive.py", "diagnostic-capture.js"], "native_cli_exit": 0, "result": "diagnostic-capture.result.json"}
```

```json
{"argv": [".tmp/offer-qa03-fix-2026-10-13-r1/venv/bin/python", "docs/qa/offer-qa03-fix-2026-10-13-r1/runtime.py", "script", "seed-fresh.py"], "exit": 0, "seconds": 15.94}
```

```json
{"argv": [".tmp/offer-qa03-fix-2026-10-13-r1/venv/bin/python", "docs/qa/offer-qa03-fix-2026-10-13-r1/runtime.py", "script", "admin-seed.py"], "exit": 0, "seconds": 5.218}
```

```json
{"argv": [".venv/bin/python", "/home/ramin/kidsmap/docs/qa/offer-qa03-fix-2026-10-13-r1/drive.py", "browser.js"], "native_cli_exit": 0, "result": "browser.result.attempt1791897302.json"}
```

```json
{"argv": [".venv/bin/python", "/home/ramin/kidsmap/docs/qa/offer-qa03-fix-2026-10-13-r1/drive.py", "admin-browser.js"], "native_cli_exit": 0, "result": "admin-browser.result.json"}
```

```json
{"argv": [".venv/bin/python", "/home/ramin/kidsmap/docs/qa/offer-qa03-fix-2026-10-13-r1/drive.py", "browser-resume.js"], "native_cli_exit": 0, "result": "browser-resume.result.json"}
```

```json
{"argv": [".tmp/offer-qa03-fix-2026-10-13-r1/venv/bin/python", "docs/qa/offer-qa03-fix-2026-10-13-r1/runtime.py", "script", "readback.py"], "exit": 1, "seconds": 1.21}
```

```json
{"argv": [".venv/bin/python", "/home/ramin/kidsmap/docs/qa/offer-qa03-fix-2026-10-13-r1/drive.py", "billing-keyboard.js"], "native_cli_exit": 0, "result": "billing-keyboard.result.json"}
```

```json
{"argv": [".tmp/offer-qa03-fix-2026-10-13-r1/venv/bin/python", "docs/qa/offer-qa03-fix-2026-10-13-r1/runtime.py", "script", "readback.py"], "exit": 0, "seconds": 11.071}
```

```json
{"argv": [".venv/bin/python", "/home/ramin/kidsmap/docs/qa/offer-qa03-fix-2026-10-13-r1/drive.py", "moderation.js"], "native_cli_exit": 0, "result": "moderation.result.json"}
```

```json
{"argv": [".tmp/offer-qa03-fix-2026-10-13-r1/venv/bin/python", "docs/qa/offer-qa03-fix-2026-10-13-r1/runtime.py", "script", "approved-readback.py"], "exit": 0, "seconds": 1.212}
```

```json
{"argv": ["node", "--check", "static/js/owner_place_continuous.js"], "exit": 0, "seconds": 0.082}
```

```json
{"argv": ["node", "--check", "static/js/permanent_place_photos.js"], "exit": 0, "seconds": 0.03}
```

```json
{"argv": [".tmp/offer-qa03-fix-2026-10-13-r1/venv/bin/python", "scripts/build_isolated_locales.py", "verify", "--manifest", ".tmp/offer-qa03-fix-2026-10-13-r1/locales/manifest.json"], "exit": 0, "seconds": 0.078}
```

