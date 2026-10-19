/* Candidate outside application: exercise actual notification code with controlled DOM/timers. */
const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
class Element{
 constructor(){this.children=[];this.parentNode=null;this.className='';this.attrs={};this.classList={contains:n=>this.className.split(' ').includes(n),add:n=>{if(!this.classList.contains(n))this.className+=' '+n;},remove:n=>{this.className=this.className.split(' ').filter(x=>x!==n).join(' ');}};}
 appendChild(e){e.parentNode=this;this.children.push(e);return e;}
 removeChild(e){this.children.splice(this.children.indexOf(e),1);e.parentNode=null;return e;}
 setAttribute(k,v){this.attrs[k]=v;}
 addEventListener(){}
}
function harness(){const body=new Element(),timers=new Map();let timer=0;const document={body,querySelector:()=>null,getElementById:()=>null,createElement:()=>new Element(),createElementNS:()=>new Element()};const window={setTimeout:fn=>{timers.set(++timer,fn);return timer;},clearTimeout:id=>timers.delete(id),requestAnimationFrame:fn=>fn()};const c=vm.createContext({document,window,Node:Element,module:{exports:{}}});vm.runInContext(fs.readFileSync('static/admin/js/kidsmap_notifications.js','utf8'),c);c.toast=c.module.exports.kmToast;return{c,body,timers};}
test('fourth toast completes synchronously and retains the newest three',()=>{const{c,body}=harness();vm.runInContext("for(let i=0;i<4;i++)toast.info('notice '+i,{duration:0});",c,{timeout:250});assert.equal(body.children[0].children.length,3);const titles=body.children[0].children.map(t=>t.children[1].children[0].textContent);assert.deepEqual(titles,['notice 1','notice 2','notice 3']);});

test('first three notices exercise the DOM fixture without a deadline failure',()=>{const{c,body}=harness();vm.runInContext("for(let i=0;i<3;i++)toast.info('control '+i,{duration:0});",c,{timeout:250});assert.equal(body.children[0].children.length,3);});
test('capacity while oldest is leaving keeps new notices after its delayed removal',()=>{const{c,body,timers}=harness();vm.runInContext("const first=toast.info('old',{duration:0});toast.info('middle',{duration:0});toast.info('new',{duration:0});toast.dismiss(first);toast.info('latest',{duration:0});",c,{timeout:250});for(const fn of timers.values())fn();assert.equal(body.children[0].children.length,3);assert.equal(body.children[0].children[2].children[1].children[0].textContent,'latest');});
test('rapid overflow remains bounded and normal clearAll still removes active notices',()=>{const{c,body,timers}=harness();vm.runInContext("for(let i=0;i<20;i++)toast.info('notice '+i);",c,{timeout:250});assert.equal(body.children[0].children.length,3);vm.runInContext('toast.clearAll()',c,{timeout:250});for(const fn of [...timers.values()])fn();assert.equal(body.children[0].children.length,0);});
