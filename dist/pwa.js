(() => {
let prompt;
const install=document.querySelector('#install-app'),status=document.querySelector('#widget-status'),code=document.querySelector('#widget-code');
window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();prompt=e;install.hidden=false;});
install.onclick=async()=>{if(prompt){await prompt.prompt();prompt=null;install.hidden=true;}};
window.addEventListener('appinstalled',()=>{install.hidden=true;});
document.querySelector('#copy-iphone-script').onclick=async()=>{try{if(navigator.clipboard.write&&window.ClipboardItem){await navigator.clipboard.write([new ClipboardItem({'text/plain':fetch('/love-widget.js').then(r=>r.text()).then(text=>new Blob([text],{type:'text/plain'}))})]);}else{const text=await fetch('/love-widget.js').then(r=>r.text());await navigator.clipboard.writeText(text);}status.textContent='Script copied. In Scriptable, create a new script, paste this code, name it Love Notes, and run it once.';}catch{status.textContent='Open the script download link, select its contents and copy them into a new Scriptable script.';}};
if('serviceWorker' in navigator&&location.protocol==='https:')navigator.serviceWorker.register('/sw.js').catch(()=>{});
async function action(path){const r=await fetch('/api/'+path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:'{}'});const data=await r.json();if(!r.ok)throw new Error(data.error||'Please try again.');return data;}
document.querySelector('#pair-widget').onclick=async function(){this.disabled=true;try{const data=await action('widget-pair');code.textContent=data.code;status.textContent='Use this once in your widget within 15 minutes. It can read only today’s note.';}catch(e){status.textContent=e.message;}finally{this.disabled=false;}};
document.querySelector('#disconnect-widgets').onclick=async function(){this.disabled=true;try{await action('widget-disconnect');code.textContent='';status.textContent='Your widget connections are disconnected.';}catch(e){status.textContent=e.message;}finally{this.disabled=false;}};
const offline=document.querySelector('#offline-message');function connection(){offline.hidden=navigator.onLine;}
window.addEventListener('online',connection);window.addEventListener('offline',connection);connection();
})();
