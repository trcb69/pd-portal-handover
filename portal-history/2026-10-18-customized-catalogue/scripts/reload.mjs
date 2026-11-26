// Page.reload on the first inventory tab of a CDP port (fixes hung tabs, keeps session). Usage: PORT=9335 node reload.mjs
const tabs = await (await fetch(`http://127.0.0.1:${process.env.PORT}/json`)).json();
const tab = tabs.find(t => t.type==='page' && (process.env.TAB ? t.id===process.env.TAB : t.url.includes('inventory.zoho.com')));
const ws = new WebSocket(tab.webSocketDebuggerUrl); await new Promise(r=>ws.onopen=r);
ws.send(JSON.stringify({id:1,method:'Page.reload',params:{}}));
setTimeout(()=>{console.log('reloaded',tab.url);process.exit(0)},500);
