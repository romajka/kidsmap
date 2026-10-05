"""Retain bounded synthetic suite evidence, without logs, environment or records."""
import json
import sys
from pathlib import Path

source = Path(sys.argv[1])
destination = Path(sys.argv[2])
result = {'run': 'completion-20261004-095717Z', 'scope': sys.argv[3] if len(sys.argv)>3 else 'approved completion point4 notifications', 'evidence': str(source)}
for name, keys in [
    ('suite-results.json', ['tests_run', 'failures', 'errors', 'skipped', 'elapsed_seconds', 'status', 'executed_ids', 'problems']),
    ('migrations.json', ['applied_count', 'unapplied_count']),
    ('discovery.json', ['explicit_count', 'explicit_unique_count', 'duplicate_explicit_ids']),
    ('isolation.json', ['postgresql', 'django', 'python', 'psycopg', 'network_guard', 'libpq_guard', 'external_credentials_present']),
    ('run.json', ['status', 'child_exit', 'cleanup', 'run_root_removed', 'socket_root_removed']),
]:
    if not (source / name).exists():
        continue
    data = json.loads((source / name).read_text())
    result[name] = {key: data[key] for key in keys if key in data}
if (source / 'checks.json').exists():
    result['checks.json'] = json.loads((source / 'checks.json').read_text())
destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
suite=result.get('suite-results.json', {})
print(json.dumps({key: suite[key] for key in ['tests_run','failures','errors','skipped','status'] if key in suite}))

