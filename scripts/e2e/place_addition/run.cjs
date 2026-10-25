const H=require('./helpers.cjs');
const args=Object.fromEntries(process.argv.slice(2).reduce((rows,item,i,all)=>item.startsWith('--')?[...rows,[item.slice(2),all[i+1]]]:rows,[]));
const fixturePath=args.fixture;
H.assert(fixturePath,'--fixture is required');
const fixture=JSON.parse(H.fs.readFileSync(fixturePath,'utf8'));H.assert.equal(fixture.synthetic,true);H.assert.equal(fixture.database,'qa_stage04');
if(args['base-url'])H.assert.equal(args['base-url'],fixture.origin);
const out=H.path.resolve(args.output||'.tmp/place-addition-e2e/results');H.fs.mkdirSync(out,{recursive:true});
let runtime=null;
const results=[];const record=row=>{results.push(row);H.fs.writeFileSync(H.path.join(out,'results.json'),JSON.stringify({synthetic:true,origin:fixture.origin,runtime,externalMaps:'NOT RUN: external transport blocked',sources:fixture.sources,results},null,2));console.log(row.status,row.id,row.role||'',row.lang||'',row.error||'');};
(async()=>{
 let ready=false;for(let attempt=0;attempt<40;attempt++){try{const r=await fetch(fixture.origin+'/admin/login/');if(r.status===200){ready=true;break;}}catch{}await new Promise(resolve=>setTimeout(resolve,500));}H.assert(ready,'Attested QA server became ready');
 const build=await(await fetch(fixture.origin+'/__qa__/build/')).json();H.assert.equal(build.synthetic,true);H.assert.deepEqual(build.sources,fixture.sources,'The QA server is running the candidate fixture snapshot');
 const crypto=require('node:crypto'),repository=H.path.resolve(__dirname,'../../..');
 for(const [name,digest]of Object.entries(fixture.sources))H.assert.equal(crypto.createHash('sha256').update(H.fs.readFileSync(H.path.join(repository,name))).digest('hex'),digest,`Source changed after fixture/stand startup: ${name}`);
 const browser=await H.launch();runtime={engine:process.env.KIDSMAP_BROWSER_ENGINE||'chromium',version:browser.version()};try{const ctx={browser,fixture,fixtureDir:H.path.dirname(H.path.resolve(fixturePath)),out,record};const group=args.group||'smoke';
 H.assert(['smoke','create','publish','visual','pricing','json','regression','limits','compact','guidance','roles','refinement','feedback','full'].includes(group),'Unknown E2E group');
 if(['smoke','create','full','publish'].includes(group)){const {create}=require('./create.cjs');const {sendForReview,publish,publicCheck}=require('./publication.cjs');for(const [lang,width]of(group==='full'?[['ru',1440],['az',390],['en',768]]:[['ru',1440]]))for(const role of ['admin','owner']){const item=await create(ctx,role,lang,width);if(['full','publish'].includes(group)){if(role==='owner')await sendForReview(ctx,item);const place=await publish(ctx,item);await publicCheck(ctx,place);}}}
 if(['visual','full'].includes(group))await require('./visual.cjs').visual(ctx);
 if(['pricing','full'].includes(group))await require('./pricing.cjs').pricing(ctx);
 if(['json','full'].includes(group))await require('./json.cjs').json(ctx);
 if(['regression','full'].includes(group))await require('./regression.cjs').regression(ctx);
 if(['limits','full'].includes(group))await require('./limits.cjs').limits(ctx);
 if(['compact','full'].includes(group))await require('./compact.cjs').compact(ctx);
 if(['guidance','full'].includes(group))await require('./guidance.cjs').guidance(ctx);
 if(group==='roles')await require('./roles.cjs').roles(ctx);
 if(group==='refinement')await require('./refinement.cjs').refinement(ctx);
 if(group==='feedback')await require('./feedback.cjs').feedback(ctx);
 H.assert(results.length,'No E2E checks executed');
}finally{await browser.close();}})().catch(error=>{console.error(error);process.exitCode=1;});
