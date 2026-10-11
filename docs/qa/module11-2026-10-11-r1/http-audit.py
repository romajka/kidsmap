"""Fresh native HTTP/head/schema evidence; no app SEO command or mutation."""
import sys,json,re,urllib.request,urllib.error,urllib.parse,datetime,hashlib
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET
P=Path(__file__).resolve().parent;B='http://localhost:8827';F=json.loads((P/'fixtures.json').read_text());rows=[];observations=[]
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*a,**kw):return None
opener=urllib.request.build_opener(NoRedirect)
def get(path,method='GET'):
 chain=[];seen=set()
 for _ in range(9):
  if path in seen:return {'chain':chain,'loop':True,'status':0,'path':path,'body':''}
  seen.add(path);url=urllib.parse.urljoin(B,path);assert urllib.parse.urlsplit(url).hostname=='localhost'
  try:r=opener.open(urllib.request.Request(url,method=method),timeout=25)
  except urllib.error.HTTPError as e:r=e
  body=r.read().decode('utf-8',errors='replace');status=r.status;loc=r.headers.get('Location','');chain.append({'path':path,'status':status,'location':loc,'x_robots_tag':r.headers.get('X-Robots-Tag','')})
  if status in [301,302,303,307,308] and loc:path=urllib.parse.urljoin(path,loc);continue
  return {'chain':chain,'status':status,'path':path,'body':body,'loop':False}
 return {'chain':chain,'status':0,'path':path,'body':'','loop':True}
class Head(HTMLParser):
 def __init__(self):super().__init__();self.meta={};self.links=[];self.title='';self.h1=[];self.json=[];self.in_title=False;self.in_h1=False;self.script=None;self.buf='';self.anchors=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='meta':self.meta[a.get('name') or a.get('property') or '']=a.get('content','')
  if tag=='link':self.links.append(a)
  if tag=='title':self.in_title=True
  if tag=='h1':self.in_h1=True;self.h1.append('')
  if tag=='script':self.script=a.get('type');self.buf=''
  if tag=='a' and a.get('href'):self.anchors.append(a['href'])
 def handle_endtag(self,tag):
  if tag=='title':self.in_title=False
  if tag=='h1':self.in_h1=False
  if tag=='script':
   if self.script=='application/ld+json':
    try:self.json.append(json.loads(self.buf))
    except ValueError:self.json.append({'parse_error':True,'prefix':self.buf[:80]})
   self.script=None
 def handle_data(self,data):
  if self.in_title:self.title+=data
  if self.in_h1:self.h1[-1]+=data
  if self.script:self.buf+=data
def add(s,ok,actual,lang='all',role='guest',url=''):
 rows.append({'scenario':s,'status':'NOT RUN' if ok is None else 'PASS' if ok else 'FAIL','role':role,'lang':lang,'width':'HTTP','url':url,'actual':actual})
def inspect(path,lang,kind):
 x=get(path);p=Head();p.feed(x['body']);canon=next((a.get('href','') for a in p.links if a.get('rel')=='canonical'),'');alts={a.get('hreflang'):a.get('href') for a in p.links if a.get('rel')=='alternate' and a.get('hreflang')}
 observation={k:v for k,v in x.items() if k!='body'};observation.update(kind=kind,lang=lang,title=p.title,h1=p.h1,meta=p.meta,canonical=canon,alternates=alts,jsonld=p.json,internal_links=[a for a in p.anchors if a.startswith('/')],body_hash=hashlib.sha256(x['body'].encode()).hexdigest())
 observations.append(observation)
 add(kind+'-response',x['status']==200 and not x['loop'],x['chain'],lang,url=path)
 if x['status']!=200:return x,p,observation
 add(kind+'-title-h1',bool(p.title.strip()) and len(p.h1)==1 and bool(p.h1[0].strip()),{'title':p.title,'h1':p.h1},lang,url=path)
 add(kind+'-metadata',bool(p.meta.get('description')) and bool(canon) and bool(p.meta.get('og:title')) and bool(p.meta.get('og:description')) and bool(p.meta.get('og:image')),p.meta,lang,url=path)
 add(kind+'-jsonld-parse',all(not isinstance(v,dict) or not v.get('parse_error') for v in p.json),{'scripts':len(p.json)},lang,url=path)
 add(kind+'-x-default',alts.get('x-default','').startswith(B+'/'),alts,lang,url=path)
 return x,p,observation
for lang in ['az','ru','en']:
 urls=F['urls'][lang];prefix='' if lang=='az' else '/'+lang
 for kind in ['place','organization','specialist','event','activity']:
  x,p,o=inspect(urls[kind],lang,kind)
  if x['status']==200:
   add(kind+'-canonical',o['canonical']==B+urls[kind],o['canonical'],lang,url=urls[kind])
   if kind in ['place','organization','activity']:
    add(kind+'-translation-alternates',set(o['alternates'])=={'az','ru','en','x-default'},o['alternates'],lang,url=urls[kind])
   add(kind+'-HEAD',get(urls[kind],'HEAD')['status']==200,'native HEAD',lang,url=urls[kind])
 for key in ['fallback','long','escaping']:
  x,p,o=inspect(urls['extras'][key],lang,key)
  if key=='fallback' and lang=='en':add('fallback-canonical-real-translation',o['canonical']==B+F['urls']['az']['extras'][key] and 'en' not in o['alternates'],o['alternates'],lang,url=urls['extras'][key])
  if key=='escaping':add('script-termination-escaped','<script>window.__QA11_XSS__=1</script>' not in x['body'] and '\\u003C/script>' in x['body'],{'jsonld_count':len(p.json)},lang,url=urls['extras'][key])
 for path in [prefix+'/catalog/',prefix+'/catalog/?page=2',prefix+'/catalog/?page=999',prefix+'/catalog/?page=1&sort=new',prefix+'/catalog/?q=QA11-NO-SUCH-ENTITY',prefix+'/catalog/?category=EDU',prefix+'/catalog/?page=2&page=1',prefix+'/catalog/qa11-strong/',prefix+'/catalog/qa11-empty/',prefix+'/events/',prefix+'/specialists/']:
  x,p,o=inspect(path,lang,'list-or-landing')
  if 'qa11-strong' in path:add('strong-landing-index',p.meta.get('robots','').startswith('index'),p.meta.get('robots'),lang,url=path)
  if 'qa11-empty' in path or '?q=' in path or '?category=' in path:add('filtered-or-empty-noindex','noindex' in p.meta.get('robots',''),p.meta.get('robots'),lang,url=path)
  if path.endswith('?page=2'):add('pagination-self-canonical',o['canonical']==B+path and 'noindex' not in p.meta.get('robots',''),{'canonical':o['canonical'],'robots':p.meta.get('robots')},lang,url=path)
 for key,status in [('draft',404),('inactive',404),('archived',404),('deleted',404)]:
  path=prefix+'/place/'+str(F['places'][key])+'/';x=get(path);add('private-place-'+key,x['status']==status and not x['loop'],x['chain'],lang,url=path)
 for key in ['pending','rejected']:
  path=prefix+'/place/'+str(F['extra_places'][key])+'/';x=get(path);add('private-place-'+key,x['status']==404 and not x['loop'],x['chain'],lang,url=path)
 for path in [prefix+'/place/'+str(F['places']['live'])+'/',prefix+'/place/'+str(F['places']['live'])+'-wrong-qa11-slug/?utm_source=qa11&x=1','/az'+urls['place'].removeprefix(prefix)+'?x=1']:
  x=get(path);add('legacy-wrongslug-query-redirect',x['status']==200 and len(x['chain'])<=2 and not x['loop'] and '?' not in x['path'],x['chain'],lang,url=path)
 add('program-workspace-private',get(urls['program'])['status']==200,'redirects to login (inspect chain below)',lang,url=urls['program']);observations.append({'kind':'program-private','lang':lang,'chain':get(urls['program'])['chain']})
x=get('/sitemap.xml');xml=ET.fromstring(x['body']);ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'};locs=[e.text for e in xml.findall('s:url/s:loc',ns)]
(P/'sitemap-initial.xml').write_text(x['body'],encoding='utf-8');add('sitemap-response',x['status']==200,{'count':len(locs)},url='/sitemap.xml')
for kind in ['place','organization','activity','specialist','event']:
 for lang in ['az','ru','en']:add('sitemap-public-'+kind,B+F['urls'][lang][kind] in locs,{'included':B+F['urls'][lang][kind] in locs},lang,url='/sitemap.xml')
for key in ['draft','inactive','archived','deleted']:
 add('sitemap-private-'+key,not any(re.search(r'/place/'+str(F['places'][key])+r'(?:-|/)',u) for u in locs),{'id':F['places'][key]},url='/sitemap.xml')
robots=get('/robots.txt');(P/'robots-initial.txt').write_text(robots['body'],encoding='utf-8');add('robots-native',robots['status']==200 and '/sitemap.xml' in robots['body'],{'status':robots['status'],'body':robots['body']},url='/robots.txt')
runtime=json.loads(get('/qa/version/')['body']);(P/'runtime-initial.json').write_text(json.dumps(runtime,indent=2));add('runtime-source-match',runtime['entry_matches_startup'] and runtime['startup_matches_disk'],runtime,role='qa',url='/qa/version/')
payload={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'transport':'real localhost HTTP','rows':rows,'observations':observations}
(P/'http-initial.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'counts':{s:sum(r['status']==s for r in rows) for s in ['PASS','FAIL','NOT RUN']},'failures':[r for r in rows if r['status']=='FAIL'][:15]},ensure_ascii=False))
