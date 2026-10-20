const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {test} = require('node:test');

// The map provider mounts after the hero form is usable. Rebinding must update
// the live destination without keeping two submit handlers or the old callback.
test('late provider binding keeps one submit handler and uses the new provider', () => {
  const source = fs.readFileSync('static/js/home_map.js', 'utf8');
  const form = new EventTarget();
  form.dataset = {};
  form.querySelector = () => null;
  const applied = [];
  const context = {
    document:{querySelector:()=>form},
    getDistrictOptions:()=>[], getAgeInput:()=>null, getAgeButtons:()=>[],
    initHomeSearchAutocomplete:()=>{}, scrollToMap:()=>{},
  };
  vm.createContext(context);
  vm.runInContext(source.slice(source.indexOf('  function bindFilterListeners('),
    source.indexOf('  function mountGoogleMap(')), context);
  context.bindFilterListeners(()=>applied.push('early'));
  form.dispatchEvent(new Event('submit', {cancelable:true}));
  context.bindFilterListeners(()=>applied.push('provider'));
  form.dispatchEvent(new Event('submit', {cancelable:true}));
  assert.deepEqual(applied, ['early', 'provider']);
});
