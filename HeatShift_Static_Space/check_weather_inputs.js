// Verify full browser input construction against recorded real-data predictions.
const fs=require('fs'),zlib=require('zlib'),assert=require('assert');
const C=require('./core.js'),engine=require('./model.js');
const model=JSON.parse(zlib.gunzipSync(fs.readFileSync(__dirname+'/station_weather_model.json.gz')));
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let max=0;
for(const item of rows){const input=C.validate(item.city,String(item.temperature),item.stamp,item.now);const values=C.stationWeatherRow(input,String(item.dewpoint),String(item.windSpeed),item.windDirection===null?'':String(item.windDirection));const prediction=input.temperature+model.residual_weight*engine.predictResidual(values,model);const error=Math.abs(prediction-item.expected);max=Math.max(max,error);if(error>=1e-10){console.log(JSON.stringify({input:item,actual:prediction,error,differing:Object.entries(values).filter(([k,v])=>v!==item.reference_features[k]).map(([k,v])=>[k,v,item.reference_features[k]])},null,2));throw Error('End-to-end browser forecast mismatch');}}
console.log(`Full browser feature construction matches ${rows.length} usable real validation reports; max difference ${max}.`);
