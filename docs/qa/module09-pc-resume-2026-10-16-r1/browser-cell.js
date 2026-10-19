async (page) => {
  const cell = __CELL__, lang = '__LANG__', width = __WIDTH__;
  const origin = 'http://127.0.0.1:33261';
  const errors = [], consoleErrors = [], failed = [], posts = [];
  const onError = error => errors.push({name:error.name,message:error.message});
  const onConsole = message => { if (message.type() === 'error') consoleErrors.push(message.text()); };
  const onFailed = request => failed.push({url:request.url(),error:request.failure()?.errorText});
  const onResponse = response => { if (response.request().method() === 'POST') posts.push({status:response.status(),url:response.url()}); };
  await page.setViewportSize({width,height:width<768?844:900});
  await page.goto(`${origin}/qa/login/${cell}/`);
  const targetPath = new URL(page.url()).pathname.replace(/^\/(ru|en)\//,'/');
  const url = origin + (lang==='az'?'':`/${lang}`) + targetPath;
  await page.goto(url);
  const initialRating = await page.getByRole('combobox').inputValue();
  if (initialRating !== '4') throw new Error(`Fixture ${cell}: expected initial4, got ${initialRating}`);
  const b = await page.context().newPage();
  await b.setViewportSize({width,height:width<768?844:900});
  for (const p of [page,b]) {
    p.on('pageerror',onError); p.on('console',onConsole); p.on('requestfailed',onFailed); p.on('response',onResponse);
  }
  try {
    await b.goto(url);
    await b.getByRole('combobox').selectOption('2');
    await b.getByRole('textbox').fill('Unsaved draft B');
    await page.getByRole('combobox').selectOption('5');
    await page.getByRole('textbox').fill('Latest private candidate A');
    await Promise.all([page.waitForNavigation({waitUntil:'domcontentloaded'}),page.locator('form[data-review-edit] button').click()]);
    const before = await (await page.request.get(`${origin}/qa/state/${cell}/`)).json();
    await b.getByRole('textbox').focus();
    await b.keyboard.press('Tab');
    const focusedButton = await b.evaluate(()=>document.activeElement.tagName==='BUTTON');
    if (!focusedButton) throw new Error('Keyboard did not reach native submit');
    const [response] = await Promise.all([b.waitForNavigation({waitUntil:'domcontentloaded'}),b.keyboard.press('Enter')]);
    const after = await (await page.request.get(`${origin}/qa/state/${cell}/`)).json();
    const editor = await b.locator('form[data-review-edit]').count() > 0;
    const draft = editor && await b.locator('textarea[name=text]').inputValue() === 'Unsaved draft B';
    const navigation = await b.locator('header a,nav a').count() > 0;
    const checks = {
      initial_saved_rating_readback:initialRating==='4',
      actual_conflict_409:response.status()===409 && posts.some(p=>p.status===409),
      no_write_on_conflict:JSON.stringify(before)===JSON.stringify(after),
      candidate_and_public_preserved:after.candidate_a && after.candidate_rating===5 && after.public.average===4 && after.public.count===1 && !after.draft_b_saved,
      recovery_editor_retains_b:editor && draft,
      recovery_navigation_present:navigation
    };
    for (const key of ['actual_conflict_409','no_write_on_conflict','candidate_and_public_preserved']) {
      if (!checks[key]) throw new Error(`Invalid reproduction control ${key}: ${JSON.stringify(after)}`);
    }
    const png=`/mnt/c/kidsmap/.tmp/module09-pc-resume-2026-10-16-r1/png/conflict-${lang}-${width}.png`;
    await b.screenshot({path:png,fullPage:true});
    return {cell,lang,width,status:response.status(),checks,keyboard_submit:focusedButton,
      before,after,body:await b.locator('body').innerText(),pageerrors:errors,console_errors:consoleErrors,
      request_failed:failed,posts,png,browser:page.context().browser().version()};
  } finally {
    for (const p of [page,b]) {
      p.off('pageerror',onError);p.off('console',onConsole);p.off('requestfailed',onFailed);p.off('response',onResponse);
    }
    await b.close();
  }
}
