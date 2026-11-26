// Real shared-template controller in jsdom; only HTTP is substituted.
// Run: node --test scripts/test_design_completion_feedback.cjs
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {JSDOM} = require(process.env.KIDSMAP_JSDOM || '../.tmp/phone-dom/node_modules/jsdom');
const loadPublicActions = require('./tests/helpers/public_actions.cjs');
const settle = () => new Promise(resolve => setImmediate(resolve));
function setup(language='ru', fetch) {
  const dom = new JSDOM(`<html lang="${language}"><body><div data-toast-stack aria-live="polite"></div>
  <article class="place-card"><div class="card-media"><a class="card-media-link" href="/place/7/" aria-label="A real place">
  <div class="card-media-blur-bg"></div><img data-photo-fallback src="/missing.webp" data-placeholder-text="Photo coming soon">
  <template data-card-image-placeholder><div class="image-placeholder" data-category-placeholder role="img" aria-label="Photo coming soon"><span class="image-placeholder-icon" aria-hidden="true"><svg data-real-category="sport" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"></circle></svg></span><span class="image-placeholder-text">Photo coming soon</span></div></template>
  </a><div class="card-price-pill">80 ₼</div></div>
  <form method="post" action="/like/7/" data-like-form><input name="csrfmiddlewaretoken" value="test"><button type="submit" class="like-btn" aria-pressed="false" data-favorite-add-label="Add" data-favorite-remove-label="Remove">Heart</button><span class="like-count">0</span></form></article>
  </body></html>`, {url:'https://kidsmap.example/',runScripts:'dangerously'});
  dom.window.fetch = fetch;
  loadPublicActions(dom.window);
  return dom;
}
test('failed card image keeps actual category placeholder, navigation and price', () => {
  const dom = setup(); const d = dom.window.document;
  d.querySelector('img').dispatchEvent(new dom.window.Event('error'));
  const placeholder = d.querySelector('.card-media-link > .image-placeholder');
  assert.ok(placeholder?.querySelector('[data-real-category="sport"]'));
  assert.equal(placeholder.getAttribute('role'), 'img');
  assert.equal(d.querySelector('.card-media-link').getAttribute('href'), '/place/7/');
  assert.equal(d.querySelector('.card-price-pill').textContent, '80 ₼');
  assert.equal(d.querySelector('.card-media-blur-bg, .card-media-link > img'), null);
  assert.equal(d.querySelectorAll('.card-media-link > .image-placeholder').length, 1);
  dom.window.close();
});
for (const [language, added, removed] of [['ru','Добавлено в избранное','Удалено из избранного'],['az','Seçilmişlərə əlavə edildi','Seçilmişlərdən silindi'],['en','Added to favorites','Removed from favorites']]) {
  test(`favorite confirms committed state in ${language} without removing the card`, async () => {
    let liked=false; const dom=setup(language, async()=>({ok:true,json:async()=>({ok:true,liked:liked=!liked,likes_count:liked?1:0})}));
    const d=dom.window.document, form=d.querySelector('form'), button=d.querySelector('.like-btn');
    const submit=()=>form.dispatchEvent(new dom.window.SubmitEvent('submit',{bubbles:true,cancelable:true,submitter:button}));
    button.focus(); submit(); assert.equal(button.disabled,true); await settle();
    assert.equal(button.getAttribute('aria-pressed'),'true'); assert.equal(button.getAttribute('aria-label'),'Remove');
    assert.equal(d.querySelector('.toast-message').textContent,added); assert.equal(d.activeElement,button);
    submit(); await settle();
    assert.equal(button.getAttribute('aria-pressed'),'false');
    assert.equal([...d.querySelectorAll('.toast-message')].at(-1).textContent,removed);
    assert.ok(d.querySelector('.place-card')); dom.window.close();
  });
}
test('failed favorite request keeps retryable state and never announces success', async()=>{
  const dom=setup('en',async()=>({ok:false,status:503,json:async()=>({message:'Unavailable'})}));
  const d=dom.window.document, button=d.querySelector('.like-btn');
  d.querySelector('form').dispatchEvent(new dom.window.SubmitEvent('submit',{bubbles:true,cancelable:true,submitter:button})); await settle();
  assert.equal(button.getAttribute('aria-pressed'),'false'); assert.equal(button.disabled,false);
  assert.equal(d.querySelector('.toast-message').textContent,'Unavailable'); dom.window.close();
});
