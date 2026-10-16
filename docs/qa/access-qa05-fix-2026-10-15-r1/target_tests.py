import json,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];py=str(R/'.venv/bin/python');labels=json.loads((H/'target-tests.json').read_text())
sys.exit(subprocess.call([py,str(H/'run_record.py'),'target-tests',py,str(H/'runtime.py'),'test',*labels],cwd=R))
