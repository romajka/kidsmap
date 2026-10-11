async (page) => {
  const rows=[];
  for (const [language,title,natures] of [['ru','Причина отказа',['Бизнес','Общественное место']],['az','İmtina səbəbi',['Biznes','İctimai məkan']],['en','Reason for rejection',['Business','Public space']]]) {
    await page.goto(`http://127.0.0.1:8840/${language}/account/places/3/edit/`);
    await page.reload();
    for (const width of [390,768,1024,1280,1440]) {
      await page.setViewportSize({width,height:900});
      const result=await page.evaluate(()=> {
        const note=document.querySelector('[data-place-review-note]'),rect=note.getBoundingClientRect();
        return {title:note.querySelector('h2').textContent,note:note.querySelector('p').textContent,
          scriptCount:note.querySelectorAll('script').length,executed:!!window.qaUnexpected,left:rect.left,right:rect.right,
          wrap:getComputedStyle(note.querySelector('p')).whiteSpace,
          nature:[...document.querySelector('[name=nature]').options].map(x=>[x.value,x.textContent])};
      });
      if(result.title!==title||!result.note.includes('<script>window.qaUnexpected=true</script>')||result.executed||result.scriptCount||result.right>width+1||result.left<0||result.wrap!=='pre-wrap')throw new Error('Rejected feedback rendering failed');
      if(JSON.stringify(result.nature)!==JSON.stringify([['business',natures[0]],['public_space',natures[1]]]))throw new Error('Localized nature choices failed');
      await page.screenshot({path:`C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/rejection-${language}-${width}.png`});
      rows.push({language,width,title:result.title,escapedLiteral:true,newlinesPreserved:true,wrap:true,nature:result.nature});
    }
  }
  return {checks:rows.length,rows};
}
