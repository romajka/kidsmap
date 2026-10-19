import json
from pathlib import Path
Q=Path('/mnt/c/kidsmap/.tmp/social09-pc-fix-r1');expected=json.loads((Q/'fixtures.json').read_text())['expected'];(Q/'combined.js').write_text((Q/'combined-body.js').read_text(encoding='utf-8-sig').replace('__EXPECTED__',json.dumps(expected)))
print('Combined sort/page native6cases prepared; execute after main matrix and SEO probes')
