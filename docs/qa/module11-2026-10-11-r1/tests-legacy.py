"""Repeat four unmodified legacy assertions on an isolated test DB.

Only the process-local QA feature flag differs. run.py is executed verbatim.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LABELS = [
    "catalog.testcases.public.PublicLanguageConsistencyTests.test_place_review_list_has_no_extra_framed_wrapper",
    "catalog.testcases.public.PublicLanguageConsistencyTests.test_public_pages_keep_system_text_in_url_language_across_requests",
    "catalog.testcases.public.TestPublicPagesSmoke.test_sitemap_includes_all_languages_and_hreflang_alternates",
    "catalog.testcases.public.PublicLanguageConsistencyTests.test_place_review_block_uses_the_page_language_for_all_system_copy",
]


def child():
    # Importing core.management does not load project settings. run.py performs
    # its own credential clearing, socket guard, setup and isolation assertions.
    sys.path[:0] = [str(HERE), str(ROOT / "src")]
    from django.core import management
    original = management.call_command

    def legacy_command(name, *args, **kwargs):
        from django.conf import settings
        assert settings.TESTING
        assert settings.DATABASES["default"]["PORT"] == "55442"
        if name == "test":
            assert settings.DATABASES["default"]["NAME"] == "module11"
            settings.LOCALIZED_PLACE_URLS_ENABLED = False
            print("QA process-local override: LOCALIZED_PLACE_URLS_ENABLED=False; disposable test_module11")
        else:
            # Django's test runner invokes migration/cache-table setup while
            # creating its disposable DB; these are not stand SEO commands.
            assert name in ("migrate", "createcachetable", "check"), name
            assert settings.DATABASES["default"]["NAME"] == "test_module11"
        return original(name, *args, **kwargs)

    management.call_command = legacy_command
    sys.argv = [str(HERE / "run.py"), "test", *LABELS]
    runpy.run_path(str(HERE / "run.py"), run_name="__main__")


def capture():
    spec = importlib.util.spec_from_file_location("module11_test_capture", HERE / "tests-run.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    attempt = next((arg for arg in sys.argv if re.fullmatch(r"--attempt\d{2}", arg)), "").replace("--", "-")
    log = HERE / ("tests-legacy" + attempt + ".log")
    command_file = HERE / ("tests-legacy" + attempt + "-command.json")
    assert not log.exists() and not command_file.exists(), "Preserve earlier evidence"
    before = helper.source_snapshot()
    env = dict(os.environ)
    env.update(PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    command = [str(ROOT / ".venv/Scripts/python.exe"), str(Path(__file__).resolve()), "--child"]
    started = datetime.now(timezone.utc).isoformat()
    begin = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="replace")
    seconds = time.monotonic() - begin
    after = helper.source_snapshot()
    clean = helper.sanitize(result.stdout)
    assert not re.search(r"csrfmiddlewaretoken.{0,150}?value.{0,10}?[A-Za-z0-9]{32,}", clean, re.I | re.S)
    log.write_text(clean, encoding="utf-8")
    ran = re.search(r"Ran (\d+) tests? in ([0-9.]+)s", clean)
    fail = re.findall(r"^FAIL: (test_\w+) \(([^)]+)\)", clean, re.M)
    err = re.findall(r"^ERROR: (test_\w+) \(([^)]+)\)", clean, re.M)
    info = {
        "mode": "AUDIT ONLY", "role": "integration-reviewer", "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(), "command_argv": command,
        "verbatim_launcher_argv": [str(HERE / "run.py"), "test", *LABELS],
        "effective_localized_place_urls_enabled": False, "exit_code": result.returncode,
        "wall_seconds": round(seconds, 3), "test_body_seconds": float(ran[2]) if ran else None,
        "executed_methods": int(ran[1]) if ran else None,
        "failure_entries_including_subtests": len(fail), "error_entries_including_subtests": len(err),
        "assertions_modified": False, "application_modified_by_runner": False,
        "db": "test_module11", "host": "127.0.0.1", "port": 55442,
        "before": {k:v for k,v in before.items() if k != "files"},
        "after": {k:v for k,v in after.items() if k != "files"},
        "source_changed": sorted(k for k in before["files"].keys() | after["files"].keys() if before["files"].get(k) != after["files"].get(k)),
        "evidence": log.name, "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
        "labels": LABELS, "scope": "Compatibility attribution only; full legacy suite NOT RUN",
    }
    command_file.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k:info[k] for k in ("exit_code", "wall_seconds", "executed_methods", "failure_entries_including_subtests", "error_entries_including_subtests", "source_changed")}))
    sys.exit(result.returncode)


if __name__ == "__main__":
    child() if "--child" in sys.argv else capture()
