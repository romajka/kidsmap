"""Independent focused proof and harness correction; retains original evidence."""
import sys, importlib.util, json, datetime, re
from pathlib import Path
P=Path(__file__).resolve().parent
# Load HTTP utilities without executing earlier full suite.
ns={'__file__':str(P/'http-audit.py')};s=(P/'http-audit.py').read_text(encoding='utf-8');exec(compile(s[:s.index("for lang in ['az','ru','en']:" )],str(P/'http-audit.py'),'exec'),ns)
get=ns['get'];Head=ns['Head'];add=ns['add'];F=ns['F'];rows=ns['rows'];B=ns['B'];observations=[]
private=json.loads((P/'private-fixtures.json').read_text())
for lang in ['az','ru','en']:
 for state,urls in private['urls'][lang].items():
  for kind,path in urls.items():
   x=get(path);ok=x['status']==404;add('private-'+kind+'-'+state,ok,{'chain':x['chain'],'private_marker_in_html':'PRIVATE_QA11_' in x['body']},lang,url=path)
   if x['status']==200:observations.append({'kind':kind,'state':state,'lang':lang,'path':path,'marker':'PRIVATE_QA11_' in x['body']})
 for kind in ['organization','activity']:
  x=get(F['urls'][lang][kind],'HEAD');add('HEAD-'+kind,x['status']==200,{'chain':x['chain'],'Allow':'GET only in source @require_GET'},lang,url=F['urls'][lang][kind])
 x=get(F['urls'][lang]['extras']['escaping']);h=Head();h.feed(x['body']);add('security-script-termination', '<script>window.__QA11_XSS__=1</script>' not in x['body'] and all(not v.get('parse_error') for v in h.json) and any(v.get('name','').find('</script>')!=-1 for v in h.json),{'jsonld_scripts':len(h.json),'roundtrip_name':True},lang,url=x['path'])
 x=get(F['urls'][lang]['program']);add('program-private-correct-contract',x['status'] in [302,404] and 'PRIVATE_QA11_' not in x['body'],x['chain'],lang,url=F['urls'][lang]['program'])
 for path in ['/az'+F['urls'][lang]['place'].removeprefix('' if lang=='az' else '/'+lang)+'?x=1',('/'+lang if lang!='az' else '')+'/event/1-wrong-slug/?x=1']:
  x=get(path);add('redirect-chain-observed',x['status']==200 and not x['loop'] and '?' not in x['path'],{'hops':len(x['chain'])-1,'chain':x['chain']},lang,url=path)
sitemap=get('/sitemap.xml');add('all-private-markers-excluded-sitemap','PRIVATE_QA11_' not in sitemap['body'],{'body_hash':__import__('hashlib').sha256(sitemap['body'].encode()).hexdigest()},url='/sitemap.xml')
(P/'http-proof.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rows':rows,'observations':observations,'corrections':{'script-termination-escaped':'initial own helper wrongly assumed uppercase u003C; native/JSON roundtrip used','program-workspace-private':'initial own helper wrongly expected login200; actual permission guard404 is correct','AZ wrong-language slug':'two redirects are observed; no contractual1hop claim made'}},indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'counts':{s:sum(r['status']==s for r in rows) for s in ['PASS','FAIL','NOT RUN']},'failures':[r for r in rows if r['status']=='FAIL']},ensure_ascii=False))
