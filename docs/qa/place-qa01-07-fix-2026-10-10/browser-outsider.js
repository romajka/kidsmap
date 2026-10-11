async (page) => {
  const response=await page.goto('http://127.0.0.1:8840/en/account/places/3/edit/');
  const result={status:response.status(),ownerFormCount:await page.locator('[data-permanent-place-form]').count(),reasonCount:await page.locator('[data-place-review-note]').count()};
  if(result.ownerFormCount||result.reasonCount)throw new Error('Outsider can read owner form');
  return result;
}
