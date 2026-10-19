import json,sys
from pathlib import Path
O=Path(__file__).resolve().parent;phase=sys.argv[1];assert phase in ['red','green']
source=(O/'browser-sentinels.js').read_text();baseline='null' if phase=='red' else (O/'evidence/browser-sentinels-red.json').read_text()
if phase=='green':baseline=json.dumps(json.loads(baseline)['rows'])
(O/('browser-sentinels-'+phase+'.js')).write_text(source.replace('__PHASE__',phase).replace('__SENTINEL_BASELINE__',baseline))
print('Own '+phase+' sentinel script prepared; source prototype/injection disabled')
