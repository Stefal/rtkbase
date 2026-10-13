// Browser preference behaviour without server, receiver or network access.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname, '../web_app/static/theme.js'), 'utf8');
function browser(saved, dark=false, blocked=false) {
  const events = {}, mediaEvents = {}, documentEvents = {}, controlEvents = {};
  const select = { value:'system', addEventListener:(name, fn)=>controlEvents[name]=fn };
  const document = {documentElement:{dataset:{}}, addEventListener:(name,fn)=>documentEvents[name]=fn,
    getElementById:()=>select};
  const media = {matches:dark, addEventListener:(name,fn)=>mediaEvents[name]=fn};
  const stored = {};
  const window = {matchMedia:()=>media, addEventListener:(name,fn)=>(events[name]??=[]).push(fn),
    dispatchEvent:event=>(events[event.type]||[]).forEach(fn=>fn(event))};
  vm.runInNewContext(source, {document,window,Event:class {constructor(type){this.type=type;}},
    localStorage:{getItem:()=>{if(blocked)throw Error('denied');return saved;},
      setItem:(key,value)=>{if(blocked)throw Error('denied');stored[key]=value;}}});
  documentEvents.DOMContentLoaded();
  return {document,media,select,stored,change:value=>{select.value=value;controlEvents.change();},
    system:value=>{media.matches=value;mediaEvents.change();},
    storage:value=>window.dispatchEvent({type:'storage',key:'rtkbase-theme',newValue:value})};
}
let b=browser(null,true);assert.equal(b.document.documentElement.dataset.theme,'dark');
b.system(false);assert.equal(b.document.documentElement.dataset.theme,'light');
b.change('dark');assert.equal(b.stored['rtkbase-theme'],'dark');
b.system(false);assert.equal(b.document.documentElement.dataset.theme,'dark');
b.storage('light');assert.equal(b.select.value,'light');assert.equal(b.document.documentElement.dataset.theme,'light');
b.storage(null);assert.equal(b.select.value,'system');
b=browser('unknown',true);assert.equal(b.select.value,'system');
b=browser('light',true);assert.equal(b.document.documentElement.dataset.theme,'light');
b=browser(null,false,true);b.change('dark');assert.equal(b.document.documentElement.dataset.theme,'dark');
console.log('Theme preference, system changes, persistence, cross-tab changes and blocked storage passed.');
