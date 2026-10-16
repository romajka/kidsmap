"""Select native RED/GREEN, audit only owned synthetic DB and filebased email."""
import collections,hashlib,json,os,re,socket,urllib.request
from pathlib import Path
from email.utils import getaddresses
import psycopg
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def result(name):
 d=json.loads((H/(name+'.js.result.json')).read_text());s=json.loads((H/(name+'.js.status.json')).read_text());assert s['native_driver_exit']==0 and not d.get('error'),(name,s)
 return d
red=result('red-setup');assert len(red['rows'])==22 and sum(r['status']=='FAIL'for r in red['rows'])==5
matrices=[result('green-'+lang)for lang in ('ru','az','en')];functional=result('functional');focus=result('visual-focus');selected=matrices+[functional,focus];rows=[r for d in selected for r in d['rows']];assert len(rows)==575 and all(r['status']=='PASS'for r in rows)
cells=[c for d in selected for c in d['completedCells']];phases=dict(collections.Counter(c['phase']for c in cells));assert phases=={'filled':18,'error':18,'empty':18,'historical-solo':6,'shared reviews':6,'native affected team lifecycle':1,'targeted focus occlusion':6}
unknown=[]
for d in [red]+selected:
 unknown.extend(d['diagnostics']['pageerrors']);unknown.extend(d['diagnostics']['badResponses']);unknown.extend(v for v in d['diagnostics']['requestFailures']if v['kind']!='external-blocked');unknown.extend(v for v in d['diagnostics']['console']if v['text']!='Failed to load resource: net::ERR_BLOCKED_BY_CLIENT.Inspector')
assert not unknown,unknown
historical=[]
for d in matrices:
 for r in d['rows']:
  if r['name']=='historical solo: cards fit panel and viewport':
   v=r['detail'];historical.append({'language':r['lang'],'width':r['width'],'card_x':v['cards'][0]['rect']['x'],'card_right':v['cards'][0]['rect']['right'],'root_scroll':v['rootScroll'],'body_scroll':v['bodyScroll']})
obs={'decision':'ACCESS-QA-04 native scoped GREEN; final source/preservation gate required','rows':rows,'counts':{'PASS':len(rows),'FAIL':0},'matrix_observations':sum(len(d['rows'])for d in matrices),'functional_observations':len(functional['rows']),'additional_focus_observations':len(focus['rows']),'phase_cells':phases,'cells':cells,'historical_solo_geometry':historical,'fresh_RED':{'rows':22,'PASS':17,'FAIL':5,'semantic_error':None,'source':'red-setup.js.result.json'},'diagnostics_unexplained':unknown,'browser':red['browser'],'notes':'Observations are not independent E2E tests. RED kept separately; no style/DOM injection; original geometry oracle unchanged; new metadata/forms/focus-hit checks strengthen it. Only targeted04/native affected consumers, not full07.'}
(H/'observations.json').write_text(json.dumps(obs,ensure_ascii=False,indent=2))
server=json.loads((H/'server.json').read_text());source=json.load(urllib.request.urlopen(server['url']+'/qa/source/',timeout=10));(H/'runtime-source-final.json').write_text(json.dumps(source,indent=2));state=json.load(urllib.request.urlopen(server['url']+'/qa/state/',timeout=10));assert state['read_only']
assert collections.Counter(v['status']for v in state['invitations'])=={'ACCEPTED':2,'CANCELED':3}and len(state['memberships'])==2
assert {(v['role'],v['active'],v['version'])for v in state['memberships']}=={('EDITOR',True,3),('EDITOR',False,2)}
for k in list(os.environ):
 if k not in {'PATH','LANG','LC_ALL','TZ'}:os.environ.pop(k)
cfg=json.loads((S/'config.json').read_text());secret=json.loads((S/'credentials.json').read_text());orig=socket.socket.connect;orig_ex=socket.socket.connect_ex
def allowed(addr):return isinstance(addr,tuple)and len(addr)>1 and addr[0]in('127.0.0.1','localhost')and addr[1]==cfg['pg_port']
def connect(sock,addr):
 if not allowed(addr):raise RuntimeError('Own QA egress denied')
 return orig(sock,addr)
def connect_ex(sock,addr):
 if not allowed(addr):raise RuntimeError('Own QA egress denied')
 return orig_ex(sock,addr)
socket.socket.connect=connect;socket.socket.connect_ex=connect_ex
with psycopg.connect(host='127.0.0.1',port=cfg['pg_port'],dbname=cfg['database'],user=cfg['user'],password=secret['db_password'],autocommit=True)as conn:
 with conn.transaction():
  with conn.cursor()as c:
   c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
   c.execute('SELECT status,count(*) FROM catalog_emailoutbox GROUP BY status');outbox=dict(c.fetchall())
   c.execute('SELECT event_kind,count(*) FROM catalog_workflownotification GROUP BY event_kind');events=dict(c.fetchall());assert events.get('team_invitation')==5 and events.get('team_invitation_decision')==2
   c.execute("SELECT i.status,coalesce(n.decisions,0),count(*) FROM catalog_ownerteaminvitation i LEFT JOIN (SELECT entity_id,count(*) AS decisions FROM catalog_workflownotification WHERE event_kind='team_invitation_decision' AND entity_type='place_team_invitation' GROUP BY entity_id)n ON n.entity_id=i.id GROUP BY i.status,coalesce(n.decisions,0)");decisions=c.fetchall();assert set(decisions)=={('ACCEPTED',1,2),('CANCELED',0,3)}
   c.execute('SELECT ownership_version,count(*) FROM catalog_place GROUP BY ownership_version');ownership=dict(c.fetchall());assert ownership=={1:3}
   c.execute("SELECT last_error_code,count(*) FROM catalog_emailoutbox WHERE status='suppressed' GROUP BY last_error_code");suppressed=dict(c.fetchall());assert set(suppressed)<={'stale_access'}
   c.execute('SELECT count(*) FROM django_migrations');migrations=c.fetchone()[0]
assert set(outbox)<={'sent','suppressed'}and sum(outbox.values())==state['outbox']
files=list((S/'email').glob('*.log'));messages=0;addresses=[]
for p in files:
 data=p.read_text();messages+=len(re.findall(r'^MIME-Version:',data,re.M));u=re.sub(r'\r?\n[ \t]+',' ',data);addresses.extend(a for _,a in getaddresses(re.findall(r'^To: (.+)$',u,re.M)))
assert messages==outbox['sent']and len(addresses)==messages and all(a.endswith('@example.invalid')for a in addresses)
blocked=False
try:socket.create_connection(('203.0.113.1',443),timeout=1)
except RuntimeError:blocked=True
assert blocked
readback={'read_only':True,'timeouts':'statement10s/lock2s','invitation_statuses':dict(collections.Counter(v['status']for v in state['invitations'])),'membership_states':[{'role':v['role'],'active':v['active'],'version':v['version']}for v in state['memberships']],'unique_decisions_by_invitation_status':decisions,'place_ownership_versions':ownership,'event_counts':events,'outbox':outbox,'suppression_error_codes':suppressed,'migrations':migrations,'local_email_files':len(files),'actual_local_email_messages':messages,'all_recipients_fictional':True,'external_probe_denied':blocked,'mail_note':'Manual scheduler tick SIMULATED; real own filebased letters, not SMTP. A pending long invite was sent before later native cancellation; sent rows need not stay PENDING forever. Consumed/canceled undelivered invitations suppressed by existing guard.'}
(H/'readback-final.json').write_text(json.dumps(readback,indent=2))
png=[]
for p in sorted((H/'screenshots').glob('*.png')):
 with Image.open(p)as im:png.append({'path':str(p.relative_to(H)),'sha256':sha(p),'width':im.width,'height':im.height,'classification':'native prepatch RED'if p.name.startswith('red-')else'native postpatch scoped GREEN evidence'})
assert len(png)==71
(H/'png-manifest.json').write_text(json.dumps(png,indent=2))
print(json.dumps({'counts':obs['counts'],'phase_cells':phases,'historical':historical,'PNGs':len(png),'readback':readback},ensure_ascii=False))
