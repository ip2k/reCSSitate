const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {webkit}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const source=fs.readFileSync(require('node:path').join(__dirname,'../userscript/recssitate.user.js'),'utf8').replace('__PAGE_RESCUE_ORIGIN__','https://reader.invalid');
const article='<main><h1>Example news article</h1>'+Array.from({length:12},()=>'<p>'+('This is a synthetic article paragraph used to test reading behavior. '.repeat(8)))+'</p></main>';
function wall(text='Disable Your Adblocker',style='position:fixed;inset:0;background:white;z-index:9'){return `<section id="wall" style="${style}"><h3>${text}</h3><button onclick="this.parentNode.remove()">Close</button></section>`;}
test('obstruction detection and removal at phone width',async()=>{
 const browser=await webkit.launch();
 try{
  const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
  await context.addInitScript({content:'window.GM={getValue:async(k,d)=>d,setValue:async()=>{}};'+source});
  let html=article;
  await context.route('https://news.invalid/**',route=>route.fulfill({contentType:'text/html',body:'<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1">'+html}));
  const page=await context.newPage();
  const button=page.getByRole('button',{name:'Read article',exact:true});
  for(const extra of ['',wall('Accept cookies'),wall('Disable Your Adblocker','position:fixed;bottom:0;height:50px;left:0;right:0;background:white'),wall('Disable Your Adblocker','display:none')]){
   html=article+extra;await page.goto('https://news.invalid/article');await page.waitForTimeout(4500);assert.equal(await button.count(),0);
  }
  html=article;await page.goto('https://news.invalid/article');
  await page.evaluate(markup=>document.body.insertAdjacentHTML('beforeend',markup),wall());
  await button.waitFor({state:'visible',timeout:7000});
  await page.locator('#wall button').click();await button.waitFor({state:'detached',timeout:3000});
  await page.evaluate(markup=>document.body.insertAdjacentHTML('beforeend',markup),wall());
  await button.waitFor({state:'visible',timeout:7000});
  const navigation=page.waitForURL('https://reader.invalid/**');
  await context.route('https://reader.invalid/**',r=>r.fulfill({body:'Reader destination'}));
  await button.click();await navigation;
  assert.equal(new URLSearchParams(new URL(page.url()).hash.slice(1)).get('url'),'https://news.invalid/article');
  await context.close();
 }finally{await browser.close();}
});
