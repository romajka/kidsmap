async (page) => {
 const o='http://127.0.0.1:33348',rows=[];
 for(const role of ['guest','author']){
  await page.goto(o+'/qa/login/'+role+'/');
  const r=await page.request.get(o+'/az/reviews/activity/target/1/',{maxRedirects:0});
  const response=await page.goto(o+'/az/reviews/activity/target/1/');
  rows.push({id:role+'-legacy-az',checks:{permanent301:r.status()===301,canonical_location:r.headers().location==='/reviews/activity/target/1/',native200:response.status()===200,canonical_url:page.url()===o+'/reviews/activity/target/1/',human_heading:(await page.locator('h1').textContent()).trim()==='Rəylər: Uydurma məşğələ AZ'},facts:{status:r.status(),location:r.headers().location,url:page.url()}});
 }
 return {rows};
}
