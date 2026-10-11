from pathlib import Path
P=Path(__file__).resolve().parent
t=(P.parent/'module13-2026-10-11-r1/mixed-price.js').read_text(encoding='utf-8')
t=t.replace('__QA13_COMMON__','__QA01R_COMMON__').replace('QA13','QA01R')
(P/'mixed-price.js').write_text(t,encoding='utf-8')
