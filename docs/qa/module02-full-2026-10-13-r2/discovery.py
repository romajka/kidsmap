import json
from pathlib import Path
from django.conf import settings
from django.test.utils import get_runner
P=Path(__file__).resolve().parent
labels=json.loads((P/'test-labels.json').read_text())
suite=get_runner(settings)(verbosity=0).build_suite(labels)
def ids(s):
 for t in s:
  if hasattr(t,'__iter__'):yield from ids(t)
  else:yield t.id()
items=list(ids(suite));assert len(items)==len(set(items))
(P/'discovery.json').write_text(json.dumps({'labels':labels,'count':len(items),'ids':items,'global_corpus':'NOT RUN'},indent=2))
print('Explicit module02 labelled suite:',len(items),'unique tests')
