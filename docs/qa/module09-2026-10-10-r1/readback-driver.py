from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'readback.js').read_text(encoding='utf-8').split("await p.goto(base+'/ru/reviews/');const sf=")[0]
s+="await c.close();return{rows,utc:new Date().toISOString()};\n}"
(P/'readback-final.js').write_text(s,encoding='utf-8')
