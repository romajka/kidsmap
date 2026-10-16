const Module=require('module'),path=require('path');const original=Module._resolveFilename;
Module._resolveFilename=function(request,parent,...rest){if(request.includes('.tmp/phone-dom/node_modules/jsdom'))return original(path.join(__dirname,'node/node_modules/jsdom'),parent,...rest);return original(request,parent,...rest)};
// Exact fixture path adapter only; no synthetic HTML and no assertion changes.
const fs=require('fs');const legacy=path.resolve('.tmp/photo-form.html');const current=path.join(__dirname,'photo-form.html');
for(const name of ['existsSync','readFileSync']){const original=fs[name];fs[name]=function(p,...args){return original.call(fs,typeof p==='string' && path.resolve(p)===legacy?current:p,...args)}}
