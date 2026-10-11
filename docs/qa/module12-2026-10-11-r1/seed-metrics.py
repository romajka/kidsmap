"""Initial fictional dated aggregates; never used for tested UI transitions."""
import seed
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from catalog.models import FunnelEvent
from django.utils import timezone
from pathlib import Path
import json
assert FunnelEvent.objects.count()==0
pid=seed.places['live'];now=timezone.now()
entries=[]
for label,when,n in [('previous',now-timedelta(days=35),1),('current',now-timedelta(days=1),2),('baku-before-month',datetime(2026,9,30,23,59,59,tzinfo=ZoneInfo('Asia/Baku')),1),('baku-after-month',datetime(2026,10,1,0,0,0,tzinfo=ZoneInfo('Asia/Baku')),1)]:
 for i in range(n):
  e=FunnelEvent.objects.create(event_type='place_view',schema_version=2,subject_type='place',subject_id=pid,place_id=pid,occurred_at=when,visitor_key_hash='fictional-seed-visitor',session_key_hash='fictional-seed-session',device_class='desktop',path='/synthetic-initial-history/')
  entries.append({'label':label,'occurred_at':when.isoformat(),'subject_id':pid,'event_type':'place_view'})
(seed.HERE/'initial-metrics.json').write_text(json.dumps({'synthetic_initial_only':True,'entries':entries},indent=2))
print('Initial synthetic metrics',len(entries))
