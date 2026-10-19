import runpy,sys
from pathlib import Path
Q=Path(__file__).resolve().parent
sys.argv=[str(Q/'runtime.py'),'validate-template-only']
runpy.run_path(str(Q/'runtime.py'),run_name='__main__')
from django.template import Template
p=Path('/mnt/c/kidsmap/docs/qa/social-qa06-recheck-2026-10-17-pc-r1/candidate-site_reviews.html')
Template(p.read_text(encoding='utf-8'))
print('Candidate Django template parsed; no render/browser execution/application patch')
