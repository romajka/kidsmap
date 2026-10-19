from pathlib import Path
Q=Path(__file__).resolve().parent
t=(Q/'flows-template.js').read_text();a=t.index('await a.goto(url);');b=t.index('await g.goto(url);',a);t=t[:a]+"let s=await state(a),h=s.typed[kind].heads.find(x=>x.user_id===F.actors.author.id);"+t[b:];a=t.index("try{await a.goto(base+'/ru/reviews/');");b=t.index('const s=await state(a);for',a);t=t[:a]+t[b:];t=t.replace("locator('main').innerText()","locator('.typed-reviews').innerText()")
(Q/'flows-complete-template.js').write_text(t)
