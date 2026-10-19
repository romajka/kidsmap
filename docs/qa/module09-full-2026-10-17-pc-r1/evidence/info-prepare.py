from pathlib import Path
Q=Path(__file__).resolve().parent
p=Q/'runtime_info.py';p.write_text('''import sys,json,hashlib,platform
sys.argv=['runtime.py','info']
from runtime import *
from django.db import connection,transaction
from django.template.loader import get_template
from django.db.migrations.recorder import MigrationRecorder
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY')
  c.execute("SET LOCAL statement_timeout='5s'")
  c.execute('SHOW server_version');version=c.fetchone()[0]
 output=dict(testing=settings.TESTING,python=platform.python_version(),django=django.get_version(),postgresql=version,db=settings.DATABASES['default']['NAME'],host=settings.DATABASES['default']['HOST'],cache_backend=settings.CACHES['default']['BACKEND'],email_backend=settings.EMAIL_BACKEND,media=str(settings.MEDIA_ROOT),private_media=str(settings.PRIVATE_MEDIA_ROOT),sole_locales=list(map(str,settings.LOCALE_PATHS)),login_url=settings.LOGIN_URL,migrations=MigrationRecorder.Migration.objects.count(),template_origin=get_template('catalog/typed_reviews.html').origin.name,source1024=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in entry['sources'].items()))
(QA/'runtime-info.json').write_text(json.dumps(output,indent=2));print('Own current source/runtime/locale origin recorded; no environment values exported')
''')
