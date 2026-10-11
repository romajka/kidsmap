import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
failures = 0
for role, lang in [('guest', 'az'), ('guest', 'en'), ('owner', 'ru'), ('owner', 'az'), ('owner', 'en'), ('admin', 'ru'), ('admin', 'az'), ('admin', 'en')]:
    print(f'RUN {role}/{lang}', flush=True)
    proc = subprocess.run([sys.executable, str(HERE / 'drive.py'), 'matrix.js', role, lang], cwd=REPO, text=True, encoding='utf-8', errors='replace', capture_output=True)
    print(proc.stdout[:5500], flush=True)
    if proc.stderr:
        print(proc.stderr[:500], flush=True)
    failures += proc.returncode != 0
print(f'Completed 8 batches; CLI failures={failures}', flush=True)
sys.exit(1 if failures else 0)
