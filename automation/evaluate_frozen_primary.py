from pathlib import Path
import sys,json,gzip,hashlib,urllib.request,urllib.parse,concurrent.futures,subprocess,csv,time,math
from datetime import datetime,timezone
import pandas as pd
import numpy as np
repo=Path(__file__).resolve().parents[1]
out=repo/'evidence/final_audit/primary_model'
out.mkdir(parents=True,exist_ok=True)
cfg={'Karachi':(25,67.25),'Lahore':(31.5,74.25),'Multan':(30.25,71.5)}
fields=[n+'_previous_day1' for n in ['temperature_2m','relative_humidity_2m','dew_point_2m','apparent_temperature','precipitation','cloud_cover','wind_speed_10m','wind_direction_10m','surface_pressure','pressure_msl']]
receipts=[]
def fetch(city):
    lat,lon=cfg[city]
    params={'latitude':lat,'longitude':lon,'models':'jma_gsm','hourly':','.join(fields),'start_date':'2024-01-02','end_date':'2024-03-31','timezone':'UTC','temperature_unit':'celsius','wind_speed_unit':'kmh'}
    url='https://previous-runs-api.open-meteo.com/v1/forecast?'+urllib.parse.urlencode(params)
    p=out/(city.lower()+'_jma_2024.json.gz')
    receipt_path=out/(city.lower()+'_receipt.json')
    if p.exists() and receipt_path.exists():return city,json.loads(gzip.decompress(p.read_bytes())),json.loads(receipt_path.read_text())
    request=urllib.request.Request(url,headers={'User-Agent':'HeatShift-Audit/1.0'})
    data=urllib.request.urlopen(request,timeout=90).read()
    payload=json.loads(data)
    if payload.get('error'):raise ValueError(payload)
    receipt={'source_url':url,'fetched_at_utc':datetime.now(timezone.utc).isoformat(),'response_sha256':hashlib.sha256(data).hexdigest(),'city':city,'purpose':'Frozen-model validation and separate calibration; no fitting or selection','original_historical_arrival':'unknown; current archive revision'}
    p.write_bytes(gzip.compress(data,mtime=0));receipt_path.write_text(json.dumps(receipt,indent=2))
    print('Fetched archived JMA:',city,flush=True)
    return city,payload,receipt
archive={}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    for city,payload,receipt in pool.map(fetch,cfg):archive[city]=payload;receipts.append(receipt)
frames=[]
for split in ('validation','calibration'):
    df=pd.read_csv(repo/'HeatShift_Warehouse/02_final'/f'{split}.csv',dtype={'station_id':str})
    df['partition']=split;frames.append(df)
frame=pd.concat(frames,ignore_index=True)
packets=[];missing=[]
for r in frame.to_dict('records'):
    h=archive[r['city']]['hourly'];label=r['target_time_utc'][:16]
    try:i=h['time'].index(label)
    except ValueError:missing.append(r['example_id']);continue
    values={f:h.get(f,[None]*len(h['time']))[i] for f in fields}
    if values[fields[0]] is None or sum(v is not None for v in values.values())<8:missing.append(r['example_id']);continue
    packets.append({'example_id':r['example_id'],'city':r['city'],'partition':r['partition'],'observation_utc':r['prediction_time_utc'],'target_utc':r['target_time_utc'],'input_temperature_c':int(round(r['temp_c'])),'baseline_raw_c':r['temp_c'],'target_c':r['target_temp_24h_c'],'weather_values':values})
packet_path=out/'_inference_inputs.tmp.json';packet_path.write_text(json.dumps(packets))
engine=json.loads(subprocess.check_output(['node',str(repo/'automation/inference_batch.js'),str(packet_path)],text=True))
packet_path.unlink(missing_ok=True)
rows=pd.DataFrame([{k:v for k,v in r.items() if k!='weather_values'} for r in engine['results']])
for pred,col in [('prediction_c','model_abs_error_c'),('baseline_raw_c','baseline_abs_error_c'),('input_temperature_c','rounded_baseline_abs_error_c')]:rows[col]=(rows[pred]-rows.target_c).abs()
rows['month']=pd.to_datetime(rows.target_utc,utc=True).dt.strftime('%Y-%m')
rows.to_csv(out/'row_predictions.csv',index=False)
def score(df):return {'examples':len(df),'model_mae_c':float(df.model_abs_error_c.mean()),'declared_raw_baseline_mae_c':float(df.baseline_abs_error_c.mean()),'rounded_station_baseline_mae_c':float(df.rounded_baseline_abs_error_c.mean()),'improvement_c':float((df.baseline_abs_error_c-df.model_abs_error_c).mean())}
val=rows[rows.partition=='validation'];cal=rows[rows.partition=='calibration']
daily=val.assign(day=pd.to_datetime(val.target_utc,utc=True).dt.date).groupby('day')[['baseline_abs_error_c','model_abs_error_c']].agg(['sum','count'])
days=list(daily.index);rng=np.random.default_rng(20261021);improvements=[]
for _ in range(2000):
    selected=[]
    while len(selected)<len(days):
        start=int(rng.integers(0,len(days)));selected.extend(days[(start+j)%len(days)] for j in range(7))
    chosen=daily.loc[selected[:len(days)]]
    improvements.append(float((chosen[('baseline_abs_error_c','sum')].sum()-chosen[('model_abs_error_c','sum')].sum())/chosen[('model_abs_error_c','count')].sum()))
bands={}
for city,g in cal.groupby('city'):
    errors=sorted(g.model_abs_error_c);q=errors[min(len(errors),math.ceil((len(errors)+1)*.9))-1]
    bands[city]={'calibration_examples':len(g),'half_width_c':q,'calibration_coverage':float((g.model_abs_error_c<=q).mean())}
metrics={'model_source_sha256':engine['model_source_sha256'],'frozen_model_changed':False,'validation':score(val),'by_city':{c:score(g) for c,g in val.groupby('city')},'by_month':{c:score(g) for c,g in val.groupby('month')},'seven_day_block_bootstrap_95pct_improvement_interval_c':np.quantile(improvements,[.025,.975]).tolist(),'calibration_bands':bands,'input_rows':len(frame),'missing_feature_rows':len(missing),'missing_example_ids':missing,'inference_ms':engine['inference_ms'],'node_heap_used_bytes':engine['node_heap_used_bytes'],'baseline_definition':'current raw NOAA temperature, identical scored rows','model_precision':'Python round to whole degrees, then current rounded station temperature plus frozen residual','limitations':['Validation was previously used during development; this is not a new untouched final test.','Archived JMA responses fetched now may differ from original historical versions.','No original training feature rows or training search for this JMA artifact were supplied.','City calibration uses March only; time dependence means future coverage is not guaranteed.','Locked test, replay and reserve files were not opened or scored.']}
(out/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
(out/'receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
print(json.dumps(metrics,indent=2),flush=True)
