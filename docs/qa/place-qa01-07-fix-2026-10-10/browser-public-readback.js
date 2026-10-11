async (page) => {
  const rows=[];
  for(const language of ['ru','az','en']) {
    for(const width of [390,1440]) {
      await page.setViewportSize({width,height:900});
      await page.goto(`http://127.0.0.1:8840/${language}/place/2-keyfiyyetli-usaq-derneyi/`);await page.reload();
      const text=await page.locator('main').innerText();
      if(!text.includes('KMFIX İkinci təsdiqlənəcək məkan')||!text.includes('KMFIX Second mixed address 24')||!text.includes('24'))throw new Error('Public approved identity/price missing');
      await page.screenshot({path:`C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/public-${language}-${width}.png`});
      rows.push({language,width,approvedName:true,approvedAddress:true,amount24:true});
    }
  }
  return {checks:rows.length,rows};
}
