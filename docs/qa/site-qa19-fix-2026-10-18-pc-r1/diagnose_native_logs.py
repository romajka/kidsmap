import inspect,json,sys
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/site19-pc-fix-r1'
sys.path.insert(0,str(Q));sys.argv=['runtime.py','diagnose'];from runtime import *
from django.contrib.admin.models import LogEntry
from django.contrib.admin.options import ModelAdmin
from django.db.models import Count
from django.db import transaction,connection
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'")
 labels=list(LogEntry.objects.values('object_repr').annotate(count=Count('pk')).order_by('object_repr'))
result={'synthetic_log_label_counts':labels,'installed_log_change_source':inspect.getsource(ModelAdmin.log_change),'scope':'Own normal QA DB aggregate label/count only; no users/messages/cookie values'}
(Q/'native-log-diagnosis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
