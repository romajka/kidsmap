"""Approved PLACE-QA-01–07 run: preserve inputs and create a fresh isolated stand."""
import hashlib
import json
import socket
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREVIOUS = ROOT / 'docs/qa/place-qa07-plan-2026-10-10'
SCRATCH = ROOT / '.tmp/place-qa01-07-fix-20261010'
SCRATCH.mkdir(parents=True, exist_ok=False)
for port in (55460, 8840):
    with socket.socket() as probe:
        assert probe.connect_ex(('127.0.0.1',port)) != 0, ('Port occupied',port)
for language in ('ru','az','en'):
    for ext in ('po','mo'):
        source = ROOT / f'locale/{language}/LC_MESSAGES/django.{ext}'
        target = SCRATCH / f'baseline-locale/{language}/LC_MESSAGES/django.{ext}'
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(source.read_bytes())
for old,new in [('qa07_settings.py','kmfix_settings.py'),('runtime.py','runtime.py'),
                ('prepare.py','prepare.py'),('pw.py','pw.py'),('browser.config.json','browser.config.json'),
                ('browser-setup.js','browser-setup.js')]:
    content = (PREVIOUS/old).read_text(encoding='utf-8')
    for before,after in [('qa07','kmfix'),('QA07','KMFIX'),('place-kmfix-plan-20261010','place-qa01-07-fix-20261010'),
                         ('place-kmfix-plan-2026-10-10','place-qa01-07-fix-2026-10-10'),('55444','55460'),('8823','8840')]:
        content = content.replace(before,after)
    if new=='prepare.py':
        content = content.replace('kidsmap-placekmfix-plan-20261010','kidsmap-placeqa01-07-fix-20261010')
        content = content.replace('place-qa0[1-6]','place-qa0[1-7]')
        content = content.replace("active = next", "files += ['static/js/owner_place_map_picker.js','static/js/location_resolution.js','static/js/owner_place_continuous.js','static/admin/js/kidsmap_place_form.js','static/admin/css/pages/kidsmap_place_form.css','src/catalog/services/publication.py','src/catalog/services/permanent_place_wizard.py','static/css/pages/owner_place_continuous.css']\nactive = next")
        content = content.replace("'application_implementation':'NOT AUTHORIZED'", "'application_implementation':'APPROVED PLACE-QA-01–07; user: Всё, начни работу, всё исправь.'")
    if new=='runtime.py':
        content = content.replace("elif sys.argv[1] == 'checks':", "elif sys.argv[1] == 'test':\n    call_command('test',*sys.argv[2:],interactive=False,verbosity=1)\nelif sys.argv[1] == 'checks':")
    (HERE/new).write_text(content,encoding='utf-8')
(HERE/'approval.json').write_text(json.dumps({'scope':'PLACE-QA-01–07','mode':'APPROVED IMPLEMENT',
    'user_instruction':'То, что мы здесь общались, всё исправь. Всё, начни работу, всё исправь.',
    'constraints':['preserve foreign work/stands','isolated DJANGO_TESTING=1','no production/commit/push/deploy'],
    'graph':'Codebase Memory transport closed; bounded source fallback'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Approved isolated fix harness created; source snapshot is recorded by prepare.py before edits.')
