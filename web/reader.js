/* global Readability, DOMPurify */
'use strict';
const form = document.querySelector('#open');
const input = document.querySelector('#url');
const status = document.querySelector('#status');
const frame = document.querySelector('#article');
let controller;
const escape = s => String(s || '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
async function read(value) {
  let url;
  try {url = new URL(value);if(url.protocol !== 'https:' || url.username || url.password) throw Error();}
  catch {status.textContent='Enter an HTTPS article address without login details.';return;}
  controller?.abort();controller=new AbortController();const current=controller;
  const timer=setTimeout(()=>current.abort(),90000);
  document.querySelector("#signin").href="/signin#"+new URLSearchParams({url:url.href});
  input.value=url.href;frame.hidden=true;document.querySelector('#setup').hidden=true;
  status.textContent='Opening the article… This can take up to a minute.';
  form.querySelector('button').disabled=true;
  const original=document.querySelector('#original');original.href=url.href;original.hidden=false;
  try {
    const response=await fetch('/api/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:url.href}),signal:current.signal});
    if(!response.ok)throw Error(response.status===401?'Sign in, then try again.':'This site could not be fetched. It may not be supported by this server.');
    const result=await response.json();
    if(controller!==current)return;
    const doc=new DOMParser().parseFromString(result.body,'text/html');
    doc.querySelectorAll('script,iframe,object,embed,base').forEach(e=>e.remove());
    const base=doc.createElement('base');base.href=url.href;doc.head.prepend(base);
    const article=new Readability(doc).parse();
    if(!article || article.textContent.trim().length<500 || /just a moment|access denied|checking your browser/i.test(article.title))throw Error('No readable article was returned. Try the original page or Safari Reader.');
    const body=DOMPurify.sanitize(article.content,{USE_PROFILES:{html:true},FORBID_TAGS:['style','form','input','button','textarea','select','iframe','video','audio','source'],FORBID_ATTR:['style','srcset'],ALLOW_DATA_ATTR:false});
    frame.srcdoc='<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; img-src https: data:; style-src &#39;unsafe-inline&#39;"><style>body{max-width:42rem;margin:auto;padding:22px;color:#192b38;background:#fff;font:19px/1.65 Georgia,serif;overflow-wrap:anywhere}h1{font:700 28px/1.2 system-ui}h2,h3{line-height:1.3}img{max-width:100%;height:auto}a{color:#175c91}pre{white-space:pre-wrap}figure{margin:20px 0}table{display:block;overflow:auto}</style><h1>'+escape(article.title)+'</h1><p>'+escape(article.byline)+'</p>'+body;
    frame.hidden=false;status.textContent='Article ready. Images and links may depend on the original site.';
    document.title=article.title+' — reCSSitate';
  } catch(error) {if(controller!==current)return;status.textContent=error.name==='AbortError'?'The request timed out. Try again or open the original article.':error.message;}
  finally {clearTimeout(timer);if(controller===current)form.querySelector('button').disabled=false;}
}
form.addEventListener('submit',event=>{event.preventDefault();const next=new URLSearchParams({url:input.value});if(location.hash.slice(1)===next.toString())read(input.value);else location.hash=next;});
function route(){const value=new URLSearchParams(location.hash.slice(1)).get('url');if(value)read(value);}
window.addEventListener('hashchange',route);route();

const bookmarklet='javascript:(()=>{location.href='+JSON.stringify(location.origin+'/#url=')+'+encodeURIComponent(location.href)})()';
document.querySelector('#bookmarklet').href=bookmarklet;
document.querySelector('#bookmarklet-code').value=bookmarklet;
document.querySelector('#copy-bookmarklet').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(bookmarklet);status.textContent='Copied. Paste this into your Safari bookmark’s address.';}catch{document.querySelector('#bookmarklet-code').select();status.textContent='Select and copy the bookmark address above.';}});
