const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../../../..');
const {JSDOM}=require(path.join(root,'.tmp/phone-dom/node_modules/jsdom'));
const source=fs.readFileSync(path.join(root,'static/js/place_phone_reveal.js'),'utf8');
const payload={phones:[{number:'+994501234567',href:'tel:+994501234567'}],whatsapp:'https://wa.me/994501234567'};
const settle=()=>new Promise(r=>setImmediate(r));
(async()=>{
  const results=[];
  for(const card of [false,true]){
    const dom=new JSDOM(`<html lang="ru"><body><div data-phone-config data-phone-endpoint="/api/places/0/phones/"><input name="csrfmiddlewaretoken" value="synthetic"></div><div data-phone-status role="status"></div><button data-phone-reveal="7" ${card?'data-phone-card="1"':''}>Показать</button><button data-phone-reveal="7" data-phone-whatsapp="1">WhatsApp</button></body></html>`,{url:'https://kidsmap.example/',runScripts:'outside-only'});
    let calls=0;
    dom.window.fetch=async(url,options)=>{calls++;assert.equal(url,'/api/places/7/phones/');assert.equal(options.method,'POST');assert.equal(options.headers['X-CSRFToken'],'synthetic');return{ok:true,json:async()=>payload};};
    dom.window.eval(source);const d=dom.window.document,b=d.querySelector('button');
    assert.equal(calls,0);b.focus();b.click();assert.equal(b.disabled,true);await settle();
    const a=d.querySelector('a');assert.equal(a.href,payload.phones[0].href);assert.equal(d.activeElement,a);
    assert.equal(a.classList.contains('km-phone-control--revealed'),card);
    assert.equal(Boolean(d.querySelector('.km-phone-group--revealed')),!card);
    const whatsapp=d.querySelectorAll('a')[1];assert.equal(whatsapp.href,payload.whatsapp);assert.equal(whatsapp.rel,'noopener noreferrer');
    const popup=d.createElement('div');popup.innerHTML=dom.window.kidsMapPhoneButton(7);d.body.append(popup);popup.querySelector('button').click();await settle();
    assert.equal(calls,1);assert.equal(popup.querySelector('a').href,payload.phones[0].href);assert.ok(popup.querySelector('.km-phone-copy-btn'));
    results.push({case:card?'compact_card':'generic_detail_and_map','status':'PASS','requests':calls,'correct_tel_whatsapp_focus_and_cache':true,'legacy_marker_on_phone_anchor':card});dom.window.close();
  }
  const out={status:'PASS_CAUSAL_PRESENTATION_PROBE',checks:results,original_test_unchanged:true,scope:'Mocked jsdom causal diagnosis only, not rendered browser',reason:'Old generic fixture expects compact-card CSS marker on the phone anchor; generic detail/map now wrap a call link and copy button. Phone URL/focus/cache remain correct.'};
  fs.writeFileSync(path.join(root,'docs/task33/final-audit/javascript-phone-diagnostic.json'),JSON.stringify(out,null,2)+'\n');
  const prior=JSON.parse(fs.readFileSync(path.join(root,'docs/task33/final-audit/javascript-results.json'),'utf8'));
  const raw=fs.readFileSync(prior.raw_evidence,'utf8');prior.counts=Object.fromEntries([...raw.matchAll(/^(?:#|ℹ) (tests|pass|fail|skipped|cancelled) (\d+)$/gm)].map(m=>[m[1],Number(m[2])]));
  prior.classification={failed_assertion:'scripts/test_phone_reveal.cjs:38',category:'LEGACY_PRESENTATION_MARKER_EXPECTATION',causal_evidence:'javascript-phone-diagnostic.json',original_assertion_preserved:true};
  fs.writeFileSync(path.join(root,'docs/task33/final-audit/javascript-results.json'),JSON.stringify(prior,null,2)+'\n');
  console.log(JSON.stringify({status:out.status,cases:results.length,original:prior.counts}));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
