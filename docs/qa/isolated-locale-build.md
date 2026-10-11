# Isolated locale builds

Run `scripts/build_isolated_locales.py` with Python from the checkout. It compiles copied PO files with GNU msgfmt and writes a complete content-hash manifest only after every catalogue succeeds. The output must be a new directory under this checkout's `.tmp`; existing outputs, source overlap, symlinks and junctions are refused. Shared `locale/*/LC_MESSAGES/*.mo` files are never overwritten.

```powershell
.venv\Scripts\python.exe scripts/build_isolated_locales.py build --output .tmp/my-unique-qa-run/locales --locales ru az en --compiler wsl
.venv\Scripts\python.exe scripts/build_isolated_locales.py verify --manifest .tmp/my-unique-qa-run/locales/manifest.json
```

`--compiler native` uses GNU msgfmt on PATH; `--compiler wsl` uses WSL GNU msgfmt and `wslpath`. Compilation checks format strings, excludes fuzzy entries and produces deterministic little-endian MO files. No Django setup, credentials or database access is involved.

Before `django.setup()` or starting a QA server, call the helper's `verify(manifest_path, source_locale)` and require the intended locale set. Set the QA settings' sole `LOCALE_PATHS` entry to the returned `locale_root`. A missing, incomplete, stale or altered catalogue must stop startup. This is a caller-side gate; the builder does not alter global Django settings.

The executable example is `docs/qa/place-qa01-07-fix-2026-10-10/runtime.py`. Its startup checks, compiler commands and exit codes are recorded in that run's report. Use `DJANGO_TESTING=1` and a separate DB/cache/media/private-media/email setup as required by the audit contract.
