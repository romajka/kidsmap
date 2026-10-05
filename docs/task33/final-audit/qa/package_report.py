"""Package the portable report and safe evidence, excluding execution tools."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
assert json.loads((ROOT/'closure.json').read_text())['status']=='AUDIT_COMPLETE_WITH_FINDINGS'
dest=ROOT/'KidsMap-28-audit-2026-10-04.zip'
files=sorted(p for p in ROOT.rglob('*')if p.is_file() and p.suffix.lower()in{'.html','.md','.json','.png'} and not any(part in {'qa','report-preview'}for part in p.relative_to(ROOT).parts) and p.name!='package.json')
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
    z.writestr('START-HERE.txt','KidsMap: audit of 28 stages, 4 October 2026.\nExtract the entire ZIP into one folder, then open report.html.\nScreenshots and evidence are local; no internet required.\nREPORT.md is the Markdown alternative; REQUIREMENTS.md contains all 306 requirements.\nApplication was not changed; production was not contacted.\n')
    for path in files:z.write(path,path.relative_to(ROOT).as_posix())
with zipfile.ZipFile(dest)as z:assert z.testzip()is None
record={'status':'PASS','file':dest.name,'files':len(files)+1,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'zip_crc':'PASS','excludes':['qa execution helpers','report preview screenshots','raw logs','credentials','production data']}
(ROOT/'package.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8');print(json.dumps(record))
