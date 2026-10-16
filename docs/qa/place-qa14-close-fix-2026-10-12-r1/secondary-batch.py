import subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
for name in sys.argv[1:]:
 p=subprocess.run([str(ROOT/'.venv/bin/python'),str(HERE/'drive.py'),name,'qa14focus-native'],cwd=ROOT,capture_output=True,text=True)
 print(p.stdout,flush=True)
 if p.returncode:print('CLI exit',p.returncode,flush=True)
