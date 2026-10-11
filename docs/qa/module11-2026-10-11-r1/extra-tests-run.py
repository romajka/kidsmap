"""Additional four existing module11 suites; no assertion/application changes."""
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LABELS = [
    "catalog.testcases.test_json_ld_serialization",
    "catalog.testcases.test_task33_event_schema",
    "catalog.testcases.test_task33_public_details",
    "catalog.testcases.test_organization_directory",
]


def main():
    spec = importlib.util.spec_from_file_location("module11_existing_capture", HERE / "tests-run.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    selected_labels = ["catalog.testcases.test_task33_event_public"] if "--event-public" in sys.argv else LABELS
    inventory = []
    for label in selected_labels:
        source = ROOT / "src" / Path(*label.split(".")).with_suffix(".py")
        tree = ast.parse(source.read_text(encoding="utf-8"))
        methods = [label + "." + c.name + "." + m.name
                   for c in tree.body if isinstance(c, ast.ClassDef)
                   for m in c.body if isinstance(m, ast.FunctionDef) and m.name.startswith("test_")]
        inventory.append({"label": label, "source": source.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "methods": methods})
    command = [str(ROOT / ".venv/Scripts/python.exe"), str(HERE / "run.py"), "test", *selected_labels]
    if "--ready" not in sys.argv:
        print(json.dumps({"status": "NOT RUN", "expected_methods": sum(len(x["methods"]) for x in inventory), "command_argv": command}))
        return
    prefix = "extra-tests-event-public" if "--event-public" in sys.argv else "extra-tests"
    log = HERE / (prefix + ".log")
    metadata = HERE / (prefix + "-command.json")
    assert not log.exists() and not metadata.exists(), "Preserve existing evidence"
    before = helper.source_snapshot()
    env = dict(os.environ)
    env.update(PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    started = datetime.now(timezone.utc).isoformat()
    begin = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="replace")
    elapsed = time.monotonic() - begin
    after = helper.source_snapshot()
    clean = helper.sanitize(result.stdout)
    assert not re.search(r"csrfmiddlewaretoken.{0,150}?value.{0,10}?[A-Za-z0-9]{32,}", clean, re.I | re.S)
    log.write_text(clean, encoding="utf-8")
    ran = re.search(r"Ran (\d+) tests? in ([0-9.]+)s", clean)
    failed_entries = re.findall(r"^FAIL: (test_\w+) \(([^)]+)\)", clean, re.M)
    error_entries = re.findall(r"^ERROR: (test_\w+) \(([^)]+)\)", clean, re.M)
    failures = sorted(set(c if c.endswith("."+m) else c+"."+m for m,c in failed_entries))
    errors = sorted(set(c if c.endswith("."+m) else c+"."+m for m,c in error_entries))
    skipped = len(re.findall(r"\.\.\. skipped", clean))
    count = int(ran[1]) if ran else None
    info = {
        "mode": "AUDIT ONLY", "role": "integration-reviewer", "started_utc": started,
        "finished_utc": datetime.now(timezone.utc).isoformat(), "command_argv": command,
        "exit_code": result.returncode, "wall_seconds": round(elapsed,3),
        "test_body_seconds": float(ran[2]) if ran else None,
        "expected_discovered_methods": sum(len(x["methods"]) for x in inventory),
        "executed_methods": count,
        "passed_methods": count-len(set(failures+errors))-skipped if count is not None else None,
        "failed_methods": failures, "errored_methods": errors, "skipped_methods": skipped,
        "failure_entries_including_subtests": len(failed_entries), "error_entries_including_subtests": len(error_entries),
        "before": {k:v for k,v in before.items() if k!="files"}, "after": {k:v for k,v in after.items() if k!="files"},
        "source_changed": sorted(k for k in before["files"].keys()|after["files"].keys() if before["files"].get(k)!=after["files"].get(k)),
        "label_inventory": inventory, "evidence": log.name,
        "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
        "db": "test_module11", "host": "127.0.0.1", "port": 55442,
        "effective_localized_place_urls_enabled": True,
        "external_integrations": "BLOCKED socket guard, no credentials; Django TestClient only",
        "assertions_modified": False, "application_modified_by_runner": False,
        "known_environment_gap": "Event schema suites hardcode Linux /tmp QA root, test_qa_stage04 name and Unix socket; guards are unchanged" if "catalog.testcases.test_task33_event_schema" in selected_labels else None,
        "not_run": ["Production", "SEO audit/apply/fix commands", "External integration APIs", "Full suite", "Rendered browser (parent ownership)"]
    }
    metadata.write_text(json.dumps(info,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({k:info[k] for k in ("exit_code","wall_seconds","executed_methods","passed_methods","failed_methods","errored_methods","skipped_methods","source_changed")}))
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
