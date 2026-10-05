"""Retain synthetic QA results and match each historical problem, without raw data."""
import argparse
import hashlib
import json
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('stamp')
args=parser.parse_args()
source=Path('/root/task33-evidence')/('completion-'+args.stamp)
root=Path('/mnt/c/kidsmap/docs/task33/completion')
suite=json.loads((source/'suite-results.json').read_text())
run=json.loads((source/'run.json').read_text())
manifest=json.loads((source/'source.json').read_text())
isolation=json.loads((source/'isolation.json').read_text())
report={'stamp':args.stamp, 'raw_evidence':str(source), 'suite':suite,
    'run':{key:run.get(key) for key in ('status','child_exit','cleanup','run_root_removed','socket_root_removed')},
    'isolation':{key:isolation.get(key) for key in ('postgresql','django','python','network_guard','libpq_guard','external_credentials_present')},
    'source_manifest_sha256':hashlib.sha256((source/'source.json').read_bytes()).hexdigest(),
    'source_count':len(manifest['files']), 'frozen_source_changed':manifest['frozen_source_changed'],
    'production':'NOT_CONTACTED'}
(root/'runs').mkdir(exist_ok=True)
(root/'runs'/f'{args.stamp}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'report':str(root/'runs'/f'{args.stamp}.json'),'tests':suite['tests_run'],
    'failures':suite['failures'],'errors':suite['errors'],'cleanup':run['cleanup']}))
