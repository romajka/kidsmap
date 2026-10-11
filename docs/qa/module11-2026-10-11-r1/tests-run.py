"""Run existing targeted tests only on the parent-owned module11 test stand.

No application/assertion patches. Raw child output stays in memory until sanitized.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

MODULE_LABELS = [
    "catalog.testcases.test_localized_place_urls",
    "catalog.testcases.test_localized_place_seo",
    "catalog.testcases.test_seo_indexability",
    "catalog.testcases.test_seo_landing_visibility",
    "catalog.testcases.test_judo_seo_landing",
    "catalog.testcases.test_task33_localization",
    "catalog.testcases.public.PublicLanguageConsistencyTests",
    "catalog.testcases.test_place_json_and_pricing_modes.PlaceSchemaOrgSeoTests",
]
SMOKE_METHODS = [
    "test_legacy_az_urls_redirect_to_default_language_without_prefix",
    "test_legacy_redirect_keeps_catalog_filter_but_drops_foreign_query",
    "test_public_pages_without_trailing_slash_redirect_to_canonical_url",
    "test_www_alias_redirects_permanently_to_canonical_origin",
    "test_legacy_azerbaijani_reviews_url_redirects_to_canonical_reviews_page",
    "test_canonical_host_redirect_does_not_capture_admin_subdomain",
    "test_public_urls_on_admin_host_redirect_to_public_origin",
    "test_public_seo_urls_ignore_request_host_when_origin_is_configured",
    "test_seo_landing_breadcrumbs_include_the_catalog_level",
    "test_catalog_page_renders_visible_breadcrumbs",
    "test_filtered_catalog_breadcrumbs_match_the_place_card_trail",
    "test_bare_place_segment_redirects_to_catalog",
    "test_robots_txt_disallows_private_sections",
    "test_sitemap_includes_all_languages_and_hreflang_alternates",
    "test_sitemap_and_robots_use_configured_public_origin",
    "test_sitemap_xml_is_valid_xml",
    "test_sitemap_excludes_place_new",
    "test_sitemap_excludes_draft_places",
    "test_sitemap_excludes_deleted_places",
    "test_sitemap_has_no_duplicate_urls",
    "test_sitemap_lastmod_matches_model_updated_at",
    "test_sitemap_does_not_contain_changefreq_or_priority",
    "test_seo_landing_uses_matching_language_content_and_hreflang",
]
QUERY_METHODS = [
    "test_place_detail_drops_foreign_next_query_parameter",
    "test_catalog_keeps_its_own_filter_query_and_detail_links_are_clean",
    "test_language_switch_preserves_catalog_filters_only",
]
LABELS = (MODULE_LABELS
    + ["catalog.testcases.public.TestPublicPagesSmoke." + x for x in SMOKE_METHODS]
    + ["catalog.testcases.public.TestCatalogEnhancements." + x for x in QUERY_METHODS])


def sanitize(value):
    value = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", value)
    # Django assertion HTML and traceback representations can contain either
    # literal HTML quotes or escaped quotes. All masked CSRF tokens are removed.
    value = re.sub(r"(?is)(csrfmiddlewaretoken.{0,150}?value.{0,10}?)[A-Za-z0-9]{32,}", r"\1[REDACTED]", value)
    value = re.sub(r"(?i)((?:csrftoken|sessionid|module11_r1_(?:csrf|session))\s*[=:]\s*[\"']?)[A-Za-z0-9]{16,}", r"\1[REDACTED]", value)
    value = re.sub(r"(?i)((?:password|secret|access_token|refresh_token|authorization)\s*[=:]\s*[\"']?)[^\s,\"'<>]{3,}", r"\1[REDACTED]", value)
    value = re.sub(r"(?i)(Bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[REDACTED]", value)
    credential = ROOT / ".tmp/module11-20261011-r1/credential"
    if credential.exists():
        secret = credential.read_text(encoding="utf-8").strip()
        if secret:
            value = value.replace(secret, "[REDACTED]")
    return value


def source_snapshot():
    files = {}
    for top in ("src", "static", "config", "locale", "templates"):
        for path in (ROOT / top).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                files[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
        "files": files,
        "source_count": len(files),
        "source_digest": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
    }


def inventory():
    result = []
    for label in LABELS:
        parts = label.split(".")
        module = ".".join(parts[:3])
        path = ROOT / "src" / Path(*module.split(".")).with_suffix(".py")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        selected_class = parts[3] if len(parts) > 3 else None
        selected_method = parts[4] if len(parts) > 4 else None
        methods = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and (selected_class is None or node.name == selected_class):
                for method in node.body:
                    if isinstance(method, ast.FunctionDef) and method.name.startswith("test_") and (selected_method is None or selected_method == method.name):
                        methods.append(module + "." + node.name + "." + method.name)
        assert methods, label
        result.append({"label": label, "source": path.relative_to(ROOT).as_posix(), "methods": methods})
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ready", action="store_true", help="Parent has attested isolated DB and launcher readiness")
    parser.add_argument("--attempt", default="", help="Optional owned attempt filename suffix")
    args = parser.parse_args()
    inv = inventory()
    command = [str(ROOT / ".venv/Scripts/python.exe"), str(HERE / "run.py"), "test", *LABELS, "--verbosity=2"]
    if not args.ready:
        print(json.dumps({"status": "NOT RUN waiting parent ready", "labels": LABELS, "methods": sum(len(x["methods"]) for x in inv), "command": command}))
        return
    assert re.fullmatch(r"[A-Za-z0-9_-]*", args.attempt)
    suffix = "" if not args.attempt else "-attempt-" + args.attempt
    log_path = HERE / ("tests" + suffix + ".log")
    metadata_path = HERE / ("tests-command" + suffix + ".json")
    assert not log_path.exists() and not metadata_path.exists(), "Preserve existing test evidence"
    before = source_snapshot()
    started = datetime.now(timezone.utc).isoformat()
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    begin = time.monotonic()
    child = subprocess.run(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="replace")
    seconds = time.monotonic() - begin
    after = source_snapshot()
    clean = sanitize(child.stdout)
    # Fail closed if a masked/unmasked token remains in captured form HTML.
    assert not re.search(r"csrfmiddlewaretoken.{0,150}?value.{0,10}?[A-Za-z0-9]{32,}", clean, re.I | re.S)
    log_path.write_text(clean, encoding="utf-8")
    ran = re.search(r"Ran (\d+) tests? in ([0-9.]+)s", clean)
    failed_headers = re.findall(r"^FAIL: (test_\w+) \(([^)]+)\)", clean, re.M)
    error_headers = re.findall(r"^ERROR: (test_\w+) \(([^)]+)\)", clean, re.M)
    failed_methods = sorted(set(cls if cls.endswith("." + method) else cls + "." + method for method, cls in failed_headers))
    error_methods = sorted(set(cls if cls.endswith("." + method) else cls + "." + method for method, cls in error_headers))
    skipped = len(re.findall(r"\.\.\. skipped", clean))
    expected = sum(len(x["methods"]) for x in inv)
    count = int(ran[1]) if ran else None
    info = {
        "mode": "AUDIT ONLY", "role": "integration-reviewer", "checkout": str(ROOT),
        "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
        "command_argv": command, "exit_code": child.returncode, "wall_seconds": round(seconds, 3),
        "test_body_seconds": float(ran[2]) if ran else None, "expected_discovered_methods": expected,
        "executed_methods": count, "passed_methods": (count - len(set(failed_methods + error_methods)) - skipped) if count is not None else None,
        "failed_methods": failed_methods, "errored_methods": error_methods,
        "failure_entries_including_subtests": len(failed_headers), "error_entries_including_subtests": len(error_headers), "skipped_methods": skipped,
        "label_inventory": inv, "before": {k:v for k,v in before.items() if k != "files"},
        "after": {k:v for k,v in after.items() if k != "files"},
        "source_changed": sorted(k for k in before["files"].keys() | after["files"].keys() if before["files"].get(k) != after["files"].get(k)),
        "db": "test_module11", "host": "127.0.0.1", "port": 55442,
        "external": "BLOCKED socket guard; IndexNow enqueue mocked by existing tests",
        "evidence": log_path.name, "log_sha256": hashlib.sha256(log_path.read_bytes()).hexdigest(),
        "not_run": ["SEO audit/fix management commands", "real IndexNow/Search Console", "production", "full suite", "rendered browser (owned by parent)"]
    }
    metadata_path.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k:info[k] for k in ("exit_code", "wall_seconds", "executed_methods", "passed_methods", "failed_methods", "errored_methods", "skipped_methods", "source_changed")}))
    sys.exit(child.returncode)


if __name__ == "__main__":
    main()
