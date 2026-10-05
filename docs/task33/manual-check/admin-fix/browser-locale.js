async page => {
 const rows=[];
 const expected={ru:['Главная','Сохранить','Авторские права'],en:['Home','Save','Copyright'],az:['Ana səhifə','Yadda saxla','Müəllif hüquqları']};
 for(const lang of ['ru','en','az']){
  await page.goto('http://127.0.0.1:8780/admin/catalog/organization/add/');
  await page.locator('.km-admin-header__lang-btn').click();
  await page.locator(`form.km-admin-lang-switch-form:has(input[name="language"][value="${lang}"]) button`).first().click();
  await page.waitForLoadState('networkidle');
  const home=(await page.locator('.breadcrumb a').first().innerText()).trim();
  const save=(await page.locator('button[name="_save"]').innerText()).replace(/[\uf000-\uf8ff]/g,'').trim();
  const copyright=(await page.locator('.main-footer strong').innerText()).trim();
  rows.push({lang,home,save,copyright,pass:home===expected[lang][0]&&save===expected[lang][1]&&copyright.startsWith(expected[lang][2])});
 }
 return {status:rows.every(r=>r.pass)?'PASS':'FAIL',rows};
}
