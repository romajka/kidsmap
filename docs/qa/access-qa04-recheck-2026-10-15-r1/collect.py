"""Factual PLAN evidence selection, never a repaired/accepted UI claim."""
import collections,hashlib,json,os,re,socket,urllib.request
from pathlib import Path
from email.utils import getaddresses
import psycopg
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def result(name,partial=False):
 d=json.loads((H/(name+'.js.result.json')).read_text());s=json.loads((H/(name+'.js.status.json')).read_text());assert s['native_driver_exit']==0
 if partial:
  assert name=='matrix-ru'and len(d['rows'])==49 and len(d['completedCells'])==8 and 'evaluateAll' in d['error']
 else:assert d.get('error')is None
 return d
setup=result('setup');ru=result('matrix-ru',True);reviews=result('reviews-ru-r2');az=result('matrix-az');en=result('matrix-en');solo=result('historical-solo')
assert all(r['status']=='PASS'for r in setup['rows'])
main_rows=ru['rows']+reviews['rows']+az['rows']+en['rows'];all_rows=setup['rows']+main_rows+solo['rows'];assert len(main_rows)==153 and len(all_rows)==198
cells=ru['completedCells']+reviews['completedCells']+az['completedCells']+en['completedCells']+solo['completedCells'];assert len(cells)==36
phase_counts=collections.Counter(c['phase']for c in cells);assert dict(phase_counts)=={'filled':18,'error':3,'empty':3,'shared reviews':6,'historical-solo':6}
all_results=[setup,ru,reviews,az,en,solo];unexplained=[]
for d in all_results:
 unexplained.extend(d['diagnostics']['pageerrors']);unexplained.extend(d['diagnostics']['badResponses']);unexplained.extend(v for v in d['diagnostics']['requestFailures']if v['kind']!='external-blocked')
 unexplained.extend(v for v in d['diagnostics']['console']if v['text']!='Failed to load resource: net::ERR_BLOCKED_BY_CLIENT.Inspector')
assert not unexplained,unexplained
historic=[]
for row in solo['rows']:
 if row['name']=='historical solo: cards fit panel and viewport':
  d=row['detail'];c=d['cards'][0];historic.append({'language':row['lang'],'width':row['width'],'panel_right':d['panel']['right'],'card_x':c['rect']['x'],'card_right':c['rect']['right'],'heading_text_rects':c['textRects'],'root_scroll':d['rootScroll'],'body_scroll':d['bodyScroll'],'status':row['status']})
assert len(historic)==6 and all(r['card_right']>r['width']and r['status']=='FAIL'for r in historic)
summary={'decision':'PLAN ACCESS-QA-04 completed fresh RED; defect OPEN, implementation NOT RUN','rows':all_rows,'counts':dict(collections.Counter(r['status']for r in all_rows)),'main_matrix_counts':dict(collections.Counter(r['status']for r in main_rows)),'historical_solo_counts':dict(collections.Counter(r['status']for r in solo['rows'])),'setup_checks':len(setup['rows']),'phase_cells':dict(phase_counts),'cells':cells,'historical_solo_geometry':historic,'diagnostics_unexplained':unexplained,'browser':setup['browser'],'partial_native_source':'matrix-ru has semantic QA review-link error after49rows/8finished states; retain those rows, supplement only2missing shared reviews with reviews-ru-r2. No successful batch result invented. RU long-cohort geometry was during entry animation; settled solo and AZ/EN independently confirm cause.','limits':'These are observations, not independent E2E cases. No CSS patch/style injection. Full18cells each empty/error, post-patch GREEN, full07 NOT RUN.'}
(H/'observations.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
server=json.loads((H/'server.json').read_text());runtime=json.load(urllib.request.urlopen(server['url']+'/qa/source/',timeout=10));state=json.load(urllib.request.urlopen(server['url']+'/qa/state/',timeout=10))
assert state['read_only']and len(state['invitations'])==4 and collections.Counter(v['status']for v in state['invitations'])=={'PENDING':1,'ACCEPTED':1,'CANCELED':2}
assert len(state['memberships'])==1 and state['memberships'][0]['active']and state['memberships'][0]['role']=='EDITOR'and state['memberships'][0]['version']==1
(H/'runtime-source-final.json').write_text(json.dumps(runtime,indent=2))
for key in list(os.environ):
 if key not in {'PATH','LANG','LC_ALL','TZ'}:os.environ.pop(key)
cfg=json.loads((S/'config.json').read_text());secret=json.loads((S/'credentials.json').read_text());original=socket.socket.connect;original_ex=socket.socket.connect_ex
def allowed(addr):return isinstance(addr,tuple)and len(addr)>1 and addr[0]in('localhost','127.0.0.1')and addr[1]==cfg['pg_port']
def connect(sock,addr):
 if not allowed(addr):raise RuntimeError('Own QA egress denied')
 return original(sock,addr)
def connect_ex(sock,addr):
 if not allowed(addr):raise RuntimeError('Own QA egress denied')
 return original_ex(sock,addr)
socket.socket.connect=connect;socket.socket.connect_ex=connect_ex
with psycopg.connect(host='127.0.0.1',port=cfg['pg_port'],dbname=cfg['database'],user=cfg['user'],password=secret['db_password'],autocommit=True)as conn:
 with conn.transaction():
  with conn.cursor()as c:
   c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
   c.execute('SELECT status,count(*) FROM catalog_emailoutbox GROUP BY status');outbox=dict(c.fetchall())
   c.execute("SELECT o.status,n.event_kind,i.status,count(*) FROM catalog_emailoutbox o JOIN catalog_workflownotification n ON n.id=o.notification_id LEFT JOIN catalog_ownerteaminvitation i ON n.entity_id=i.id AND n.event_kind='team_invitation' GROUP BY o.status,n.event_kind,i.status");delivery_rows=c.fetchall()
   c.execute('SELECT count(*) FROM django_migrations');migrations=c.fetchone()[0]
assert outbox=={'sent':2,'suppressed':3}
assert set(delivery_rows)=={('sent','team_invitation_decision',None,1),('sent','team_invitation','PENDING',1),('suppressed','team_invitation','ACCEPTED',1),('suppressed','team_invitation','CANCELED',2)}
files=list((S/'email').glob('*.log'));messages=0;addresses=[]
for p in files:
 data=p.read_text();messages+=len(re.findall(r'^MIME-Version:',data,re.M));unfolded=re.sub(r'\r?\n[ \t]+',' ',data);addresses.extend(a for _,a in getaddresses(re.findall(r'^To: (.+)$',unfolded,re.M)))
assert messages==outbox['sent']==2 and len(addresses)==2 and all(a.endswith('@example.invalid')for a in addresses)
blocked=False
try:socket.create_connection(('203.0.113.1',443),timeout=1)
except RuntimeError:blocked=True
assert blocked
readback={'read_only':True,'timeouts':'statement10s/lock2s','invitations_by_status':dict(collections.Counter(v['status']for v in state['invitations'])),'active_memberships':1,'role':'EDITOR','membership_version':1,'notifications':state['notifications'],'outbox':outbox,'delivery_currentness_aggregate':delivery_rows,'migrations':migrations,'local_email_files':len(files),'local_email_messages':messages,'all_recipients_fictional':True,'external_probe_denied':blocked,'setup':'users/places ORM only; invitation/accept/cancel by nativeUI. Empty-owner snapshots preceded a later separate historical-solo invitation to that owner place. No roles/remove transition tested yet.'}
(H/'readback-final.json').write_text(json.dumps(readback,indent=2))
png=[]
for p in sorted((H/'screenshots').glob('*.png')):
 with Image.open(p)as im:png.append({'path':str(p.relative_to(H)),'sha256':sha(p),'width':im.width,'height':im.height,'classification':'native prepatch RED/controls/shared evidence, not GREEN'})
assert len(png)==39
(H/'png-manifest.json').write_text(json.dumps(png,indent=2))
print(json.dumps({'decision':summary['decision'],'counts':summary['counts'],'main_counts':summary['main_matrix_counts'],'phase_cells':summary['phase_cells'],'PNGs':len(png),'readback':readback},ensure_ascii=False))
