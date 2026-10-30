const test = require('node:test');
const assert = require('node:assert/strict');
const {EventEmitter} = require('node:events');
const {feedbackWatch} = require('../e2e/place_addition/response_watch.cjs');
const origin = 'http://127.0.0.1:8898';
const payload = () => ({errors:{name_az:['Required']},readiness:{is_ready:false,items:[],sections:[],required_count:10,completed_count:0}});
function response(options = {}) {
  return {
    url: () => origin + (options.path || '/account/places/preview/'),
    status: () => options.status ?? 422,
    request: () => ({method: () => options.method || 'POST', postData: () => options.data ?? '_km_check_required=1'}),
    json: async () => {if(options.malformed)throw Error('Not JSON');return options.payload ?? payload();},
  };
}
test('accepts only real check-only validation shapes for unsaved and saved forms', async () => {
  const page = new EventEmitter(),watch = feedbackWatch(page,origin);
  page.emit('response',response());
  page.emit('response',response({path:'/ru/account/places/42/preview/',data:'Content-Disposition: form-data; name="_km_check_required"\r\n\r\n1\r\n'}));
  assert.equal(await watch.verify(),2);
});
test('staff preview uses the same strict check-only validation contract', async () => {
  const page = new EventEmitter(),watch = feedbackWatch(page,origin);
  page.emit('response',response({path:'/admin/editor/places/preview/'}));
  page.emit('response',response({path:'/admin/editor/places/42/preview/'}));
  assert.equal(await watch.verify(),2);
});
test('unexpected HTTP errors and invalid validation replies still fail the browser scenario', async () => {
  const invalid = [
    {status:500},{status:404},{method:'GET'},{path:'/account/places/save/'},{data:'name_az=Somewhere'},
    {malformed:true},{payload:{errors:{},readiness:payload().readiness}},
    {payload:{errors:{name_az:['Required']},readiness:{...payload().readiness,is_ready:true}}},
    {payload:{errors:{name_az:['Required']},readiness:{...payload().readiness,completed_count:11}}},
  ];
  for(const options of invalid){
    const page = new EventEmitter(),watch = feedbackWatch(page,origin);
    page.emit('response',response(options));
    await assert.rejects(watch.verify(),/Only contracted incomplete check-only 422 responses are expected/);
  }
});
test('successful responses are not reported as validation failures', async () => {
  const page = new EventEmitter(),watch = feedbackWatch(page,origin);
  page.emit('response',response({status:200}));
  assert.equal(await watch.verify(),0);
});
test('JavaScript page errors remain available to the browser assertion', async () => {
  const page = new EventEmitter(),watch = feedbackWatch(page,origin);
  page.emit('pageerror',Error('synthetic page error'));
  assert.deepEqual(watch.errors,['synthetic page error']);
});
