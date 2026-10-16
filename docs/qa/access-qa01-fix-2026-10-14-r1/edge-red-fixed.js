async (page) => {
 const rows=[],base='http://127.0.0.1:57059/';
 const record=(name,ok,detail)=>rows.push({lang:'ru',width:390,name,status:ok?'PASS':'FAIL',detail});
 const active=()=>page.evaluate(()=>({id:document.activeElement.id,inModal:document.getElementById('resetPasswordModal').contains(document.activeElement),opener:document.activeElement.matches('[data-open-reset-modal]')}));
 await page.context().clearCookies();await page.setViewportSize({width:390,height:900});await page.goto(base+'ru/auth/login/');
 const opener=page.locator('[data-open-reset-modal]');
 await opener.click();await page.keyboard.press('Escape');await page.waitForTimeout(150);
 record('Rapid close never refocuses hidden dialog',(await active()).opener,await active());
 await page.waitForTimeout(180);await opener.click();await page.waitForTimeout(100);
 await page.evaluate(()=>{const b=document.createElement('button');b.id='qaDynamicBackground';b.textContent='Synthetic background';document.body.appendChild(b);b.focus()});
 record('New background control cannot take focus',(await active()).inModal,await active());
 await page.keyboard.press('Escape');await page.waitForTimeout(300);
 await page.evaluate(()=>{const b=document.getElementById('qaDynamicBackground');if(b)b.remove()});
 await page.goto(base+'ru/auth/login/');await opener.click();await page.waitForTimeout(100);
 await page.locator('#resetModalEmailInput').fill('unknown@example.invalid');
 await page.route('**/auth/password-reset/',async route=>{await new Promise(r=>setTimeout(r,600));await route.continue()});
 const response=page.waitForResponse(r=>r.url().endsWith('/auth/password-reset/')&&r.request().method()==='POST');
 await page.locator('#resetModalSubmitBtn').click();await page.keyboard.press('Escape');await response;await page.waitForTimeout(200);
 record('Late success after close keeps opener',(await active()).opener,await active());
 await page.unroute('**/auth/password-reset/');
 await page.goto(base+'ru/auth/login/');return {rows,simulation:'late transport delay and dynamic background fixture SIMULATED; real app focus and real reset endpoint'};
}
