"""Extract synthetic matrix JSON from Playwright CLI output."""
import json
import sys
from pathlib import Path
root = Path(sys.argv[1])
raw = (root / 'matrix-cli.txt').read_text()
start = raw.find('{', raw.find('### Result'))
if start < 0:
    raise RuntimeError('Browser matrix result missing; inspect CLI output')
result, _ = json.JSONDecoder().raw_decode(raw[start:])
(root / 'matrix.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
if 'total' in result:
    summary = {key: result[key] for key in ('passed', 'total', 'legacy', 'keyboard', 'events')}
    summary['failures'] = [{key: row[key] for key in ('width', 'lang', 'kind', 'issues')} for row in result['rows'] if row['issues']]
else:
    failures = []
    for row in result['rows']:
        canonical_row = next(x for x in result['rows'] if x['kind'] == row['kind'] and x['lang'] == (row['lang'] if row['kind'] == 'complete' else 'az'))
        if row['status'] != 200 or row['canonical'] != canonical_row['canonical']:
            failures.append({'lang': row['lang'], 'kind': row['kind'], 'issue': 'head'})
    desktop = result['desktop']; mobile = result['mobile']
    if desktop['expanded'] != 'true' or desktop['firstLink'] != 'az' or desktop['secondLink'] != 'ru' or desktop['shellLanguage'] != 'ru':
        failures.append({'issue': 'desktop_keyboard'})
    if mobile['open'] != 'false' or mobile['shellLanguage'] != 'ru':
        failures.append({'issue': 'mobile_keyboard'})
    summary = {'total': len(result['rows']), 'desktop': desktop, 'mobile': mobile, 'failures': failures}
(root / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
print(json.dumps(summary, ensure_ascii=False))
