"""Read-only structural evidence; does not import Django or access a database."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
PATHS = [
    "src/catalog/services/tracking.py",
    "src/catalog/services/visit_tracking.py",
    "src/catalog/services/analytics_identity.py",
    "src/catalog/services/analytics_metrics.py",
    "src/catalog/services/favorite_metrics.py",
    "src/catalog/services/admin_analytics.py",
    "src/catalog/services/google_analytics_reporting.py",
    "src/catalog/controllers/tracking_controller.py",
    "src/catalog/controllers/owner_analytics_controller.py",
    "src/catalog/repositories/tracking_repositories.py",
    "src/catalog/models/site.py",
    "src/catalog/models/analytics.py",
    "src/catalog/checks.py",
    "src/catalog/domain_admin/site.py",
    "src/catalog/templates/pages/owner_analytics.html",
    "src/catalog/templates/base.html",
    "templates/admin/catalog/site_analytics.html",
    "static/js/ai_referral_tracking.js",
]
files = []
for relative in PATHS:
    raw = (ROOT / relative).read_bytes()
    row = {"path": relative, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    if relative.endswith(".py"):
        tree = ast.parse(raw.decode("utf-8-sig"))
        row["definitions"] = [
            {"symbol": node.name, "line": node.lineno}
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.ClassDef))
            and node.name in {
                "track_event", "track_subject_view", "track_request", "_ga_period_key",
                "build_statistics_context", "build_snapshot", "build_subject_metrics", "_base_events",
                "_period_values", "analytics_identity_for_request", "classify_device", "build_context",
                "find_active_for_event", "increment_or_create_hit", "track_event_from_json", "SiteVisit",
                "FunnelEvent", "SiteAnalyticsAdmin", "AnalyticsActorExclusion", "AnalyticsIngressDaily",
            }
        ]
    files.append(row)
git = lambda *args: subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
evidence = {
    "mode": "AUDIT ONLY / source only",
    "head": git("rev-parse", "HEAD"),
    "branch": git("branch", "--show-current"),
    "files": files,
    "scoped_dirty_paths": git("diff", "--name-only", "--", *PATHS).splitlines(),
    "tests_executed": 0,
    "runtime_checks_executed": 0,
    "external_integrations": "NOT RUN",
}
(OUT / "source-checks.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"files_checked": len(files), "dirty_scoped_files": len(evidence["scoped_dirty_paths"]), "python_ast": "PASS", "runtime": "NOT RUN"}))
