import json
from pathlib import Path
Q=Path('/mnt/c/kidsmap/.tmp/social08-pc-fix-r1');rows=json.loads((Q/'matrix.json').read_text());r=rows[-1];print(r['item']['key']);print('canceled',r['facts']['canceled']);print('after',r['facts']['after'])
