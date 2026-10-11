"""Own scoped evidence runner; no application or existing assertion changes."""
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
QA = HERE.parent
PYTHON = ROOT / '.venv/Scripts/python.exe'
NODE = Path('C:/Program Files/nodejs/node.exe')
LABELS = [
    'catalog.testcases.test_analytics_contract',
    'catalog.testcases.test_analytics_events_v2',
    'catalog.testcases.test_analytics_metrics',
    'catalog.testcases.test_favorite_metrics',
    'catalog.testcases.test_owner_analytics',
    'catalog.testcases.test_public_favorite_count',
    'catalog.testcases.test_analytics_commands',
    'catalog.testcases.tracking',
    'catalog.testcases.test_ai_referral_tracking',
]
ADMIN = ['catalog.testcases.admin.TestAdminOwnershipModerationUX.' + name for name in (
    'test_admin_site_analytics_page_shows_ga4_block',
    'test_admin_site_analytics_page_uses_new_dashboard_layout_and_period_fallback',
    'test_admin_site_analytics_page_shows_empty_ga_blocks_without_local_fallback',
    'test_admin_site_analytics_page_does_not_create_demo_places',
)]
jobs = {
    'primary': [str(PYTHON), str(QA / 'run.py'), 'test', *LABELS, *ADMIN],
    'ai-js': [str(NODE), 'static/js/tests/ai_referral_tracking.test.js'],
    'phone-dom': [str(NODE), '--test', '--test-reporter=tap', 'scripts/test_phone_reveal.cjs'],
    'supplement': [str(PYTHON), str(HERE / 'run-supplement.py')],
    'fault-confirmed': [str(PYTHON), str(HERE / 'run-supplement.py'), 'test_analytics_acceptance.FreshAnalyticsAcceptance.test_public_card_survives_simulated_analytics_backend_failure'],
    'private-origin': [str(PYTHON), str(HERE / 'run-supplement.py'), 'test_analytics_acceptance.FreshAnalyticsAcceptance.test_active_private_draft_id_cannot_accept_anonymous_contact_event', 'test_analytics_acceptance.FreshAnalyticsAcceptance.test_legitimate_same_origin_with_explicit_port_accepts_contact_event'],
}
job = sys.argv[1]
command = jobs[job]
start = time.perf_counter()
p = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
duration = time.perf_counter() - start
output = p.stdout + '\n' + p.stderr
secret_file = ROOT / '.tmp/module12-20261011-r1/credential'
if secret_file.exists():
    secret = secret_file.read_text().strip()
    if secret:
        output = output.replace(secret, '[REDACTED QA CREDENTIAL]')
output = re.sub(r'(visitor_key_hash|session_key_hash)([=:]\s*)[\w:.-]+', r'\1\2[REDACTED HASH]', output)
(HERE / (job + '.log')).write_text(output, encoding='utf-8')
record = {'job': job, 'command_argv': command, 'cwd': str(ROOT), 'date_utc': datetime.now(timezone.utc).isoformat(), 'exit_code': p.returncode, 'duration_seconds': round(duration, 3), 'log': job + '.log', 'scope': 'DJANGO_TESTING isolated module12 DB/cache/media/email; all external sockets blocked' if job in ('primary', 'supplement', 'fault-confirmed', 'private-origin') else 'Local Node; no network transport; DOM is SIMULATED and not rendered browser evidence'}
django = re.search(r'Ran (\d+) tests? in ([\d.]+)s', output)
if django:
    record['test_count'] = int(django[1])
    summary = re.search(r'FAILED \(([^)]*)\)', output)
    record['failures'] = int(re.search(r'failures=(\d+)', summary[1])[1]) if summary and re.search(r'failures=(\d+)', summary[1]) else 0
    record['errors'] = int(re.search(r'errors=(\d+)', summary[1])[1]) if summary and re.search(r'errors=(\d+)', summary[1]) else 0
    record['skipped'] = int(re.search(r'skipped=(\d+)', (summary[1] if summary else output))[1]) if re.search(r'skipped=(\d+)', (summary[1] if summary else output)) else 0
    record['passed'] = record['test_count'] - record['failures'] - record['errors'] - record['skipped']
elif job == 'phone-dom':
    for key in ('tests', 'pass', 'fail', 'skipped'):
        m = re.search(r'^# ' + key + r' (\d+)', output, re.M)
        if m:
            record[key] = int(m[1])
(HERE / (job + '.json')).write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record, indent=2))
print(output[-16000:])
sys.exit(p.returncode)
