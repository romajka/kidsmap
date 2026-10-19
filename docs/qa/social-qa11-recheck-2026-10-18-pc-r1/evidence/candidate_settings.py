from qa_settings import *
from copy import deepcopy
TEMPLATES=deepcopy(TEMPLATES)
TEMPLATES[0]['DIRS']=[QA_ROOT/'candidate/templates']+list(TEMPLATES[0]['DIRS'])
STATICFILES_DIRS=[QA_ROOT/'candidate/static']+list(STATICFILES_DIRS)
