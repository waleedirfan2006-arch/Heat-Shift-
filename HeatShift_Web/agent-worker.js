'use strict';
let runtime;
async function init(){
  if(runtime)return runtime;
  runtime=(async()=>{
    postMessage({status:'Loading Python runtime… First use may take a minute.'});
    const runtimeURL=new URL('./',self.location.href).href;
    importScripts(runtimeURL+'pyodide.js');
    postMessage({status:'Starting the bundled Python engine…'});
    const py=await loadPyodide({indexURL:runtimeURL});
    postMessage({status:'Loading pandas and the preserved agents…'});
    await py.loadPackage('pandas');
    py.FS.mkdirTree('/heatshift/vendor');py.FS.mkdirTree('/heatshift/evidence');
    const files=['integration.py','vendor/data_quality_agent.py','vendor/insight_agent.py','evidence/integration_provenance.json','evidence/karachi_train.csv.gz','evidence/lahore_train.csv.gz','evidence/multan_train.csv.gz','trusted_weather_guide.md','insight_policy.py','gold_manifest.json'];
    await Promise.all(files.map(async file=>{const r=await fetch(new URL(file.split('/').pop()+'?v=strict-scope-v2',self.location.href),{cache:'no-store'});if(!r.ok)throw Error('Agent source unavailable: '+file);py.FS.writeFile('/heatshift/'+file,new Uint8Array(await r.arrayBuffer()));}));
    await py.runPythonAsync("import sys, json\nsys.path.insert(0, '/heatshift')\nfrom integration import run_quality, ask_insight, training_evidence, _load_agent\n_load_agent('data_quality_agent.py', 'DataQualityAgent')\n_load_agent('insight_agent.py', 'InsightAgent')");
    return py;
  })().catch(e=>{runtime=null;throw e;});
  return runtime;
}
async function handle(data){
  const {id,kind,city,text,filename,isUpload}=data;
  try{
    const py=await init();
    py.globals.set('selected_city',city);py.globals.set('input_text',text||'');py.globals.set('input_filename',filename||'training.csv');py.globals.set('is_upload',Boolean(isUpload));
    let output;
    if(kind==='insight')output=await py.runPythonAsync("json.dumps(ask_insight(selected_city, input_text), default=str)");
    else output=await py.runPythonAsync("payload = input_text.encode('utf-8') if is_upload else training_evidence(selected_city).to_csv(index=False).encode('utf-8')\nreport, cleaned = run_quality(payload, input_filename)\njson.dumps({'report': report, 'cleaned': cleaned.decode('utf-8')}, default=str)");
    postMessage({id,result:JSON.parse(output)});
  }catch(e){postMessage({id,error:String(e.message||e)});}
}
let queue=Promise.resolve();
self.onmessage=({data})=>{queue=queue.then(()=>handle(data));};
