"""Export only bounded safe QA aggregates, never test payloads/log records."""
import json
from pathlib import Path
import sys

raw = Path(sys.argv[1])
out = Path(sys.argv[2])
result = {'evidence': str(raw), 'executor': '/root/stage26_security', 'production': 'NOT_CONTACTED'}
for filename, keys in [
    ('run.json', ['status', 'child_exit', 'cleanup', 'run_root_removed', 'socket_root_removed']),
    ('suite-results.json', ['tests_run', 'failures', 'errors', 'skipped', 'status', 'problems']),
    ('isolation.json', ['postgresql', 'django', 'python', 'psycopg', 'network_guard', 'libpq_guard', 'external_credentials_present']),
    ('migrations.json', ['applied_count', 'unapplied_count']),
]:
    if (raw / filename).is_file():
        data = json.loads((raw / filename).read_text())
        result[filename] = {key: data[key] for key in keys if key in data}
if (raw / 'checks.json').is_file():
    result['checks'] = json.loads((raw / 'checks.json').read_text())
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
