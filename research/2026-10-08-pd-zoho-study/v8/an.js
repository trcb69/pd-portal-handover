const d=require("./d.json"),p=require("./p.json"),sh=require("./sh.json"),inv=require("./inv.json");
const T=s=>Date.parse(s);const g=(o,k)=>Object.values(o).find(v=>v.body&&v.body[k])?.body[k];
const stats=new Proxy({},{get:(o,k)=>o[k]??(o[k]={})});const rows=[];
const bump=(t,so,ch,lab,ids)=>{const x=stats[t];x.n=(x.n||0)+1;const dt=(T(so)-T(ch))/1000;
 const k=dt>=0?"so_at_or_after":"so_before";x[k]=(x[k]||0)+1;if(dt<0)(x.neg=x.neg||[]).push(dt);if(dt>=0)(x.lag=x.lag||[]).push(dt);
 rows.push({type:t,id:ids,so_lm:so,child_lm:ch,so_minus_child_s:dt,field:lab});};
const P={},S={},I={};
for(const v of Object.values(p))if(v.body.package)P[v.body.package.package_id]=v.body.package;
for(const v of Object.values(sh))if(v.body.shipmentorder)S[v.body.shipmentorder.shipment_id]=v.body.shipmentorder;
for(const v of Object.values(inv))if(v.body.invoice)I[v.body.invoice.invoice_id]=v.body.invoice;
let sos=0,newest={},ok=0,bad=0;const sorows=[];
for(const v of Object.values(d)){const s=v.body.salesorder;if(!s)continue;sos++;
 let mx=0,mxl="";
 for(const x of s.packages||[]){const c=P[x.package_id];if(!c)continue;bump("package",s.last_modified_time,c.last_modified_time,"lm",s.salesorder_number);bump("package(created)",s.last_modified_time,c.created_time,"created",s.salesorder_number);
  if(T(c.last_modified_time)>mx){mx=T(c.last_modified_time);mxl="package"}
  const sd=S[x.shipment_id];if(sd){bump("shipment",s.last_modified_time,sd.last_modified_time,"lm",s.salesorder_number);bump("shipment(created)",s.last_modified_time,sd.created_time,"created",s.salesorder_number);if(T(sd.last_modified_time)>mx){mx=T(sd.last_modified_time);mxl="shipment"}}}
 for(const x of s.invoices||[]){const c=I[x.invoice_id];if(!c)continue;bump("invoice",s.last_modified_time,c.last_modified_time,"lm",s.salesorder_number);bump("invoice(created)",s.last_modified_time,c.created_time,"created",s.salesorder_number);if(T(c.last_modified_time)>mx){mx=T(c.last_modified_time);mxl="invoice"}}
 if(mx){const dt=(T(s.last_modified_time)-mx)/1000;dt>=0?ok++:bad++;sorows.push({so:s.salesorder_number,so_lm:s.last_modified_time,newest_child:new Date(mx+19800000).toISOString(),by:mxl,dt})}}
for(const t in stats){const x=stats[t];if(x.n)console.log(t,JSON.stringify({n:x.n,at_or_after:x.so_at_or_after||0,before:x.so_before||0,neg:x.neg}))}
for(const t of Object.keys(rows.reduce((a,r)=>(a[r.type]=1,a),{}))){const r=rows.filter(x=>x.type==t);const a=r.filter(x=>x.so_minus_child_s>=0).length;const l=r.filter(x=>x.so_minus_child_s>=0).map(x=>x.so_minus_child_s).sort((a,b)=>a-b);console.log(t,r.length,"so>=child",a,"before",r.length-a,"lag median",l[l.length>>1],"max",l[l.length-1],"min before",Math.min(...r.map(x=>x.so_minus_child_s)))}
console.log("SOs",sos,"with children",ok+bad,"so>=newest",ok,"before",bad);
require("fs").writeFileSync("analysis.json",JSON.stringify({sorows,rows},null,1));
console.log(sorows.filter(r=>r.dt<0));
