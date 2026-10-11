from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'final-proof.js').read_text(encoding='utf-8').split("for(const lang of ['ru','az','en'])")[0]
s=s.replace("u=>u.searchParams.get('page')==='2'", "u=>u.searchParams.get('page')==='2',{waitUntil:'domcontentloaded'}")
s+="for(const c of contexts)await c.close();return{rows,utc:new Date().toISOString()};\n}"
(P/'pagination-final.js').write_text(s,encoding='utf-8')
