from pathlib import Path
O=Path(__file__).resolve().parent
s=(O/'browser-green-matrix.js').read_text()
s=s.replace("rows.push({id,role", "const layout=await alert.evaluate(e=>{const c=e.querySelector('.km-place-form-alert__content'),li=c.querySelector('.errorlist li'),a=c.querySelector('a'),cr=c.getBoundingClientRect(),lr=li.getBoundingClientRect(),ar=a.getBoundingClientRect();return{contentWidth:cr.width,messageWidth:lr.width,linkBelowMessage:ar.top>=lr.bottom-1,messageWithinContent:lr.left>=cr.left-1&&lr.right<=cr.right+1};});\n   rows.push({layout,id,role")
s=s.replace('checks:{a302:', 'checks:{readableMessage:layout.messageWidth>=100,recoveryBelowMessage:layout.linkBelowMessage,messageWithinContent:layout.messageWithinContent,a302:')
s=s.replace("'/png/green-'", "'/png/final-'")
(O/'browser-final-matrix.js').write_text(s)
s=s.replace("['content','super']", "['content']").replace("['az','ru','en']", "['ru']").replace('[360,390,768,1024,1280,1440]', '[390]').replace("['same','disjoint']", "['disjoint']").replace("'/png/final-'", "'/png/final-smoke-'")
(O/'browser-final-smoke.js').write_text(s)
print('Final matrix and distinct smoke created: 17 checks/case including three measured layout checks')
