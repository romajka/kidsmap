import subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap')
for mode in ['filled','empty','error','partial']:
    p=subprocess.run(['python3',str(R/'.tmp/m12-native-case.py'),mode,'r1'])
    if p.returncode:raise SystemExit(p.returncode)
