const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { JSDOM } = require(process.env.KIDSMAP_JSDOM || 'jsdom');
const source = fs.readFileSync(require('node:path').join(__dirname, '../../static/js/review_submission.js'), 'utf8');
function setup({native = true, selected = '', responses = []} = {}) {
  const rating = native ? `<fieldset data-review-stars><legend>Rating</legend>${[1,2,3,4,5].map(n=>`<input type="radio" name="rating" value="${n}" data-review-rating-input ${String(n)===selected?'checked':''}>`).join('')}</fieldset>` : `<input type="hidden" name="rating" data-review-rating-input value="${selected}">`;
  const dom = new JSDOM(`<section><div data-review-feedback data-rating-required="Choose a rating" data-network-error="Retry; text kept" data-server-error="Server error" data-sending="Sending"><div data-review-live hidden tabindex="-1"><svg><path data-review-icon></path></svg><strong data-review-title></strong><span data-review-message></span></div></div><a data-review-login href="/auth/login/?next=/specialists/demo/" target="_blank" hidden>Sign in in a new tab</a><div data-review-composer><form action="/specialists/8/review/" data-review-submission>${rating}<textarea name="text">Private review draft</textarea><button type="submit">Send</button></form></div></section>`, {url:'http://localhost/',runScripts:'outside-only'});
  const w=dom.window;w.HTMLElement.prototype.scrollIntoView=function(){};
  const calls=[];
  w.fetch=async(url,options)=>{calls.push({url,rating:options.body.get('rating'),text:options.body.get('text')});calls[calls.length-1].csrf=options.body.get('csrfmiddlewaretoken');const r=responses.shift()||{ok:true,status:200,body:{ok:true,message:'Received'}};if(r instanceof Error)throw r;return {...r,json:async()=>r.body};};
  w.eval(source);
  const form=w.document.querySelector('form');
  return {w,doc:w.document,calls,form,submit:async()=>{form.dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await new Promise(r=>setTimeout(r,5));},close:()=>dom.window.close()};
}
test('native rating must be selected before a request is sent', async()=>{
  const t=setup();await t.submit();assert.equal(t.calls.length,0);assert.equal(t.doc.querySelector('[data-review-message]').textContent,'Choose a rating');assert.equal(t.doc.activeElement,t.form.querySelector('input[type=radio]'));t.close();
});
test('selected native rating is sent and success hides composer',async()=>{
  const t=setup({selected:'4'});await t.submit();assert.deepEqual(t.calls[0],{url:'http://localhost/specialists/8/review/',rating:'4',text:'Private review draft',csrf:null});assert.equal(t.doc.querySelector('[data-review-composer]').hidden,true);t.close();
});
test('expired login exposes safe template login link without clearing the draft',async()=>{
  const t=setup({selected:'4',responses:[{ok:false,status:401,body:{ok:false,auth_required:true,redirect_url:'https://untrusted.invalid/',message:'Sign in'}}]});await t.submit();const a=t.doc.querySelector('[data-review-login]');assert.equal(a.hidden,false);assert.equal(a.origin,'http://localhost');assert.equal(t.form.elements.text.value,'Private review draft');assert.equal(t.form.querySelector('button').disabled,false);t.close();
});
test('network failure preserves input and allows a successful retry',async()=>{
  const t=setup({selected:'3',responses:[new Error('offline')]});await t.submit();assert.equal(t.form.elements.text.value,'Private review draft');assert.equal(t.form.querySelector('button').disabled,false);await t.submit();assert.equal(t.calls.length,2);assert.equal(t.doc.querySelector('[data-review-composer]').hidden,true);t.close();
});
test('existing hidden rating controls retain their validation and submission contract',async()=>{
  const t=setup({native:false});await t.submit();assert.equal(t.calls.length,0);t.form.querySelector('[data-review-rating-input]').value='5';await t.submit();assert.equal(t.calls[0].rating,'5');assert.equal(t.doc.querySelector('[data-review-composer]').hidden,true);t.close();
});

test('retry after another-tab login uses the current CSRF cookie without losing the review',async()=>{
 const t=setup({selected:'4'});const input=t.doc.createElement('input');input.type='hidden';input.name='csrfmiddlewaretoken';input.value='old-token';t.form.append(input);t.doc.cookie='csrftoken=new-token; path=/';await t.submit();assert.equal(t.calls[0].csrf,'new-token');assert.equal(t.calls[0].text,'Private review draft');t.close();
});
