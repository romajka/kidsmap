from pathlib import Path
import json
h=Path(__file__).parent
p=h/'visual-matrix.js'
s=p.read_text(encoding='utf-8').replace('__INFORMATIONAL__',json.loads((h/'admin-flow.result.txt').read_text())['ids']['informational'])
# Enter on a blank creation form invokes HTML validation. No live mutation.
p.write_text(s,encoding='utf-8')
