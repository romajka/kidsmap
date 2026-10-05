"""Current hashes against immutable executed freeze, with reviewed CSS delta attribution."""
import hashlib
import json
from pathlib import Path
import sys

root = Path('/mnt/c/kidsmap')
original = json.loads((root/'docs/task33/reports/27-integration-source.json').read_text())
css = 'static/css/events_landing.css'
expected_css = 'ab2a88df60d30d18c709d2878836b32415fbd6316f076436d7fcb54e2b042ae0'
template = 'src/catalog/templates/catalog/events_landing.html'
expected_template = 'e1ede6c4044f62273d7537965c52a19ce799dc339880d3862ae965f87b06522f'
files = []
for old in original['source_files']:
    path = old['path']
    current_sha = hashlib.sha256((root/path).read_bytes()).hexdigest()
    unchanged = current_sha == old['frozen_sha256']
    reviewed = ((path == css and current_sha == expected_css)
                or (path == template and current_sha == expected_template))
    files.append({'path':path, 'current_sha256':current_sha,
                  'executed_frozen_sha256':old['frozen_sha256'], 'unchanged':unchanged,
                  'late_source_only_review':reviewed,
                  'reviewed_delta': 'hero-stat CSS wrapping' if path == css else ('landing native navigation motion override' if path == template else None),
                  'covered_by_runtime_or_review':unchanged or reviewed})
assert sum(not item['unchanged'] for item in files) == 2
assert all(item['covered_by_runtime_or_review'] for item in files)
result = {'head':original['head'], 'executor':'/root/stage27_integration',
          'runtime':'10/10 PASS on original freeze; late CSS/template source-only reviews, no runtime repeat',
          'source_files':files, 'unchanged_count':sum(f['unchanged'] for f in files),
          'late_reviewed_count':sum(f['late_source_only_review'] for f in files),
          'current_coverage_count':len(files), 'production':'NOT_CONTACTED'}
Path(sys.argv[1]).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({key:result[key] for key in ('unchanged_count','late_reviewed_count','current_coverage_count')}))
