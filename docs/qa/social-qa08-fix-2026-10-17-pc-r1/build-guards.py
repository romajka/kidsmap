import json
from pathlib import Path
Q=Path('/mnt/c/kidsmap/.tmp/social08-pc-fix-r1');cases=[c for c in json.loads((Q/'cases.json').read_text()) if not c['key'].startswith('guard-') and c['width']==390];changed=json.loads((Q/'guard-cases.json').read_text());assert len(cases)==len(changed)==6
(Q/'guards.js').write_text((Q/'guards-body.js').read_text(encoding='utf-8-sig').replace('__CASES__',json.dumps(cases)).replace('__CHANGED__',json.dumps(changed)))
print('Six real-context ACL/method/CSRF sets and six native current-success flows ready; execute after matrix only')
