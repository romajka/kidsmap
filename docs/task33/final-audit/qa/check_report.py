"""Check generated report structure and portable local links."""
import json,ast,hashlib
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote,urlsplit
ROOT=Path(__file__).resolve().parents[1]
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.ids=set()
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if attrs.get('id'):self.ids.add(attrs['id'])
        for name in ('href','src'):
            if attrs.get(name):self.links.append(attrs[name])
p=Links();p.feed((ROOT/'report.html').read_text(encoding='utf8'));errors=[]
for link in p.links:
    parsed=urlsplit(link)
    if parsed.scheme or parsed.netloc:continue
    if parsed.path:
        if not (ROOT/unquote(parsed.path)).is_file():errors.append('missing:'+link)
    elif parsed.fragment and parsed.fragment not in p.ids:errors.append('missing_anchor:'+link)
inputs=json.loads((ROOT/'report-inputs.json').read_text())
for name,digest in inputs.items():
    if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:errors.append('stale_report_input:'+name)
parsed_count=0
for path in ROOT.rglob('*.json'):
    json.loads(path.read_text(encoding='utf8'));parsed_count+=1
python_count=0
for path in (ROOT/'qa').rglob('*.py'):
    ast.parse(path.read_text(encoding='utf8'));python_count+=1
result={'status':'PASS'if not errors else'FAIL','links_checked':len(p.links),'json_parsed':parsed_count,'python_ast_parsed':python_count,'errors':errors}
(ROOT/'report-validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(result));raise SystemExit(bool(errors))
