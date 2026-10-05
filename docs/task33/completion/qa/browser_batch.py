"""Execute all four strict Chromium families against one frozen local source."""
import argparse,json,subprocess
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--stamp',required=True);args=parser.parse_args()
assert args.stamp.isalnum()
source=Path('/mnt/c/kidsmap/docs/task33/completion/qa')
root=Path('/root/task33-evidence')/('completion-browser-batch-'+args.stamp)
root.mkdir(exist_ok=False)
with (root/'sync.log').open('w') as log:
    subprocess.run(['bash',str(source/'browser_sync.sh')],stdout=log,stderr=subprocess.STDOUT,check=True)
results=[]
for family in ('targeted','r1','specialist','event'):
    with (root/(family+'.log')).open('w') as log:
        run=subprocess.run(['bash',str(source/'browser_run.sh'),family,args.stamp],stdout=log,stderr=subprocess.STDOUT)
    evidence=Path('/root/task33-evidence')/f'completion-browser-{family}-{args.stamp}'
    result={'family':family,'exit':run.returncode,'evidence':str(evidence)}
    if (evidence/'summary.json').exists():
        summary=json.loads((evidence/'summary.json').read_text())
        result.update({k:summary[k] for k in ('status','contexts','checks','passed_checks','event_counts','cleanup')})
    results.append(result);print(json.dumps(result),flush=True)
    (root/'results.json').write_text(json.dumps(results,indent=2)+'\n')
raise SystemExit(any(result['exit'] for result in results))
