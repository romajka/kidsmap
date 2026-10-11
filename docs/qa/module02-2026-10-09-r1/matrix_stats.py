from pathlib import Path
import sys
sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter
import json
h=Path(__file__).parent
for name in ['visual-matrix','create-state-matrix','admin-render-proof']:
 p=h/(name+'.result.txt')
 if not p.exists():continue
 try:data=json.loads(p.read_text(encoding='utf-8'))
 except ValueError:continue
 print(name,len(data['rows']),dict(Counter(r['status'] for r in data['rows'])))
 if name=='visual-matrix':
  print('Errors',len(data.get('errors',[])),'blocked',data.get('blockedExternalOrigins',{}))
  print('Error samples',data.get('errors',[])[:4])
  print('NOT RUN samples',[(r['scene'],r.get('error','')[:180]) for r in data['rows'] if r['status']=='NOT RUN'][:3])
  print('Geometry failures',[(r['role'],r['language'],r['width'],r['scene'],r.get('geometry')) for r in data['rows'] if r.get('geometry',{}).get('horizontalOverflow')][:8])
  print('small buttons',[(r['scene'],r['language'],r['width'],r['geometry']['smallButtons'][:3]) for r in data['rows'] if r.get('geometry',{}).get('smallButtons')][:5])
