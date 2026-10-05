"""Export actual clock causal observations without DOM/private records."""
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]);text=(root/'result-cli.txt').read_text();raw=text.split('### Result',1)[1].split('###',1)[0].strip();data=json.loads(raw)
run=json.loads((root/'launcher/run.json').read_text())
result={'stage':26,'execution_identity':'/root/stage26_browser','kind':'ACTUAL_UTC_CLOCK_CAUSAL','facts':data['facts'],'expected':data['expected'],'pastRejected':data['pastRejected'],'launcher_status':run['status'],'cleanup':run['cleanup'],'evidence':str(root),'matrix_sha256':hashlib.sha256((root/'matrix.js').read_bytes()).hexdigest(),'source_manifest_sha256':hashlib.sha256((root/'source-sha256.json').read_bytes()).hexdigest(),'external_transport':'CDNs stubbed','post_run':False}
if len(sys.argv)>2:Path(sys.argv[2]).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
