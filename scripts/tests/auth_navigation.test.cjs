const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function fixture(values, hash) {
  const forms = values.map(value => ({
    input: {value}, handlers: {},
    hasAttribute() { return true; },
    querySelector() { return this.input; },
    addEventListener(name, fn) { this.handlers[name] = fn; },
  }));
  const window = {location: {origin: 'https://kidsmap.az', hash}};
  vm.runInNewContext(fs.readFileSync('static/js/auth_navigation.js', 'utf8'), {
    document: {cookie: '', querySelectorAll: () => forms}, window, URL,
  });
  return {forms, window};
}

test('desktop and mobile forms preserve their own query and current fragment on submission', () => {
  const {forms, window} = fixture(['/catalog/?category=sport', '/en/catalog/?page=2'], '#map');
  forms.forEach(form => form.handlers.submit());
  assert.equal(forms[0].input.value, '/catalog/?category=sport#map');
  assert.equal(forms[1].input.value, '/en/catalog/?page=2#map');
  window.location.hash = '#reviews';
  forms[0].handlers.submit();
  assert.equal(forms[0].input.value, '/catalog/?category=sport#reviews');
  assert.equal(forms[1].input.value, '/en/catalog/?page=2#map');
});

test('empty auth-loop return and foreign targets are not rewritten', () => {
  const {forms} = fixture(['', 'https://other.example/path'], '#map');
  forms.forEach(form => form.handlers.submit());
  assert.equal(forms[0].input.value, '');
  assert.equal(forms[1].input.value, 'https://other.example/path');
});

test('removed fragment is cleared on next submit', () => {
  const {forms} = fixture(['/catalog/#old'], '');
  forms[0].handlers.submit();
  assert.equal(forms[0].input.value, '/catalog/');
});

test('all navigation forms refresh a rotated CSRF cookie without changing unrelated return targets', () => {
  const forms = [true, false, false].map(preserveHash => ({
    input: {value: '/specialists/demo/#reviews'}, csrf: {value: 'old-token'}, handlers: {},
    hasAttribute() { return preserveHash; },
    querySelector(selector) { return selector.includes('csrfmiddlewaretoken') ? this.csrf : this.input; },
    addEventListener(name, fn) { this.handlers[name] = fn; },
  }));
  const document = {cookie: 'csrftoken=fresh-token; theme=light', querySelectorAll: () => forms};
  vm.runInNewContext(fs.readFileSync('static/js/auth_navigation.js', 'utf8'), {
    document, window: {location: {origin: 'https://kidsmap.az', hash: '#map'}}, URL,
  });
  forms.forEach(form => form.handlers.submit());
  assert.deepEqual(forms.map(form => form.csrf.value), ['fresh-token', 'fresh-token', 'fresh-token']);
  assert.equal(forms[0].input.value, '/specialists/demo/#map');
  assert.equal(forms[1].input.value, '/specialists/demo/#reviews');
  assert.equal(forms[2].input.value, '/specialists/demo/#reviews');
  document.cookie = 'csrftoken=another-token';
  forms[2].handlers.submit();
  assert.equal(forms[2].csrf.value, 'another-token');
});
