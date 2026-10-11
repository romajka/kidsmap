"""Local test-only mail capture. Tokens remain in ignored scratch, never report."""
from pathlib import Path
from django.core.mail.backends.locmem import EmailBackend as LocMem
from django.conf import settings
import json,threading
lock=threading.Lock()
class EmailBackend(LocMem):
 def send_messages(self,messages):
  assert settings.TESTING
  sent=super().send_messages(messages)
  with lock:
   p=Path(settings.QA_ROOT)/'mail.json'
   data=json.loads(p.read_text(encoding='utf-8')) if p.exists() else []
   for m in messages:data.append({'to':m.to,'subject':m.subject,'body':m.body})
   p.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
  return sent
