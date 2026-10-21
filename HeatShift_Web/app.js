'use strict';
const $=id=>document.getElementById(id),C=HeatShiftCore,city=$('city');
const escapeHtml=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let evidence,lastForecast,qualityResult,unit='C',worker,sequence=0,modelPromise;
let observationOrigin='manual entry; not independently verified';
const calibrationPromise=fetch('model_evaluation.json').then(r=>{if(!r.ok)throw Error();return r.json();}).catch(()=>null);
const pending=new Map();
const fmtDate=x=>new Intl.DateTimeFormat('en-PK',{timeZone:'Asia/Karachi',month:'short',day:'numeric',year:'numeric',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(x))+' PKT';
const temp=x=>(unit==='F'?x*1.8+32:x).toFixed(1);
function download(data,name,type='application/json'){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([typeof data==='string'?data:JSON.stringify(data,null,2)],{type}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000);}
function renderCity(){
 const name=city.value,cfg=C.cities[name];$('airport').textContent=cfg.icao+' · Pakistan';$('insightCity').textContent=name;$('metarLink').href='https://aviationweather.gov/data/metar/?ids='+cfg.icao;$('metarLink').textContent='Get the '+name+' airport report · '+cfg.icao+' ↗';
 if(!evidence)return;const s=evidence[name];$('historicalMean').textContent=s.mean.toFixed(1);$('historicalMin').textContent=s.min.toFixed(1)+' °C';$('historicalMax').textContent=s.max.toFixed(1)+' °C';$('rowCount').textContent=s.rows.toLocaleString();$('stationSub').textContent=name+' airport · training observations';
 const m=s.monthly,w=900,h=185,pad=40,min=Math.floor((Math.min(...m.map(x=>x.mean))-3)/5)*5,max=Math.ceil((Math.max(...m.map(x=>x.mean))+3)/5)*5;
 const x=i=>pad+i*(w-2*pad)/(m.length-1),y=v=>h-30-(v-min)*(h-47)/(max-min);const points=m.map((v,i)=>`${x(i)},${y(v.mean)}`).join(' ');
 let lines='';for(let v=min;v<=max;v+=5)lines+=`<line x1="${pad}" y1="${y(v)}" x2="${w-pad}" y2="${y(v)}" stroke="#edf1e6" stroke-dasharray="3 4"/><text x="0" y="${y(v)+3}" fill="#a4af98" font-size="9">${v}°</text>`;
 const selected=m.map((v,i)=>i).filter(i=>i===0||i===m.length-1||i%Math.ceil(m.length/7)===0);
 $('chart').innerHTML=`<svg viewBox="0 0 ${w} ${h}" role="img"><title>${name} historical monthly mean temperature</title><defs><linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c9ddad" stop-opacity=".55"/><stop offset="1" stop-color="#eef5e3" stop-opacity=".1"/></linearGradient></defs>${lines}<polygon points="${pad},${h-30} ${points} ${w-pad},${h-30}" fill="url(#fade)"/><polyline points="${points}" fill="none" stroke="#819e67" stroke-width="2.4" stroke-linejoin="round"/>${m.map((v,i)=>`<circle cx="${x(i)}" cy="${y(v.mean)}" r="3" fill="#fff" stroke="#8ba775"><title>${v.month}: ${v.mean} °C</title></circle>`).join('')}${selected.map(i=>`<text x="${x(i)}" y="${h-8}" text-anchor="middle" fill="#a2ac96" font-size="9">${new Date(m[i].month+'-01T00:00Z').toLocaleDateString('en',{month:'short',year:'2-digit',timeZone:'UTC'})}</text>`).join('')}</svg>`;
 $('chartScope').textContent=name+' · '+s.rows.toLocaleString()+' observations · '+s.start.slice(0,10)+' to '+s.end.slice(0,10);
}
fetch('summary.json').then(r=>{if(!r.ok)throw Error();return r.json();}).then(d=>{evidence=d;renderCity();}).catch(()=>{$('stationSub').textContent='Repository summary unavailable';$('chart').textContent='Historical chart unavailable. No values have been assumed.';});renderCity();
function clearForecast(){lastForecast=null;$('downloadForecast').hidden=true;$('result').innerHTML='<div class="empty-state"><span>↗</span><h3>Ready for your next estimate.</h3><p>Review the observation and run the model.</p></div>';}
city.addEventListener('change',()=>{renderCity();clearForecast();$('temperature').value='';$('observedAt').value='';$('metar').value='';$('parseStatus').textContent='';qualityResult=null;$('qualityResult').innerHTML='<p class="help">City changed. Run a fresh quality check.</p>';$('qualityDownloads').hidden=true;$('qualityState').textContent='NOT RUN';$('insightResult').textContent='City changed. Ask the agent about '+city.value+' training observations.';});
['temperature','observedAt'].forEach(id=>$(id).addEventListener('input',()=>{observationOrigin='manual entry; not independently verified';clearForecast();}));
$('parseMetar').addEventListener('click',()=>{try{const p=C.parseMetar($('metar').value,city.value);$('temperature').value=p.temperature;$('observedAt').value=p.stamp;clearForecast();$('parseStatus').textContent='Observation filled. Review the temperature and PKT time.';}catch(e){$('parseStatus').textContent=e.message;}});
function renderForecast(){if(!lastForecast)return;const r=lastForecast;$('result').innerHTML=`<p class="result-target">${escapeHtml(r.city)} · ${fmtDate(r.target_utc)}</p><div class="result-number">${temp(r.prediction_c)}<small> °${unit}</small></div><p class="muted">${(Math.abs(r.prediction_c-r.baseline_c)*(unit==='F'?1.8:1)).toFixed(1)} °${unit} ${r.prediction_c>=r.baseline_c?'warmer':'cooler'} than the observation</p><div class="result-metrics"><div><span>Same-as-today baseline</span><strong>${temp(r.baseline_c)} °${unit}</strong></div><div><span>Historical error range</span><strong>${temp(r.prediction_c-r.band_c)}–${temp(r.prediction_c+r.band_c)} °${unit}</strong></div></div><p class="result-source">Observation: ${fmtDate(r.observation_utc)} · ${escapeHtml(r.observation_source)}<br>JMA fields: ${r.available}/10 · retrieved ${fmtDate(r.retrieved_at_utc)}<br>Model: original frozen HGB · ${escapeHtml(r.model_sha256.slice(0,12))}</p><p class="help">Range source: ${escapeHtml(r.band_source||'chronological training errors')}. Future coverage is not guaranteed. This estimates station temperature, not rain or general weather conditions.</p>`;$('downloadForecast').hidden=false;}
$('forecastForm').addEventListener('submit',async event=>{
 event.preventDefault();clearForecast();let input;try{input=C.validate(city.value,$('temperature').value,$('observedAt').value);}catch(e){$('forecastStatus').textContent=e.message;return;}
 const button=$('predict');button.disabled=true;button.textContent='Retrieving inputs & running model…';$('forecastStatus').textContent='Connecting to JMA inputs through Open-Meteo…';
 try{
  const cfg=C.cities[input.city],params=new URLSearchParams({latitude:cfg.lat,longitude:cfg.lon,models:'jma_gsm',hourly:C.fields.join(','),start_date:input.target.toISOString().slice(0,10),end_date:input.target.toISOString().slice(0,10),timezone:'UTC',temperature_unit:'celsius',wind_speed_unit:'kmh'});
  if(!modelPromise)modelPromise=fetch('model.json').then(r=>{if(!r.ok)throw Error('Frozen model unavailable.');return r.json();}).catch(e=>{modelPromise=null;throw e;});
  const [m,response,evaluation]=await Promise.all([modelPromise,fetch('https://previous-runs-api.open-meteo.com/v1/forecast?'+params,{signal:AbortSignal.timeout(25000)}),calibrationPromise]);
  if(!response.ok)throw Error('Weather input connection unavailable (HTTP '+response.status+'). Please try again.');
  const w=C.weatherValues(await response.json(),input.target),prediction=input.temperature+HeatShiftModel.predictResidual(C.row(input,w.values),m);if(!Number.isFinite(prediction))throw Error('Model output is invalid.');
  if(city.value!==input.city)throw Error('City changed during the request. Run a new prediction.');
  const calibrated=evaluation?.model_source_sha256===m.source_sha256?evaluation.calibration_bands?.[input.city]:null;
  lastForecast={city:input.city,method:'original_jma_hgb',observation_utc:input.observation.toISOString(),target_utc:input.target.toISOString(),baseline_c:input.temperature,prediction_c:prediction,band_c:calibrated?calibrated.half_width_c:cfg.q90,band_source:calibrated?'March 2024 calibration':'chronological training errors',available:w.available,retrieved_at_utc:new Date().toISOString(),model_sha256:m.source_sha256,observation_source:observationOrigin,limitations:'Experimental 24-hour airport temperature estimate. Historical error band is not a coverage guarantee.'};renderForecast();$('forecastStatus').textContent='Estimate ready. Review the input source and uncertainty.';$('jmaStatus').textContent='Connected · '+w.available+'/10 fields';$('jmaDot').className='dot green';
 }catch(e){$('result').innerHTML='<div class="error">'+escapeHtml(e.name==='TimeoutError'?'Weather input connection timed out. Try again shortly.':e.message)+'</div>';$('forecastStatus').textContent='No forecast produced. No baseline was substituted.';$('jmaStatus').textContent='Unavailable · last request failed';$('jmaDot').className='dot amber';}
 finally{button.disabled=false;button.innerHTML='Run 24-hour prediction <span>↗</span>';}
});
$('units').addEventListener('click',()=>{unit=unit==='C'?'F':'C';renderForecast();});$('downloadForecast').addEventListener('click',()=>{if(lastForecast)download(lastForecast,'heatshift-'+lastForecast.city.toLowerCase()+'-forecast.json');});
async function agents(kind,cityName,text,filename,isUpload=false){

 if(!worker){worker=new Worker('agent-worker.js?v=strict-scope-v2');worker.onmessage=({data})=>{
  if(data.status){$('runtimeStatus').textContent=data.status;$('agentStatus').textContent='Starting…';return;}
  const request=pending.get(data.id);if(!request)return;clearTimeout(request.timer);pending.delete(data.id);
  if(data.error){$('agentStatus').textContent='Unavailable · execution failed';$('runtimeStatus').textContent='Agent unavailable: '+data.error;request.reject(Error(data.error));}
  else{$('agentStatus').textContent='Ready · original sources verified';$('runtimeBrief').textContent='Original Python · running in browser';$('agentDot').className='dot green';$('runtimeStatus').textContent='Both agent source fingerprints verified. Processing runs in this browser; no CSV is uploaded to a server.';request.resolve(data.result);}
 };worker.onerror=()=>{for(const p of pending.values()){clearTimeout(p.timer);p.reject(Error('Browser Python runtime unavailable. Reload the page and retry.'));}pending.clear();worker.terminate();worker=null;$('agentStatus').textContent='Unavailable · runtime failed';};}
 return new Promise((resolve,reject)=>{const id=++sequence;const timer=setTimeout(()=>{pending.delete(id);reject(Error('Agent startup timed out. Reload the page and check that runtime assets can load.'));},240000);pending.set(id,{resolve,reject,timer});worker.postMessage({id,kind,city:cityName,text,filename,isUpload});});
}
function fileChanged(){const file=$('csvFile').files[0];$('fileName').textContent=file?file.name+' · '+(file.size/1024).toFixed(0)+' KB':'Optional · up to 10 MB · processed in this browser';$('runQuality').innerHTML=file?'Run quality agent on CSV <span>◇</span>':'Run training-data check <span>◇</span>';$('resetFile').hidden=!file;qualityResult=null;$('qualityDownloads').hidden=true;$('approveCleaned').checked=false;$('downloadCleaned').disabled=true;$('qualityResult').innerHTML='<p class="help">Source selected. Run a fresh quality check.</p>';$('qualityState').textContent='NOT RUN';}
$('csvFile').addEventListener('change',fileChanged);$('resetFile').addEventListener('click',()=>{$('csvFile').value='';fileChanged();});
$('runQuality').addEventListener('click',async()=>{
 const button=$('runQuality'),file=$('csvFile').files[0],selected=city.value;button.disabled=true;$('csvFile').disabled=true;$('resetFile').disabled=true;$('approveCleaned').checked=false;$('downloadCleaned').disabled=true;$('qualityDownloads').hidden=true;qualityResult=null;$('qualityState').textContent='RUNNING';$('qualityResult').innerHTML='<p class="help">Preparing the original Data Quality Agent… First use downloads Python and pandas. You can keep exploring the dashboard.</p>';
 try{if(file&&(file.size>10*1024*1024||!file.name.toLowerCase().endsWith('.csv')))throw Error('Choose a CSV file smaller than 10 MB.');const result=await agents('quality',selected,file?await file.text():'',file?file.name:selected.toLowerCase()+'_training.csv',Boolean(file));if(city.value!==selected)throw Error('City changed. Run a fresh check.');qualityResult=result;const r=result.report;
 $('qualityResult').innerHTML=`<p class="help">${result.saved_run?'Saved original-agent run · '+escapeHtml(r.timestamp)+' (agent clock, zone unstated)<br>':''}${escapeHtml(file?file.name:selected+' training observations')} · ${r.rows_before.toLocaleString()} → ${r.rows_after.toLocaleString()} rows</p><div class="quality-metrics"><div><strong>${r.duplicates_removed}</strong><span>Duplicates removed</span></div><div><strong>${r.values_filled}</strong><span>Values filled</span></div><div><strong>${r.weather_flags_total}</strong><span>Range flags</span></div></div><p class="help">Missing after review: ${r.missing_values_after} · Data age: unknown</p><div class="decision-list">${r.decisions.map(d=>`<div class="decision"><span class="tag">${escapeHtml(d.action.toUpperCase())}</span>${escapeHtml(d.rule)} · ${d.rows_affected} rows<p>${escapeHtml(d.reason)}</p></div>`).join('')||'<p class="help">No decisions recorded. This does not establish a complete quality audit.</p>'}</div><p class="help">${r.integration_notes.map(escapeHtml).join('<br>')}</p>`;$('qualityState').textContent=result.saved_run?'SAVED AGENT RUN':'REVIEW READY';$('qualityDownloads').hidden=false;
 }catch(e){$('qualityResult').innerHTML='<div class="error">Quality agent unavailable: '+escapeHtml(e.message)+'</div>';$('qualityState').textContent='UNAVAILABLE';}
 finally{button.disabled=false;$('csvFile').disabled=false;$('resetFile').disabled=false;}
});
$('approveCleaned').addEventListener('change',()=>{$('downloadCleaned').disabled=!$('approveCleaned').checked;});$('downloadCleaned').addEventListener('click',()=>{if(qualityResult&&$('approveCleaned').checked)download(qualityResult.cleaned,'heatshift-reviewed-cleaned.csv','text/csv');});$('downloadQuality').addEventListener('click',()=>{if(qualityResult)download(qualityResult.report,'heatshift-quality-report.json');});
document.querySelectorAll('[data-question]').forEach(b=>b.addEventListener('click',()=>{$('question').value=b.dataset.question;}));
$('askInsight').addEventListener('click',async()=>{const question=$('question').value.trim(),selected=city.value;if(!question){$('insightResult').textContent='Enter a question first.';return;}const button=$('askInsight');button.disabled=true;$('insightResult').textContent='Loading the original Insight Agent and selected training table…';
 try{const r=await agents('insight',selected,question);if(city.value!==selected)throw Error('City changed. Ask again for the selected city.');const a=r.answer;$('insightResult').innerHTML=`<span class="eyebrow">${r.saved_run?'SAVED ORIGINAL-AGENT RUN · ':''}${a.supported?'EVIDENCE-BASED SUMMARY':'INSUFFICIENT EVIDENCE'}</span><p>${escapeHtml(a.answer)}</p><p class="help">${r.saved_run?'Saved run: '+escapeHtml(r.timestamp)+' (agent clock, zone unstated)<br>':''}${escapeHtml(r.scope)}<br>${escapeHtml(r.data_start_utc)} to ${escapeHtml(r.data_end_utc)} · ${r.rows.toLocaleString()} rows<br>Scope check: ${escapeHtml(r.policy?.intent||'legacy')} · Citation validation: ${r.citations_valid?'passed':'failed'}</p>${a.citations.length?'<div class="citations">VERIFIED SOURCE REFERENCES<br>'+a.citations.map(c=>'<span class="citation">'+escapeHtml(c.gold_row_id||c.row_id)+'</span>').join('')+'</div>':''}${r.gold_table?'<p class="help">Gold table SHA-256: '+escapeHtml(r.gold_table.sha256)+'</p><a class="text-link" href="'+escapeHtml(r.gold_table.file)+'" download>Download the cited canonical table ↗</a>':''}<button id="insightDownload" class="button secondary">Download cited answer ↓</button>`;$('insightDownload').addEventListener('click',()=>download(r,'heatshift-'+selected.toLowerCase()+'-insight.json'));}
 catch(e){$('insightResult').innerHTML='<div class="error">Insight agent unavailable: '+escapeHtml(e.message)+'</div>';}
 finally{button.disabled=false;}
});
const observer=new IntersectionObserver(entries=>{for(const e of entries)if(e.isIntersecting){document.querySelectorAll('.sidebar nav a').forEach(a=>{const active=a.hash==='#'+e.target.id;a.classList.toggle('active',active);if(active)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');});}},{rootMargin:'-5% 0px -65% 0px'});document.querySelectorAll('main section[id]').forEach(s=>observer.observe(s));

let latestPipeline=null;
function pipelineView(){
 const target=$('pipelineResults'),button=$('usePipelineObservation');if(!target)return;
 button.disabled=true;button.textContent='Latest automatic observation unavailable';
 if(!latestPipeline){target.innerHTML='';$('lastSuccess').textContent='Last successful run unavailable.';return;}
 const d=latestPipeline;const age=(Date.now()-new Date(d.generated_at_utc).getTime())/3600000;
 const stale=!Number.isFinite(age)||age<0||age>2;
 $('pipelineStatus').textContent=(stale?'STALE · ':'Fresh snapshot · ')+fmtDate(d.generated_at_utc)+' · '+d.status+(d.bundled?' · bundled copy; live repository unavailable':' · operational repository verified');
 const success=d.last_successful_run;
 $('lastSuccess').textContent=success?'Last successful run: '+fmtDate(success.finished_at_utc):'Last successful run not provided by this snapshot.';
 if(success?.run_url&&/^https:\/\/github\.com\/waleedirfan2006-arch\/Heat-Shift-\/actions\/runs\/\d+$/.test(success.run_url)){
  $('lastSuccess').innerHTML+=' <a class="text-link" target="_blank" rel="noreferrer" href="'+escapeHtml(success.run_url)+'">View verified run ↗</a>';
 }
 target.innerHTML='<div class="table-scroll"><table><thead><tr><th>City</th><th>Observed at (PKT)</th><th>Temperature</th><th>24-hour estimate</th><th>Quality</th><th>Freshness / status</th></tr></thead><tbody>'+Object.entries(d.cities||{}).map(([name,r])=>{
  const readingAge=(Date.now()-new Date(r.observation_utc).getTime())/3600000;
  const valid=r.status==='ready'&&Number.isFinite(r.prediction_c)&&Number.isFinite(r.observed_temperature_c);
  const outdated=stale||!Number.isFinite(readingAge)||readingAge<0||readingAge>4;
  return '<tr><td>'+escapeHtml(name)+'</td><td>'+(r.observation_utc?escapeHtml(fmtDate(r.observation_utc)):'Unavailable')+'</td><td>'+(valid?r.observed_temperature_c.toFixed(1)+' °C':'Unavailable')+'</td><td>'+(valid?r.prediction_c.toFixed(1)+' °C':'Unavailable')+'</td><td>'+escapeHtml(r.quality_status||'unavailable')+'</td><td>'+escapeHtml(valid?(outdated?'stale':Math.round(readingAge*60)+' min old'):r.error||r.status)+'</td></tr>';
 }).join('')+'</tbody></table></div>';
 const row=d.cities?.[city.value];const readingAge=row?(Date.now()-new Date(row.observation_utc).getTime())/3600000:Infinity;
 if(!stale&&row?.status==='ready'&&Number.isFinite(row.observed_temperature_c)&&Number.isFinite(row.prediction_c)&&readingAge>=0&&readingAge<=4){button.disabled=false;button.textContent='Use latest '+row.icao+' observation · '+fmtDate(row.observation_utc);}
}
async function loadPipeline(){
 $('refreshPipeline').disabled=true;
 try{const r=await fetch('https://raw.githubusercontent.com/waleedirfan2006-arch/Heat-Shift-/heatshift-runtime/runtime/latest.json?at='+Date.now(),{cache:'no-store',signal:AbortSignal.timeout(12000)});if(!r.ok)throw Error();latestPipeline=await r.json();}
 catch(e){try{const r=await fetch('latest_pipeline.json');if(!r.ok)throw Error();latestPipeline={...await r.json(),bundled:true};}catch{latestPipeline=null;$('pipelineStatus').textContent='Hourly snapshot unavailable. No live data is assumed.';}}
 finally{pipelineView();$('refreshPipeline').disabled=false;}
}
$('refreshPipeline').addEventListener('click',loadPipeline);city.addEventListener('change',pipelineView);
$('usePipelineObservation').addEventListener('click',()=>{const r=latestPipeline?.cities?.[city.value];if(!r||$('usePipelineObservation').disabled)return;clearForecast();$('temperature').value=r.observed_temperature_c;$('observedAt').value=new Date(new Date(r.observation_utc).getTime()+5*3600000).toISOString().slice(0,16);$('metar').value=r.metar||'';observationOrigin='automatic GitHub pipeline; AWC METAR';$('forecastStatus').textContent='Automatic observation filled. Review the values and run a forecast.';});
loadPipeline();
setInterval(()=>{if(!document.hidden)loadPipeline();},60000);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)loadPipeline();});
