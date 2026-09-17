// ==UserScript==
// @name reCSSitate
// @namespace recssitate
// @version 0.2.0
// @description Offer a reader when a persistent anti-adblock wall obstructs an article.
// @match https://*/*
// @run-at document-idle
// @noframes
// @grant GM.getValue
// @grant GM.setValue
// ==/UserScript==
(async () => {
  'use strict';
  if(window.top!==window)return;
  const preset='__PAGE_RESCUE_ORIGIN__';
  let origin=await GM.getValue('readerOrigin',preset);
  function valid(value){try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password?u.origin:null;}catch{return null;}}
  async function configure(){const value=prompt('HTTPS address of your reader server',valid(origin)||'');if(value===null)return;const next=valid(value);if(!next){alert('Enter an HTTPS server address without credentials.');return;}origin=next;await GM.setValue('readerOrigin',next);}
  // Safari Userscripts supports storage, but not GM.registerMenuCommand.
  // Unconfigured copies ask for the server only when the reader button is tapped.
  if(valid(origin)===location.origin)return;
  const message=/disable (?:your|my|the) ad\s*blocker|disable your ad blocker|turn off (?:your )?ad\s*blocker|ad\s*blocker (?:detected|enabled)|please consider allowing ads|support us by disabling/i;
  let host,wallSince=0,lastWall=null,dismissed=false,scheduled=false;
  function obstruction(){
    const article=document.querySelector('article,main,[itemprop="articleBody"]');
    // An article may be hidden by CSS; textContent still provides a useful signal.
    if(!article || (article.textContent||'').trim().length<500)return null;
    for(const node of document.querySelectorAll('h1,h2,h3,[role="dialog"],[aria-modal="true"]')){
      if(!message.test(node.textContent||''))continue;
      const headingStyle=getComputedStyle(node),headingBox=node.getBoundingClientRect();
      if(headingStyle.display==='none'||headingStyle.visibility==='hidden'||headingBox.width===0||headingBox.height===0)continue;
      for(let panel=node,depth=0;panel&&depth<9;panel=panel.parentElement,depth++){
        const style=getComputedStyle(panel),box=panel.getBoundingClientRect();
        if(style.display==='none'||style.visibility==='hidden'||Number(style.opacity)===0)break;
        const overlap=Math.max(0,Math.min(box.bottom,innerHeight)-Math.max(box.top,0));
        const width=Math.max(0,Math.min(box.right,innerWidth)-Math.max(box.left,0));
        if((style.position==='fixed'||style.position==='absolute'||panel.getAttribute('aria-modal')==='true')&&width>innerWidth*.65&&overlap>innerHeight*.4){
          const top=document.elementFromPoint(Math.max(1,Math.min(innerWidth-1,box.left+box.width/2)),Math.max(1,Math.min(innerHeight-1,box.top+overlap/2)));
          if(top&&panel.contains(top))return panel;
        }
      }
    }
    return null;
  }
  function hide(){host?.remove();host=null;}
  function show(){
    if(host)return;
    host=document.createElement('aside');host.id='recssitate-button';host.setAttribute('popover','manual');
    host.style.cssText='position:fixed;inset:auto 12px max(12px,env(safe-area-inset-bottom)) auto;margin:0;border:0;padding:0;background:transparent;overflow:visible;z-index:2147483647;max-width:calc(100vw - 24px)';
    const shadow=host.attachShadow({mode:'open'});
    shadow.innerHTML='<style>.row{display:flex;gap:8px;align-items:center;padding:8px;background:#132a40;border-radius:14px;box-shadow:0 3px 16px #0005}button{border:0;border-radius:9px;padding:12px 16px;min-height:44px;background:#fff;color:#132a40;font:600 15px system-ui;cursor:pointer}.close{min-width:44px;padding:12px;background:#294158;color:white}</style><div class="row"><button class="read">Read article</button><button class="close" aria-label="Dismiss reader button">×</button></div>';
    shadow.querySelector('.read').addEventListener('click',()=>{
      const endpoint=valid(origin);if(!endpoint){configure();return;}
      // Navigation in the same tab survives iOS popup restrictions and preserves Back.
      location.assign(endpoint+'/#'+new URLSearchParams({url:location.href}).toString());
    });
    shadow.querySelector('.close').addEventListener('click',()=>{dismissed=true;hide();});
    document.documentElement.append(host);try{host.showPopover();}catch{}
  }
  function scan(){
    scheduled=false;if(dismissed)return;
    const wall=obstruction();
    if(!wall){lastWall=null;wallSince=0;hide();return;}
    if(wall!==lastWall){lastWall=wall;wallSince=Date.now();setTimeout(scan,2600);}
    if(Date.now()-wallSince>=2500)show();
  }
  function schedule(){if(!scheduled){scheduled=true;setTimeout(scan,500);}}
  let timer;
  function watch(){clearInterval(timer);let ticks=0;timer=setInterval(()=>{scan();if(++ticks>=90)clearInterval(timer);},1000);}
  window.addEventListener('scroll',schedule,{passive:true});
  window.addEventListener('pageshow',()=>{dismissed=false;watch();});
  document.addEventListener('visibilitychange',()=>{if(document.hidden)clearInterval(timer);else watch();});
  watch();
})();
