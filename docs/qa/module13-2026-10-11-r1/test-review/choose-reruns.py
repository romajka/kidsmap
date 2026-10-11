"""Choose failed existing methods by actual trace; no skips or assertion changes."""
import collections,json
from pathlib import Path
P=Path(__file__).resolve().parent
archive=P/'full-runner-at-launch.py'
if not archive.exists():
    original=(P/'full-suites.py').read_text()
    original=original.replace("sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')\n",'').replace("sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')\n",'')
    archive.write_text(original,encoding='utf-8')
rows=[json.loads(s) for s in (P/'full-observations.jsonl').read_text().splitlines()]
by_method=collections.defaultdict(list)
for row in rows:by_method[row['id'].split(' (',1)[0]].append(row)
def category(items):
    errors='\n'.join(x.get('traceback','') for x in items)
    if any(x['status']=='SKIP' for x in items):return 'SKIP'
    if not any(x['status'] in ('FAIL','ERROR','SUBTEST_FAIL') for x in items):return 'PASS'
    if any(x in errors for x in ('TASK33_QA_ROOT','requires QA04','QA04 isolation markers','No module named \'guard\'','socket_path','test_qa_stage04')):return 'ENVIRONMENT_GUARD_NOT_RUN'
    if 'UnicodeEncodeError' in errors:return 'ENVIRONMENT_ENCODING_RERUN'
    if 'PermissionError' in errors and 'doCleanups' in errors:return 'ENVIRONMENT_CLEANUP_ERROR'
    if 'FileNotFoundError' in errors and "'/tmp" in errors:return 'ENVIRONMENT_POSIX_PATH_NOT_RUN'
    return 'FAILED_BASELINE_PENDING'
group={k:category(v) for k,v in by_method.items()}
baseline=sorted(k for k,v in group.items() if v=='FAILED_BASELINE_PENDING')
target=sorted(k for k,v in group.items() if v=='ENVIRONMENT_ENCODING_RERUN')
(P/'baseline-labels.json').write_text(json.dumps(baseline,indent=2))
(P/'target-labels.json').write_text(json.dumps(target,indent=2))
(P/'initial-classification.json').write_text(json.dumps({'by_method':group,'counts':dict(collections.Counter(group.values())),'baseline_labels':baseline,'utf8_rerun_labels':target},indent=2))
print(json.dumps({'counts':dict(collections.Counter(group.values())),'baseline_labels':baseline,'utf8_rerun_labels':target},indent=2))
