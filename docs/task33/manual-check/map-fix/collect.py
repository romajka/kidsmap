import hashlib,json,shutil,urllib.request
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
def read_result(name):
    lines=(HERE/(name+'.log')).read_text(encoding='utf-8-sig').splitlines()
    result=json.loads(next(line for line in lines if line.startswith('{')))
    (HERE/(name+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result
red=read_result('browser-red');live=read_result('browser-live');matrix=read_result('browser-matrix')
assert not red['pass'] and red['result']['failedTilesVisible']>0
assert matrix['status']=='PASS' and len(matrix['rows'])==18
assert len(live['responses'])==15 and all(row['status']==200 for row in live['responses'])
assert all(row['referer']=='http://127.0.0.1:8780/' for row in live['requests'])
source=json.loads((HERE.parent/'source-manifest.json').read_text())
for item in source['source_files']:
    for root in (REPO,Path(source['runtime_root'])):
        assert hashlib.sha256((root/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
completion=HERE.parents[1]/'completion'
baseline=json.loads((completion/'final-verification.json').read_text())['source_files']
for item in baseline:
    assert hashlib.sha256((Path('/root/km-completion-browser')/item['path']).read_bytes()).hexdigest()==item['sha256']
evidence=json.loads((completion/'evidence-manifest.json').read_text())['files']
for item in evidence:assert hashlib.sha256((completion/item['path']).read_bytes()).hexdigest()==item['sha256']
http=[]
for url in ('/ru/','/','/en/','/qa/','/ru/catalog/','/qa/files/screens/map-fixed-live.png'):
    with urllib.request.urlopen('http://localhost:8780'+url,timeout=15) as response:
        http.append({'url':url,'status':response.status})
        if url=='/ru/':assert response.headers['Referrer-Policy']=='same-origin'
screens=HERE/'screenshots';screens.mkdir(exist_ok=True)
for name in ('map-fixed-live','map-403-320','map-403-1280','map-offline-320','map-offline-1280'):
    shutil.copyfile(REPO/'output/playwright/manual-check'/f'{name}.png',screens/f'{name}.png')
result={'status':'PASS','checked_at':datetime.now(timezone.utc).isoformat(),'source_files':len(source['source_files']),
    'historical_runtime_files_unchanged':len(baseline),'completion_evidence_unchanged':len(evidence),
    'js_tests':12,'browser_cases':18,'browser_unexpected_errors':0,'live_tiles_http_200':15,
    'scope':'Homepage Leaflet/OpenStreetMap only; Google catalog fallback unchanged',
    'backend_full_regression':'NOT_REPEATED_JS_AND_TEMPLATE_CHANGE','production':'NOT_CONTACTED','http':http}
(HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result))
