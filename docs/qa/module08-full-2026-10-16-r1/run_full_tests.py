import json,subprocess,sys
from pathlib import Path
h=Path(__file__).resolve().parent;r=h.parents[2]
a=[sys.executable,str(h/'run_command.py'),'full-backend',str(r/'.tmp'/h.name/'venv/bin/python'),str(h/'runtime.py'),'test',*json.loads((h/'test-labels.json').read_text())]
raise SystemExit(subprocess.run(a,cwd=r).returncode)
