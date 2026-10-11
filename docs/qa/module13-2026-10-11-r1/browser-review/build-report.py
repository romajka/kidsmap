import collections
import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
ROLE_ORDER = ['guest', 'owner', 'admin']
raw_files = [HERE / f'matrix-{role}-{lang}.result.json' for role in ROLE_ORDER for lang in ['ru', 'az', 'en']]
raw_files += [HERE / 'auth-recheck.result.json', HERE / 'supplement.result.json', HERE / 'locale-check.result.json', HERE / 'locale-visible.result.json']
rows, observations, declared_screens, attests, sources, excluded = [], [], [], [], [], []
for path in raw_files:
    if not path.exists():
        continue
    data = json.loads(path.read_text(encoding='utf-8'))
    sources.append(path.name)
    attests.append(data.get('attestation', {}))
    observations.extend(data.get('observations', []))
    declared_screens.extend(data.get('screens', []))
    for row in data.get('rows', []):
        row = dict(row, evidence_result=path.name)
        if row.get('scenario') == 'owner-district-placeholder-language':
            row['canonical_id'] = 'CROSS-QA-03'
            row['id_assignment'] = 'Assigned by kidsmap-orchestrator after raw capture; raw evidence preserved.'
        if row.get('scenario') == 'anonymous-favorite-auth-dialog':
            excluded.append(dict(row, reason='Incorrect QA oracle: native UI intentionally shows role=status toast, not dialog. Fresh auth-recheck replaces this assertion.'))
            continue
        rows.append(row)
for o in observations:
    k = o['keyboard']['first']
    outline_width = re.findall(r'(\d+(?:\.\d+)?)px', k.get('outline', ''))
    proved = (outline_width and float(outline_width[-1]) > 0) or k.get('shadow', 'none') != 'none'
    rows.append({'scenario': o['surface'] + '-computed-visible-focus', 'status': 'PASS' if proved else 'NOT RUN', 'role': o['role'], 'lang': o['lang'], 'width': o['width'], 'url': o['url'], 'utc': o['utc'], 'detail': 'First Tab target visible; nonzero computed outline or shadow' if proved else 'Other focus indicators require visual comparison; not inferred from outline/shadow alone.', 'keyboard': k})
    n = o['network']
    local_bad = [r for r in n['responses'] if r['url'].startswith('http://localhost:8831/')]
    guarded = {r['url'] for r in n['writeGuard']}
    local_console = [r for r in n['console'] if r['type'] == 'error' and r.get('url', '').startswith('http://localhost:8831/') and not any(path in r['url'] for path in guarded)]
    local_failed = [r for r in n['failed'] if r['url'].startswith('http://localhost:8831/') and not any(path in r['url'] for path in guarded) and r.get('error') != 'net::ERR_ABORTED']
    rows.append({'scenario': o['surface'] + '-local-console-network', 'status': 'PASS' if not n['pageerrors'] and not local_bad and not local_console and not local_failed else 'FAIL', 'role': o['role'], 'lang': o['lang'], 'width': o['width'], 'url': o['url'], 'utc': o['utc'], 'pageerrors': n['pageerrors'], 'local_bad_responses': local_bad, 'local_console_errors': local_console, 'local_failed_requests': local_failed, 'externalBlocked': n['externalBlocked'], 'writeGuard': n['writeGuard'], 'console': n['console']})
(HERE / 'matrix.json').write_text(json.dumps({'rows': rows, 'excluded_invalid_oracles': excluded, 'sources': sources}, ensure_ascii=False, indent=2), encoding='utf-8')
with (HERE / 'matrix.csv').open('w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['scenario', 'status', 'role', 'lang', 'width', 'url', 'utc', 'screenshot', 'evidence_result'], extrasaction='ignore')
    w.writeheader()
    w.writerows(rows)
(HERE / 'observations.json').write_text(json.dumps(observations, ensure_ascii=False, indent=2), encoding='utf-8')
declared = {s['file']: s for s in declared_screens}
manifest = []
for p in sorted((HERE / 'screenshots').glob('*.png')):
    with Image.open(p) as im:
        width, height = im.size
        im.verify()
    rel = p.relative_to(HERE).as_posix()
    manifest.append({'file': rel, 'pixel_width': width, 'pixel_height': height, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'declared_complete_run': rel in declared, 'note': 'Completed native rendered capture' if rel in declared else 'Initial probe or unfinished first attempt; not used as completed matrix assertion', **declared.get(rel, {})})
(HERE / 'screenshot-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
contacts = []
for role in ROLE_ORDER:
    surfaces = {'guest': ['place', 'organization', 'activity', 'specialist', 'event-physical', 'event-online', 'catalog-empty'], 'owner': ['place-edit', 'organization-edit', 'program-edit'], 'admin': ['place-admin', 'event-admin']}[role]
    for surface in surfaces:
        selected = [HERE / f'screenshots/native-r2-{role}-{lang}-{width}-{surface}.png' for lang in ['ru', 'az', 'en'] for width in [390, 1440]]
        selected = [p for p in selected if p.exists()]
        if not selected:
            continue
        cell_w, cell_h = 430, 620
        canvas = Image.new('RGB', (cell_w * 3, cell_h * 2), '#e8eee8')
        draw = ImageDraw.Draw(canvas)
        for i, p in enumerate(selected):
            with Image.open(p) as im:
                im = im.convert('RGB')
                im = im.crop((0, 0, im.width, min(im.height, 1100)))
                im.thumbnail((cell_w - 14, cell_h - 45))
                x, y = (i // 2) * cell_w + 7, (i % 2) * cell_h + 35
                canvas.paste(im, (x, y))
            draw.text(((i // 2) * cell_w + 7, (i % 2) * cell_h + 9), p.name.replace('native-r2-', ''), fill='black')
        filename = f'contact-{role}-{surface}.png'
        canvas.save(HERE / filename)
        contacts.append({'file': filename, 'derived_from': [p.relative_to(HERE).as_posix() for p in selected], 'native': False})
(HERE / 'contacts.json').write_text(json.dumps(contacts, indent=2), encoding='utf-8')
count = dict(collections.Counter(r['status'] for r in rows))
cells = {role: sorted({(o['lang'], o['width']) for o in observations if o['role'] == role}) for role in ROLE_ORDER}
summary = {'counts': count, 'page_observations': len(observations), 'cells_per_role': {r: len(c) for r, c in cells.items()}, 'surfaces_per_role': {r: sorted({o['surface'] for o in observations if o['role'] == r}) for r in ROLE_ORDER}, 'native_png_complete': sum(s['declared_complete_run'] for s in manifest), 'native_png_retained': len(manifest), 'derived_contacts': len(contacts), 'excluded_invalid_oracle_count': len(excluded), 'fresh_sources_match': all(a.get('startup_matches_disk') and a.get('entry_matches_startup') for a in attests if a), 'failures': [r for r in rows if r['status'] == 'FAIL'], 'not_run_scenarios': dict(collections.Counter(r['scenario'] for r in rows if r['status'] == 'NOT RUN'))}
(HERE / 'counts.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in summary.items() if k != 'failures'}, ensure_ascii=False))
