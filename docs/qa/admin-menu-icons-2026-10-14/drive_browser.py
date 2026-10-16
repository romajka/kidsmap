import json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
process=subprocess.run(['playwright-cli','-s=admin-menu-icons-20261014','run-code','--filename',str(HERE/'browser.js')],capture_output=True,text=True,timeout=120)
output=process.stdout+process.stderr
(HERE/'browser.txt').write_text(output)
assert output.startswith('### Result\n'), 'See browser.txt'
result=json.JSONDecoder().raw_decode(output.split('\n',1)[1])[0]
(HERE/'browser-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result))
assert not result['failures'] and not result['errors'] and not result['network']
