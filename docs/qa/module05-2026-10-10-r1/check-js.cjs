const fs=require('fs'),vm=require('vm'),path=require('path');let failed=[];
for(const f of fs.readdirSync(__dirname).filter(x=>x.endsWith('.js'))){try{new vm.Script('('+fs.readFileSync(path.join(__dirname,f),'utf8')+')');}catch(e){failed.push({file:f,error:String(e)});}}
console.log(JSON.stringify({syntax_failures:failed}));process.exit(failed.length?1:0);
