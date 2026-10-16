from pathlib import Path
import json,subprocess,sys
H=Path(__file__).resolve().parent;R=H.parents[2];py=str(R/'.venv/bin/python');labels=json.loads((H/'additional-security-recheck-labels.json').read_text());sys.exit(subprocess.call([py,str(H/'run_record.py'),'additional-security-recheck',py,str(H/'runtime.py'),'test',*labels],cwd=R))
