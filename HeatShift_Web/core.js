(function(root){
'use strict';
const cities={Karachi:{icao:'OPKC',station:'41780099999',lat:25,lon:67.25,q90:2.066},Lahore:{icao:'OPLA',station:'41640099999',lat:31.5,lon:74.25,q90:2.830},Multan:{icao:'OPMT',station:'41675099999',lat:30.25,lon:71.5,q90:2.809}};
const fields=['temperature_2m','relative_humidity_2m','dew_point_2m','apparent_temperature','precipitation','cloud_cover','wind_speed_10m','wind_direction_10m','surface_pressure','pressure_msl'].map(x=>x+'_previous_day1');
function validate(city,temp,stamp,now=Date.now()){
 if(!cities[city])throw Error('Choose Karachi, Lahore or Multan.');
 if(String(temp).trim()==='')throw Error('Enter the observed temperature.');
 const value=Number(temp);
 if(!Number.isFinite(value)||!Number.isInteger(value)||value < -60||value>60)throw Error('Use a whole-number station temperature from −60 to 60 °C.');
 if(!/^\d{4}-\d{2}-\d{2}T\d{2}:00$/.test(stamp))throw Error('Use an exact on-the-hour observation time. Do not round a report time.');
 const time=new Date(stamp+':00+05:00');
 if(!Number.isFinite(time.getTime())||new Date(time.getTime()+5*3600000).toISOString().slice(0,16)!==stamp)throw Error('Check the observation date.');
 const age=(now-time.getTime())/3600000;
 if(age<0||age>4)throw Error('Use an observation from the last four hours, not a future time.');
 return {city,temperature:value,observation:time,target:new Date(time.getTime()+24*3600000)};
}
function parseMetar(text,city,now=Date.now()){
 const cfg=cities[city];const tokens=text.trim().toUpperCase().split(/\s+/);
 if(!cfg||!tokens.includes(cfg.icao))throw Error('The report must match the selected airport station.');
 if(tokens.filter(x=>/^\d{6}Z$/.test(x)).length!==1)throw Error('Paste one report at a time.');
 const stamp=tokens.find(x=>/^\d{6}Z$/.test(x));const temperature=tokens.find(x=>/^(M?\d{2})\/(M?\d{2}|\/)$/.test(x));
 if(!stamp||!temperature)throw Error('Could not find a DDHHMMZ time and temperature/dew-point group. Enter the values manually.');
 const day=Number(stamp.slice(0,2)),hour=Number(stamp.slice(2,4)),minute=Number(stamp.slice(4,6));
 if(minute!==0||hour>23||day<1||day>31)throw Error('Use an on-the-hour report; do not round a different report time.');
 const n=new Date(now);const candidates=[-1,0].map(offset=>new Date(Date.UTC(n.getUTCFullYear(),n.getUTCMonth()+offset,day,hour,minute))).filter(d=>d.getUTCDate()===day&&d.getTime()<=now&&now-d.getTime()<=4*3600000);
 if(candidates.length!==1)throw Error('This report is too old, future-dated, or has an ambiguous date.');
 const raw=temperature.split('/')[0];const value=raw.startsWith('M')?-Number(raw.slice(1)):Number(raw);
 const dew=temperature.split('/')[1]; const dewpoint=/^M?\d{2}$/.test(dew)?(dew.startsWith('M')?-Number(dew.slice(1)):Number(dew)):null;
 const wind=tokens.find(x=>/^(\d{3}|VRB)\d{2,3}(?:G\d{2,3})?KT$/.test(x));const match=wind?.match(/^(\d{3}|VRB)(\d{2,3})(?:G\d{2,3})?KT$/);
 const windSpeed=match?Number(match[2]):null;const windDirection=match&&match[1]!=='VRB'&&windSpeed!==0?Number(match[1]):null;
 return {temperature:value,stamp:new Date(candidates[0].getTime()+5*3600000).toISOString().slice(0,16),dewpoint,windSpeed,windDirection};
}
function weatherValues(payload,target){
 if(payload.error)throw Error(String(payload.reason||'Weather service error'));
 const idx=(payload.hourly?.time||[]).indexOf(target.toISOString().slice(0,16));
 if(idx<0)throw Error('The JMA service did not return the requested hour.');
 const values={};for(const name of fields){const v=payload.hourly[name]?.[idx];values[name]=typeof v==='number'&&Number.isFinite(v)?v:null;}
 const available=fields.filter(x=>values[x]!==null).length;
 if(values.temperature_2m_previous_day1===null||available<8)throw Error(`Only ${available}/10 required JMA fields were returned. Try later or explicitly choose baseline-only mode.`);
 return {values,available};
}
function row(input,values){const local=new Date(input.observation.getTime()+5*3600000);const hour=local.getUTCHours();const day=Math.floor((Date.UTC(local.getUTCFullYear(),local.getUTCMonth(),local.getUTCDate())-Date.UTC(local.getUTCFullYear(),0,1))/86400000)+1;return {station_temp_input_c:input.temperature,hour_sin:Math.sin(2*Math.PI*hour/24),hour_cos:Math.cos(2*Math.PI*hour/24),year_sin:Math.sin(2*Math.PI*(day-1)/365.2425),year_cos:Math.cos(2*Math.PI*(day-1)/365.2425),station_id:cities[input.city].station,hour_pk:String(hour),month_pk:String(local.getUTCMonth()+1),...values};}
function stationWeatherRow(input,dew,speed,direction){
 if(String(dew).trim()===''||String(speed).trim()==='')throw Error('Paste a full METAR report, or enter dew point and wind speed.');
 const d=Number(dew),w=Number(speed);let angle=String(direction).trim()===''?null:Number(direction);
 if(!Number.isInteger(d)||d < -98||d>37||!Number.isInteger(w)||w<0||w>175)throw Error('Check the dew point and wind speed from the station report.');
 if(angle!==null&&(!Number.isInteger(angle)||angle<1||angle>360))throw Error('Use wind direction 1–360 degrees, or leave it blank for variable wind.');
 if(w===0)angle=null;
 const calendar=row(input,{});
 return {current_c:input.temperature,dew_c:d,dew_spread_c:input.temperature-d,wind_kt:w,wind_sin:angle===null?null:Math.sin(angle*(Math.PI/180)),wind_cos:angle===null?null:Math.cos(angle*(Math.PI/180)),dew_missing:0,wind_missing:0,hour_sin:calendar.hour_sin,hour_cos:calendar.hour_cos,year_sin:calendar.year_sin,year_cos:calendar.year_cos,karachi:input.city==='Karachi'?1:0,lahore:input.city==='Lahore'?1:0,multan:input.city==='Multan'?1:0};
}
const api={cities,fields,validate,parseMetar,weatherValues,row,stationWeatherRow};root.HeatShiftCore=api;if(typeof module!=='undefined')module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
