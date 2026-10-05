import hashlib,json,subprocess,urllib.request,urllib.parse
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parents[1]
REPO=HERE.parents[2]
COMPLETION=HERE.parent/'completion'
snapshot=json.loads((COMPLETION/'final-verification.json').read_text())
for item in snapshot['source_files']:
    for root in (REPO,Path('/root/km-completion-browser')):
        assert hashlib.sha256((root/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
evidence=json.loads((COMPLETION/'evidence-manifest.json').read_text())['files']
for item in evidence:
    assert hashlib.sha256((COMPLETION/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
class Links(HTMLParser):
    def __init__(self):super().__init__();self.urls=[]
    def handle_starttag(self,tag,attrs):
        values=dict(attrs)
        for attr in (['src'] if tag=='img' else ['href'] if tag=='a' else []):
            value=values.get(attr,'')
            if value and not value.startswith(('#','https:','http:')):self.urls.append(value)
links=Links();links.feed((COMPLETION/'report.html').read_text())
result=[]
for url in ['/qa/','/ru/','/ru/catalog/','/ru/events/','/ru/specialists/','/qa/fixtures.json','/qa/files/report/report.html']+['/qa/files/report/'+url for url in sorted(set(links.urls))]:
    try:
        normalized=urllib.parse.urljoin('http://127.0.0.1:8780/qa/files/report/report.html',url)
        # Browsers resolve parent-segment links before requesting them.
        from posixpath import normpath
        parts=urllib.parse.urlsplit(normalized)
        normalized=urllib.parse.urlunsplit(parts._replace(path=normpath(parts.path)+('/' if parts.path.endswith('/') else '')))
        with urllib.request.urlopen(normalized,timeout=15) as response:status=response.status
    except urllib.error.HTTPError as error:status=error.code
    result.append({'url':url,'status':status})
info=json.loads(subprocess.check_output(['docker','inspect','kidsmap-manual-20261004'],text=True))[0]
assert info['HostConfig']['NetworkMode']=='none' and not info['HostConfig']['PortBindings']
assert info['Config']['Labels']['kidsmap.manual.owner']=='manual-20261004'
output={'checked_at':datetime.now(timezone.utc).isoformat(),'application_source_files_unchanged':len(snapshot['source_files']),
    'completion_evidence_files_unchanged':len(evidence),'http':result,'database_network':'none','database_ports':False,
    'server_bind':'127.0.0.1:8780','production':'NOT_CONTACTED','scope':'local preview and manual acceptance guide only',
    'status':'PASS' if all(r['status']==200 for r in result) else 'REVIEW_REQUIRED'}
(HERE/'runtime-verification.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({**{k:v for k,v in output.items() if k!='http'},'http_checks':len(result),'bad_http':[r for r in result if r['status']!=200]}))
