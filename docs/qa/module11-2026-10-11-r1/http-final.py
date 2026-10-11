"""Current post-UI HTTP proof, exact private paths, no direct data transitions."""
from pathlib import Path
import json,datetime,hashlib
P=Path(__file__).resolve().parent
s=(P/'http-audit.py').read_text(encoding='utf-8');ns={'__file__':str(P/'http-audit.py')};exec(compile(s[:s.index("for lang in ['az','ru','en']:" )],str(P/'http-audit.py'),'exec'),ns)
get=ns['get'];Head=ns['Head'];add=ns['add'];F=ns['F'];rows=ns['rows'];B=ns['B'];inspect=ns['inspect']
xml=get('/sitemap.xml');(P/'sitemap-final.xml').write_text(xml['body'],encoding='utf-8')
private=json.loads((P/'private-fixtures.json').read_text())
for lang in ['az','ru','en']:
 F['urls'][lang]['specialist']=('' if lang=='az' else '/'+lang)+'/specialists/fictional-qa11-specialist-ui-renamed/'
 for kind in ['place','organization','activity','event','specialist']:
  path=F['urls'][lang][kind];x,h,o=inspect(path,lang,'final-'+kind)
  add('final-canonical',o.get('canonical')==B+path,o.get('canonical'),lang,url=path)
  add('final-sitemap-'+kind,B+path in xml['body'],{'included':B+path in xml['body']},lang,url='/sitemap.xml')
  if kind in ['organization','activity']:add('final-HEAD-'+kind,get(path,'HEAD')['status']==200,get(path,'HEAD')['chain'],lang,url=path)
 for state,urls in private['urls'][lang].items():
  for kind,path in urls.items():
   x=get(path);h=Head();h.feed(x['body']);add('final-private-'+kind+'-'+state,x['status']==404 and 'PRIVATE_QA11_' not in x['body'],{'chain':x['chain'],'entity_jsonld':len(h.json)},lang,url=path)
   add('final-private-sitemap-'+kind+'-'+state,B+path not in xml['body'],{'exact_path':B+path},lang,url='/sitemap.xml')
 for key in ['draft','inactive','archived','deleted']:
  path=('' if lang=='az' else '/'+lang)+'/place/'+str(F['places'][key])+'/';x=get(path)
  add('final-private-place-'+key,x['status']==404,x['chain'],lang,url=path)
  add('final-private-place-sitemap-'+key,not __import__('re').search(r'/place/'+str(F['places'][key])+r'(?:-|/)',xml['body']),{'id':F['places'][key]},lang,url='/sitemap.xml')
 # Permit observed chains rather than invent a universal one-hop contract.
 for path in [('' if lang=='az' else '/'+lang)+'/event/1-wrong/?foreign=1',('' if lang=='az' else '/'+lang)+'/place/1-wrong/?foreign=1']:
  x=get(path);add('final-redirect-no-loop',x['status']==200 and not x['loop'] and '?' not in x['path'],{'chain':x['chain'],'hops':len(x['chain'])-1},lang,url=path)
out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rows':rows,'observations':ns['observations'],'sitemap_sha256':hashlib.sha256(xml['body'].encode()).hexdigest()}
(P/'http-final.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:sum(r['status']==k for r in rows) for k in ['PASS','FAIL','NOT RUN']}))
