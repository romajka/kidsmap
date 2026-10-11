"""Create a compact test-only handoff with exact source/HEAD verification."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
paths = [
    'src/catalog/services/analytics_metrics.py', 'src/catalog/services/analytics_quality.py',
    'src/catalog/services/tracking.py', 'src/catalog/services/analytics_identity.py',
    'src/catalog/services/visit_tracking.py', 'src/catalog/services/admin_analytics.py',
    'src/catalog/services/google_analytics_reporting.py',
    'src/catalog/controllers/owner_analytics_controller.py', 'src/catalog/controllers/place_controller.py',
    'src/catalog/domain_admin/site.py', 'src/catalog/repositories/tracking_repositories.py',
    'src/catalog/templates/pages/owner_analytics.html', 'templates/admin/catalog/site_analytics.html',
    'src/config/settings.py', 'src/config/test_runner.py',
    'src/catalog/views.py', 'src/catalog/controllers/tracking_controller.py',
    'src/catalog/testcases/test_analytics_contract.py', 'src/catalog/testcases/test_analytics_events_v2.py',
    'src/catalog/testcases/test_analytics_metrics.py', 'src/catalog/testcases/test_favorite_metrics.py',
    'src/catalog/testcases/test_owner_analytics.py', 'src/catalog/testcases/test_public_favorite_count.py',
    'src/catalog/testcases/test_analytics_commands.py', 'src/catalog/testcases/tracking.py',
    'src/catalog/testcases/test_ai_referral_tracking.py', 'src/catalog/testcases/admin.py',
    'static/js/tests/ai_referral_tracking.test.js', 'static/js/ai_referral_tracking.js',
    'scripts/test_phone_reveal.cjs', 'static/js/place_phone_reveal.js',
]
snapshot = json.loads((HERE.parent / 'snapshot.json').read_text(encoding='utf-8'))
verified = {}
for path in paths:
    result = subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', path], cwd=ROOT)
    verified[path] = {'sha256_worktree': hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
                      'git_diff_HEAD_exit': result.returncode, 'unchanged_HEAD': result.returncode == 0}
evidence = {'snapshot': {k: snapshot[k] for k in ('checkout', 'head', 'branch', 'active_run', 'source_digest')},
            'relevant_source': verified,
            'memory': {'project': 'C-kidsmap', 'status': 'ready', 'generation': '2026-10-11T10:18:23Z',
                       'coverage': 'metadata_changed/coverage_unavailable for cited files; direct source verified',
                       'scope_gaps': ['src/catalog/testcases/__pycache__ excluded', 'static/js/tests coverage unavailable'],
                       'graph_exported': False},
            'application_changes_by_agent': False,
            'existing_assertion_changes': False,
            'external_GA': 'NOT RUN'}
(HERE / 'source-snapshot.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
print(json.dumps({'files': len(paths), 'all_unchanged_HEAD': all(x['unchanged_HEAD'] for x in verified.values()),
                  'head': snapshot['head'], 'active_run': snapshot['active_run']}))
