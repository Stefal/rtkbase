(function(scope) {
  'use strict';
  const dictionary=scope.RTKBaseFrench || (typeof module!=='undefined' ? require('./language-fr.js') : {});
  const key='rtkbase-language',valid=value=>['fr','en'].includes(value);
  let preference='fr';
  try {const saved=scope.localStorage.getItem(key);if(valid(saved))preference=saved;} catch(_) {}
  function t(source,values={}) {
    const text=preference==='fr'&&Object.prototype.hasOwnProperty.call(dictionary,source)?dictionary[source]:source;
    return text.replace(/\{([a-zA-Z]+)\}/g,(whole,name)=>Object.prototype.hasOwnProperty.call(values,name)?String(values[name]):whole);
  }
  // Only authored, explicitly marked text is translated. Do not touch
  // receiver-supplied names, measurements, logs, links or input values.
  const nodes=new WeakMap();
  function render(element) {
    const source=element.getAttribute('data-i18n');
    let node=nodes.get(element);
    if(!node){
      function find(parent){
        for(const child of parent.childNodes){
          if(child.nodeType===3 && child.textContent.trim()===source)return child;
          if(child.nodeType===1){const found=find(child);if(found)return found;}
        }
        return null;
      }
      node=find(element);if(node)nodes.set(element,node);
    }
    if(node)node.textContent=t(source);
  }
  function apply(){
    if(!scope.document)return;
    scope.document.documentElement.lang=preference;
    scope.document.querySelectorAll('[data-i18n]').forEach(render);
    const select=scope.document.getElementById('interface-language');if(select)select.value=preference;
    scope.dispatchEvent(new scope.Event('rtkbase-language-change'));
  }
  const api={t,get language(){return preference;},setLanguage(value){
    if(!valid(value))return false;
    preference=value;try{scope.localStorage.setItem(key,value);}catch(_){}
    apply();return true;
  }};
  if(typeof module!=='undefined')module.exports=api;
  scope.RTKBaseI18n=api;
  if(!scope.document)return;
  scope.document.addEventListener('DOMContentLoaded',()=>{
    const select=scope.document.getElementById('interface-language');
    if(select)select.addEventListener('change',()=>api.setLanguage(select.value));
    apply();
  });
  scope.addEventListener('storage',event=>{
    if(event.key===key){preference=valid(event.newValue)?event.newValue:'fr';apply();}
  });
})(typeof window!=='undefined'?window:{});
