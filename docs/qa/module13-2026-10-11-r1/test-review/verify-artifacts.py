"""Read-only final evidence and source preservation verification."""
import ast
import collections
import datetime
import hashlib
import json
import pathlib
import re
import subprocess

P = pathlib.Path(__file__).resolve().parent
ROOT = P.parents[3]
QA = P.parent
load = lambda name: json.loads((P / name).read_text(encoding="utf-8"))
checks = {}

py_files = sorted(P.glob("*.py"))
for path in py_files:
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
checks["qa_python_ast"] = {"files": len(py_files), "PASS": True}
json_files = sorted(P.glob("*.json"))
for path in json_files:
    json.loads(path.read_text(encoding="utf-8"))
jsonl_files = sorted(P.glob("*.jsonl"))
jsonl_rows = 0
for path in jsonl_files:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            json.loads(line)
            jsonl_rows += 1
checks["evidence_json_parse"] = {"files": len(json_files), "jsonl_files": len(jsonl_files), "jsonl_rows": jsonl_rows, "PASS": True}

c = load("counts.json")
results = load("results.json")
rows = results["normalized_methods"]
inventory = load("full-inventory.json")
assert len(rows) == len({r["id"] for r in rows}) == len(inventory["ids"]) == 2090
assert set(r["id"] for r in rows) == set(inventory["ids"])
assert dict(collections.Counter(r["status"] for r in rows)) == c["django_normalized"] == {"PASS": 2036, "FAIL": 11, "NOT RUN": 43}
assert dict(collections.Counter(r["classification"] for r in rows)) == c["django_classifications"]
assert results["counts"] == c
full = load("full-results.json")
target = load("target-results.json")
frozen = load("baseline-results.json")
compiled = load("baseline-compiled-results.json")
assert full["exit_code"] == 1 and target["exit_code"] == 0
assert frozen["exit_code"] == compiled["exit_code"] == 1
assert full["deduplicated_identical_ids"] == 0
assert collections.Counter(r["status"] for r in full["method_observations"]) == full["statuses"]
assert sum(len(x) for x in (full["method_observations"], target["method_observations"], frozen["records"], compiled["records"])) == c["raw_observation_rows_all_django_profiles"] == 2223
assert c["django_method_slots_all_profiles"] == 2090 + 2 + 11 + 11 == 2114
assert c["fresh_gnu_head_baseline"]["browser_runtime_changed"] is False
checks["normalized_and_raw_counts"] = {"unique_methods": 2090, "method_slots": 2114, "raw_observation_rows": 2223, "normalized": c["django_normalized"], "PASS": True}

js = load("js-results.json")
assert len(js["results"]) == 20 and all(r["exit_code"] == 0 and r["status"] == "PASS" for r in js["results"])
assert js["aggregate_node_counts"]["tests"] == js["aggregate_node_counts"]["pass"] == 117
assert len(js["browser_scripts"]) == 3
standalone = load("standalone-results.json")
backup = load("wsl-backup-results.json")
assert standalone["counts"] == {"PASS": 13, "ERROR": 3}
assert backup["exit_code"] == 0 and len(backup["records"]) == 3 and all(r["status"] == "PASS" for r in backup["records"])
checks["js_standalone_counts"] = {"scripts": 20, "node_entries": 117, "named_tests": 115, "bare_wrappers": 2, "standalone_windows": standalone["counts"], "backup_posix_replay": 3, "PASS": True}

manage = load("manage-discovery.json")
head = load("head-discovery.json")
qual = load("discovery-corpus-qualification.json")
assert manage["count"] == 618 and manage["tests_executed"] == 0 and manage["database_created"] is False
assert head["head_no_label_count"] == 618 and head["head_explicit_full_count"] == 2070
assert head["head_ci_missing_count"] == 1452 and head["head_wrapper_missing_count"] == 140
assert qual["local_worktree_ci_missing"] == 1472 == qual["local_missing_from_tracked_tests"] + qual["local_missing_from_untracked_tests"]
assert qual["local_missing_from_tracked_tests"] == 1452 and qual["local_missing_from_untracked_tests"] == 20
checks["discovery_qualification"] = {"head_missing_tracked": 1452, "worktree_missing": 1472, "worktree_foreign_untracked": 20, "wrapper_missing": 140, "actual_github_execution": "NOT RUN", "PASS": True}

report = (P / "REPORT.md").read_text(encoding="utf-8")
links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", report)
missing = []
for link in links:
    if not link.startswith(("https://", "http://", "#")):
        path = (P / link.split("#", 1)[0]).resolve()
        if not path.is_file():
            missing.append(link)
assert not missing
assert len(re.findall(r"^## [1-9]\. ", report, flags=re.M)) == 9
checks["report_links_and_sections"] = {"local_links": len(links), "missing_links": missing, "sections": 9, "PASS": True}

snapshot = json.loads((QA / "snapshot.json").read_text(encoding="utf-8"))
current = {rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() for rel in snapshot["source_files"]}
assert current == snapshot["source_files"]
digest = hashlib.sha256(json.dumps(current, sort_keys=True).encode()).hexdigest()
assert digest == c["snapshot"]["source_digest"] == full["source_digest"]
head_now = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
branch_now = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
active_now = next(x.split(":", 1)[1].strip() for x in (ROOT / "docs/task33/implementation-status.md").read_text(encoding="utf-8").splitlines() if x.startswith("active_run:"))
assert head_now == c["snapshot"]["head"] and branch_now == c["snapshot"]["branch"] and active_now == c["snapshot"]["active_run"]
checks["application_and_assertion_source_preserved"] = {"files": len(current), "source_digest": digest, "head": head_now, "branch": branch_now, "active_run": active_now, "PASS": True}

credential = (ROOT / ".tmp/module13-20261011-r1/credential").read_bytes().strip()
assert len(credential) > 10
credential_hits = [path.name for path in P.iterdir() if path.is_file() and credential in path.read_bytes()]
assert not credential_hits
csrf_pattern = re.compile(rb"name=[\"']csrfmiddlewaretoken[\"'][^>]*value=[\"']([A-Za-z0-9]{64})[\"']")
csrf_hits = [path.name for path in P.iterdir() if path.is_file() and csrf_pattern.search(path.read_bytes())]
assert not csrf_hits
checks["evidence_privacy"] = {"exact_isolated_credential_hits": 0, "raw_html_csrf_token_hits": 0, "redaction_record": "redaction.json", "scope": "Own evidence only; no production credentials used", "PASS": True}

diff = subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True, text=True)
assert diff.returncode == 0, "git diff --check failed; inspect own/foreign provenance before changes"
checks["git_diff_check"] = {"command": "git diff --check", "exit_code": diff.returncode, "PASS": True}

verification = {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "command": ".venv/Scripts/python.exe -X utf8 docs/qa/module13-2026-10-11-r1/test-review/verify-artifacts.py", "exit_code": 0, "checks": checks, "limits": ["Verification confirms evidence integrity, not overall application acceptance", "Nine GNU control passes do not change original runtime FAIL", "Actual GitHub CI and real external integrations NOT RUN", "No new tests, application, rules, migrations or assertions edited by this role"]}
(P / "verification.json").write_text(json.dumps(verification, indent=2), encoding="utf-8")
print(json.dumps({"exit_code": 0, "checks": len(checks), "source_files_preserved": len(current), "normalized": c["django_normalized"], "report": str(P / "REPORT.md"), "verification": str(P / "verification.json")}, indent=2))
