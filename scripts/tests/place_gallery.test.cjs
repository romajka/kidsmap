const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
function mount(reduced=false){
 const scrolling=[]; const thumbs=[0,1,2].map(i=>({offsetLeft:i*90,offsetWidth:80,classList:{toggle(){}},setAttribute(){},scrollIntoView:o=>scrolling.push(o),addEventListener(){}}));
 const strip={scrollLeft:0,clientWidth:180,scrollTo:o=>scrolling.push(o)};
 thumbs.forEach(t=>t.parentElement=strip);
 const prev={getAttribute:()=> 'Предыдущее фото'},next={getAttribute:()=> 'Следующее фото'};
 const elements={'[data-place-gallery-main]':{},'[data-place-gallery-prev]':prev,'[data-place-gallery-next]':next,'[data-place-gallery-current]':{},'.place-gallery__thumbs':strip};
 const gallery={querySelector:s=>elements[s],querySelectorAll:()=>thumbs};
 let options; const context={document:{querySelectorAll:()=>[gallery],body:{hasAttribute:()=>false}},window:{matchMedia:()=>({matches:reduced}),Swiper:function(el,opts){options=opts;opts.on.init({realIndex:0});}}};
 vm.runInNewContext(fs.readFileSync('static/js/place_gallery.js','utf8'),context);
 return {scrolling,options};
}
test('mounting gallery does not scroll the document or strip',()=>assert.equal(mount().scrolling.length,0));
test('reduced motion uses instant transitions',()=>assert.equal(mount(true).options.speed,0));
test('gallery navigation keeps server-localized accessible labels',()=>assert.equal(mount().options.a11y?.nextSlideMessage,'Следующее фото'));
test('changing a slide scrolls only its thumbnail strip',()=>{
 const state=mount();state.options.on.slideChange({realIndex:2});
 assert.equal(state.scrolling.length,1);assert.equal(state.scrolling[0].left,130);
 assert.equal(state.scrolling[0].block,undefined);
});
