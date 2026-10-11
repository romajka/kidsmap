"""Apply exactly the approved two-line PO change, preserving original bytes."""
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
STATE=ROOT/'.tmp/place-qa08-fix-20261011-r1'
target=ROOT/'locale/ru/LC_MESSAGES/django.po'
before=target.read_bytes()
assert before==(STATE/'ru-po-before.bin').read_bytes(), 'Foreign PO drift; do not overwrite'
old='#~ msgid "Выберите район"\r\n#~ msgstr "Выберите район"'.encode('utf-8')
assert before.count(old)==1
new='msgid "Выберите район"\r\nmsgstr "Выберите район"'.encode('utf-8')
after=before.replace(old,new,1)
target.write_bytes(after)
proof={'file':target.relative_to(ROOT).as_posix(),'removed_bytes':6,'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest(),'exact_replacement':True,'old_entry_obsolete':True,'new_entry_active':True}
(HERE/'po-change.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
print('Only the two obsolete markers removed; all other PO bytes preserved')
