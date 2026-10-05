"""Write a compact, synthetic design QA aggregate; raw browser records stay outside Git."""
from pathlib import Path
import hashlib
import json
import sys

evidence = Path('/root/task33-evidence')
names = ['first', 'final', 'pending-red', 'final2', 'final-copy']
runs = {}
for name in names:
    root = evidence / f'stage25-design-{name}-20261003'
    result = json.loads((root / 'results.json').read_text())
    checks = result['checks']
    runs[name] = {
        'evidence': str(root),
        'rows': result['total'], 'passed_rows': result['passed'],
        'checks': len(checks), 'passed_checks': result['checksPassed'],
        'event_counts': {k: len(v) for k, v in result['events'].items()},
        'failed_checks': [c for c in checks if not c['pass']],
        'failed_rows': [{k: r[k] for k in ('file', 'lang', 'width', 'issues')} for r in result['rows'] if r['issues']],
        'screenshots': sorted(p.name for p in root.glob('*.png')),
        'executed_matrix_sha256': hashlib.sha256((root / 'matrix.js').read_bytes()).hexdigest(),
        'prototype_source_snapshot': json.loads((root / 'source-snapshot.json').read_text()),
    }
design = Path('/mnt/c/kidsmap/docs/task33/design/specialist')
fresh = runs['final-copy']['prototype_source_snapshot']
mismatches = [r['path'] for r in fresh if hashlib.sha256((design / r['path']).read_bytes()).hexdigest() != r['sha256']]
data = {
    'stage': 25, 'scope': 'DESIGN_ONLY', 'design_status': 'REVIEW_PENDING',
    'reviewer': '/root/stage25_browser', 'role': 'browser-qa',
    'head': '015d031d8eb17114bd860159dde805b38df3c13c', 'branch': 'task33-progress',
    'browser': 'Chromium 1247 via cached Playwright CLI 0.1.22',
    'server': 'allowlisted loopback static HTTP on 127.0.0.1:8795; no Django/DB/external assets',
    'widths': [320, 360, 390, 768, 1024, 1280, 1440], 'languages': ['az', 'ru', 'en'],
    'runs': runs, 'final_source_checked': len(fresh), 'final_source_mismatches': mismatches,
    'full_matrix_state_variants': 192, 'full_matrix_flow_assertions': 216,
    'classifications': {
        'first': 'Preliminary render-only matrix on initial prototype source.',
        'final': 'Two RU→EN harness readiness races before deferred JS; corrected navigation wait, no product code change for these two.',
        'pending-red': 'Three actual design defects: pending qualification exposed certificate action. Fixed by prototype author; final2 and final-copy independently verify exclusion.',
        'final2': 'Complete matrix plus state/flow checks on frozen ae981f... source.',
        'final-copy': 'Fresh final source 63fb1d... after bounded copy-only reconciliation/role translations; all eight screens plus denied states and actual keyboard navigation.',
    },
    'not_run': ['Application UI integration', 'Real backend nested-ID/ACL/claim concurrency', 'Django checks/migrations or PostgreSQL tests for stage25 design', 'Real fixture migration/reconciliation', 'Real upload/storage/download', 'Production', 'User design acceptance', 'Screen-reader full audit', 'Native file chooser browser/OS localization'],
    'cleanup': 'Each runner closes only qa25 session and its owned static server; root review server 8796 untouched.',
}
Path(sys.argv[1]).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'final_rows': runs['final-copy']['rows'], 'final_passed': runs['final-copy']['passed_rows'], 'final_checks': runs['final-copy']['checks'], 'final_checks_passed': runs['final-copy']['passed_checks'], 'final_sources': len(fresh), 'mismatches': len(mismatches)}))
if mismatches:
    raise SystemExit(1)
