from pathlib import Path
Q=Path(__file__).resolve().parent
t=(Q/'favorites-notifications-template.js').read_text();a=t.index("try{\nawait a.goto(base+'/ru/account/notifications/');");t=t[:a]+t[t.index('const s=await state(o);for',a):];t=t.replace("base+'/ru/places/'","base+'/ru/catalog/'")
(Q/'favorites-finish-template.js').write_text(t)
