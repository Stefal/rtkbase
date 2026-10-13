const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const dictionary=require('../web_app/static/language-fr.js');
const source=fs.readFileSync(require.resolve('../web_app/static/language.js'),'utf8');
function page(saved,blocked=false){
  const text={nodeType:3,textContent:'Settings'},label={nodeType:1,childNodes:[text],href:'/settings'};
  const marked={nodeType:1,childNodes:[label],getAttribute:()=> 'Settings'};
  const untouched={value:'SGC2',textContent:'Settings'},select={value:'',addEventListener:(name,fn)=>select.change=fn};
  const events={},storage=new Map(saved?[['rtkbase-language',saved]]:[]);
  const window={RTKBaseFrench:dictionary,Event:function(type){this.type=type;},
    localStorage:{getItem:k=>{if(blocked)throw Error('blocked');return storage.get(k);},setItem:(k,v)=>{if(blocked)throw Error('blocked');storage.set(k,v);}},
    document:{documentElement:{},querySelectorAll:()=>[marked],getElementById:()=>select,addEventListener:(name,fn)=>events[name]=fn},
    addEventListener:(name,fn)=>events[name]=fn,dispatchEvent:()=>{}};
  vm.runInNewContext(source,{window});events.DOMContentLoaded();
  return {window,text,label,untouched,select,storage,events};
}
const a=page();assert.equal(a.text.textContent,'Réglages');assert.equal(a.window.document.documentElement.lang,'fr');
a.select.value='en';a.select.change();assert.equal(a.text.textContent,'Settings');assert.equal(a.storage.get('rtkbase-language'),'en');
assert.equal(a.label.href,'/settings');assert.equal(a.untouched.value,'SGC2');assert.equal(a.untouched.textContent,'Settings');
a.window.RTKBaseI18n.setLanguage('fr');assert.equal(a.text.textContent,'Réglages');
assert.equal(a.window.RTKBaseI18n.setLanguage('invalid'),false);
assert.equal(a.window.RTKBaseI18n.t('unknown <text>'),'unknown <text>');
assert.equal(a.window.RTKBaseI18n.t('Receiver {name}',{name:'test'}),'Receiver test');
assert.equal(page('en').text.textContent,'Settings');assert.equal(page('invalid').text.textContent,'Réglages');
assert.equal(page(null,true).text.textContent,'Réglages');
a.events.storage({key:'rtkbase-language',newValue:'en'});assert.equal(a.text.textContent,'Settings');assert.equal(a.select.value,'en');
assert.equal(a.window.RTKBaseI18n.language,'en');
console.log('Language switch, persistence, storage sync, blocked storage, safe text and untouched values: passed');
