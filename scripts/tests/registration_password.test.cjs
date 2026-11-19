const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { JSDOM } = require(process.env.KIDSMAP_JSDOM || '../../.tmp/phone-dom/node_modules/jsdom');

test('registration accepts lowercase passphrases and catches short, numeric or mismatched passwords', (t) => {
  const dom = new JSDOM(`<form class="register-form">
    <label class="register-field"><input type="password" name="password1"></label>
    <label class="register-field"><input type="password" name="password2"></label>
    <div data-register-progress></div>
  </form><script type="application/json" id="register-copy">{}</script>`, { runScripts: 'outside-only' });
  t.after(() => dom.window.close());
  const { document, Event } = dom.window;
  dom.window.HTMLElement.prototype.scrollIntoView = () => {};
  const template = fs.readFileSync('src/catalog/templates/auth/register.html', 'utf8');
  const scripts = JSDOM.fragment(template).querySelectorAll('script:not([type]):not([src])');
  for (const script of scripts) dom.window.eval(script.textContent);

  const form = document.querySelector('form');
  function canSubmit(password, confirmation = password) {
    form.elements.password1.value = password;
    form.elements.password2.value = confirmation;
    return form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  }

  assert.equal(canSubmit('orchard-river-lantern-velvet'), true, 'valid passphrase');
  assert.equal(canSubmit('short'), false, 'minimum length');
  assert.equal(canSubmit('1234567890'), false, 'entirely numeric');
  assert.equal(canSubmit('١٢٣٤٥٦٧٨'), false, 'Unicode decimal digits are numeric too');
  assert.equal(canSubmit('orchard-river-lantern-velvet', 'different'), false, 'confirmation must match');
});
