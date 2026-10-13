(function () {
'use strict';
const panel=document.getElementById('system-update-panel'); if(!panel)return;
const check=document.getElementById('system-update-check'), label=document.getElementById('system-update-status'), log=document.getElementById('system-update-progress');
const details=document.getElementById('system-update-error-details');
let pending=false;
function showLastUpdate(timestamp) {
const target=document.getElementById('system-update-last');
if(!Number.isFinite(timestamp)){target.textContent='Last successful system update: not yet recorded.';return;}
const date=new Date(timestamp*1000), minutes=Math.max(0,Math.floor((Date.now()-date.getTime())/60000));
const elapsed=minutes<1?'just now':minutes<60?minutes+' minute'+(minutes===1?'':'s')+' ago':minutes<1440?Math.floor(minutes/60)+' hour'+(Math.floor(minutes/60)===1?'':'s')+' ago':Math.floor(minutes/1440)+' day'+(Math.floor(minutes/1440)===1?'':'s')+' ago';
target.textContent='Last successful system update: '+date.toLocaleString()+' ('+elapsed+').';
}
async function request(payload){
const response=await fetch('/api/v1/system-updates',payload?{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':panel.dataset.token},body:JSON.stringify(payload)}:{});
const data=await response.json(); if(!response.ok)throw new Error(data.error||'System updates unavailable');
if('last_successful_update' in data)showLastUpdate(data.last_successful_update);
const busy=['queued','running'].includes(data.state); check.disabled=busy;
label.textContent=data.error||({idle:'Ready to check for updates.',queued:'Waiting for package manager…',running:'Updating…',ready:'Review the proposed packages below.',succeeded:'System updates completed.',failed:'System update failed.'}[data.state]||data.state); if(data.reboot_required)label.textContent+=': manual reboot required';
details.hidden=data.state!=='failed';
log.textContent=data.state==='failed'?(data.progress||[]).join('\n'):'';
if(details.hidden)details.open=false;
}
async function act(payload){pending=true;check.disabled=true;try{await request(payload);}catch(e){label.textContent=e.message;check.disabled=false;}finally{pending=false;}}
check.addEventListener('click',()=>{if(window.confirm('Update package lists and install available system updates? Package scripts may restart services.'))act({action:'update'});});
setInterval(async()=>{if(pending||!panel.classList.contains('show'))return;pending=true;try{await request();}catch(e){label.textContent=e.message;}finally{pending=false;}},2000);
}());
