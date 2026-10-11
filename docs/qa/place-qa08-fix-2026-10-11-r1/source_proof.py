"""Own runtime / compiled catalogue proof; no shared catalogue mutation."""
import gettext
import hashlib
import json
import urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
STATE=ROOT/'.tmp/place-qa08-fix-20261011-r1'
key='Выберите район'
entries=[]
for language in ('ru','az','en'):
    roots={profile:STATE/profile/'locale'/language/'LC_MESSAGES/django.mo' for profile in ('baseline-locales','fixed-locales')}
    roots['shared']=ROOT/'locale'/language/'LC_MESSAGES/django.mo'
    proofs={}
    for profile,path in roots.items():
        with path.open('rb') as stream: translator=gettext.GNUTranslations(stream)
        proofs[profile]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'active_key':key in translator._catalog,'direct_translation':translator.gettext(key)}
    po=ROOT/'locale'/language/'LC_MESSAGES/django.po'
    entries.append({'language':language,'current_po_sha256':hashlib.sha256(po.read_bytes()).hexdigest(),'catalogues':proofs})
(HERE/'compiled-locales-proof.json').write_text(json.dumps({'key':key,'entries':entries,'shared_mo_written':False},ensure_ascii=False,indent=2),encoding='utf-8')
with urllib.request.urlopen('http://localhost:8842/qa/version/',timeout=40) as response:
    runtime=json.load(response)
assert runtime['snapshot_matches_startup'] and runtime['startup_matches_disk'] and runtime['testing']
assert runtime['db_port']==55447 and runtime['locale_profile']=='fixed-locales'
(HERE/'runtime-version.json').write_text(json.dumps(runtime,indent=2),encoding='utf-8')
qa={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.py') if p.name in ('run.py','qa_settings.py','qa_urls.py')}
(HERE/'qa-runtime-hashes.json').write_text(json.dumps(qa,indent=2),encoding='utf-8')
print('Runtime startup/disk match; verified isolated fixed MO; RU active key:',entries[0]['catalogues']['fixed-locales']['active_key'])
