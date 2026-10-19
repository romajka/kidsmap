import json,subprocess
from datetime import datetime
from pathlib import Path
Q=Path('/mnt/c/kidsmap/.tmp/social09-pc-plan-r1');d=json.loads(subprocess.check_output(['docker','inspect','m09s04-fix-r1-app']))[0];s=d['State'];info={'id':d['Id'],'name':d['Name'],'status':s['Status'],'exit_code':s['ExitCode'],'oom_killed':s['OOMKilled'],'started':s['StartedAt'],'finished':s['FinishedAt'],'command':d['Config']['Cmd']};print(json.dumps(info))
(Q/'foreign-container-state.json').write_text(json.dumps(info,indent=2))
