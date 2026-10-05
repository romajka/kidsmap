import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[4];out=root/'docs/task33/final-audit'
path=root/'.tmp/photo-form.html'
data=json.loads((out/'javascript-results.json').read_text(encoding='utf8'))
data['retained_html_fixture']={'path':'.tmp/photo-form.html','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'provenance':'UNKNOWN historical local fixture; not freshly rendered in this audit','executed_case':'photo editor boots inside the actual Django wizard HTML','conclusion_boundary':'One of the11 cases uses retained HTML. Passing that case proves compatibility with those retained bytes, not current Django render.'}
(out/'javascript-results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
probe=json.loads((out/'javascript-phone-diagnostic.json').read_text(encoding='utf8'))
probe['limitations']=['jsdom emitted Not implemented: navigation to another Document on the tel action; native OS call and actual network are not verified.']
(out/'javascript-phone-diagnostic.json').write_text(json.dumps(probe,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Retained HTML fixture and native-navigation limitations recorded; no new test execution')
