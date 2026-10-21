"""Hourly acquisition -> original quality agent -> frozen model -> cited insights.

No model fitting, no held-out data, and no modification of vendor agent code.
"""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.request import Request,urlopen
from urllib.parse import urlencode,urlparse,parse_qs
import argparse,csv,hashlib,json,sqlite3,subprocess,sys,time,shutil
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'HeatShift_Unified_Space'))
from integration import run_quality,_load_agent
CONFIG={'Karachi':('OPKC',25,67.25),'Lahore':('OPLA',31.5,74.25),'Multan':('OPMT',30.25,71.5)}
FIELDS=[n+'_previous_day1' for n in ['temperature_2m','relative_humidity_2m','dew_point_2m','apparent_temperature','precipitation','cloud_cover','wind_speed_10m','wind_direction_10m','surface_pressure','pressure_msl']]

def fetch(url,path,manifest):
    stamp=datetime.now(timezone.utc).isoformat()
    req=Request(url,headers={'User-Agent':'HeatShift-Hourly/1.0'})
    with urlopen(req,timeout=40) as response:data=response.read()
    path.write_bytes(data)
    manifest.append({'file':path.name,'source_url':url,'source':'Aviation Weather Center' if 'aviationweather.gov' in url else 'Open-Meteo JMA GSM previous-runs','query':json.dumps(parse_qs(urlparse(url).query),sort_keys=True),'fetched_at_utc':stamp,'sha256':hashlib.sha256(data).hexdigest(),'licence':'NOAA public information; source terms apply' if 'aviationweather.gov' in url else 'CC BY 4.0 data; separate API commercial-use terms apply','licence_url':'https://www.weather.gov/disclaimer' if 'aviationweather.gov' in url else 'https://open-meteo.com/en/terms','bytes':len(data),'status':'retrieved'})
    return json.loads(data)

def _run(output):
    started=time.perf_counter();now=datetime.now(timezone.utc)
    for name in ('raw','cleaned','processed'): (output/name).mkdir(parents=True,exist_ok=True)
    # Reusing an output directory must never make an old table look newly fetched.
    for previous in (output/'cleaned').glob('*_cleaned.csv'):
        if not previous.resolve().is_relative_to(output.resolve()):raise ValueError('Unsafe output path')
        previous.unlink()
    manifest=[];errors=[];quality=[];cities={};packets=[];insights=[]
    url='https://aviationweather.gov/api/data/metar?'+urlencode({'ids':','.join(v[0] for v in CONFIG.values()),'format':'json','hours':8})
    try:reports=fetch(url,output/'raw/metar.json',manifest)
    except Exception as error:reports=[];errors.append({'stage':'METAR acquisition','error':str(error)})
    for city,(icao,lat,lon) in CONFIG.items():
        try:
            all_rows=[];eligible=[]
            for r in reports:
                if r.get('icaoId')!=icao:continue
                try:stamp=datetime.fromtimestamp(int(r['obsTime']),timezone.utc);temp=float(r['temp'])
                except (KeyError,TypeError,ValueError,OverflowError):continue
                all_rows.append({'time':stamp.isoformat(),'temperature_c':temp,'source_row_id':f"{icao}:{int(r['obsTime'])}"})
                if stamp.minute==0 and timedelta(0)<=now-stamp<=timedelta(hours=4) and temp.is_integer() and -60<=temp<=60:eligible.append((stamp,temp,r))
            if not eligible:raise ValueError('No valid exact-hour station report from the last four hours.')
            stamp,temp,report=max(eligible,key=lambda x:x[0]);target=stamp+timedelta(hours=24)
            q,cleaned=run_quality(pd.DataFrame(all_rows).to_csv(index=False).encode(),city.lower()+'_live.csv')
            quality.append({'city':city,**q});cleanfile=output/'cleaned'/f'{city.lower()}_cleaned.csv';cleanfile.write_bytes(cleaned)
            params={'latitude':lat,'longitude':lon,'models':'jma_gsm','hourly':','.join(FIELDS),'start_date':target.date().isoformat(),'end_date':target.date().isoformat(),'timezone':'UTC','temperature_unit':'celsius','wind_speed_unit':'kmh'}
            w=fetch('https://previous-runs-api.open-meteo.com/v1/forecast?'+urlencode(params),output/'raw'/f'{city.lower()}_jma.json',manifest)
            if w.get('error'):raise ValueError(w.get('reason'))
            h=w['hourly'];i=h['time'].index(target.strftime('%Y-%m-%dT%H:%M'));values={f:h.get(f,[None]*len(h['time']))[i] for f in FIELDS}
            if values[FIELDS[0]] is None or sum(v is not None for v in values.values())<8:raise ValueError('Insufficient JMA fields; no forecast substituted.')
            packets.append({'city':city,'input_temperature_c':int(temp),'observation_utc':stamp.isoformat(),'target_utc':target.isoformat(),'weather_values':values})
            cities[city]={'status':'ready','icao':icao,'observation_utc':stamp.isoformat(),'target_utc':target.isoformat(),'observed_temperature_c':temp,'baseline_c':temp,'metar':report.get('rawOb'),'jma_fields':sum(v is not None for v in values.values()),'observation_source':'AWC METAR API; automatic pipeline','quality_status':'review required' if any(d.get('action')=='flag' for d in q['decisions']) else 'checks completed','quality':{k:q[k] for k in ['rows_before','rows_after','duplicates_removed','values_filled','weather_flags_total','missing_values_after']}}
        except Exception as error:cities[city]={'status':'unavailable','error':str(error)};errors.append({'city':city,'stage':'city pipeline','error':str(error)})
    if packets:
        try:
            packet_path=output/'processed/inference_inputs.json';packet_path.write_text(json.dumps(packets),encoding='utf-8')
            result=json.loads(subprocess.check_output(['node',str(ROOT/'automation/inference_batch.js'),str(packet_path)],text=True))
            for row in result['results']:cities[row['city']].update({'prediction_c':row['prediction_c'],'model_sha256':row['model_sha256']})
        except Exception as error:
            errors.append({'stage':'frozen inference','error':str(error)})
            for packet in packets:
                cities[packet['city']].update({'status':'unavailable','error':'Frozen inference failed. No prediction substituted.'})
    for city,row in cities.items():
        if row['status']=='ready' and 'prediction_c' not in row:
            row.update({'status':'unavailable','error':'No verified model output available.'})
            errors.append({'city':city,'stage':'inference','error':row['error']})
    if list((output/'cleaned').glob('*_cleaned.csv')):
        agent_class=_load_agent('insight_agent.py','InsightAgent');agent=agent_class.__new__(agent_class)
        agent.project_dir=output;agent.processed_dir=output/'cleaned';agent.docs_dir=output/'no_document_numbers';agent.docs_dir.mkdir(exist_ok=True);agent.report_dir=output/'processed';agent.retriever=None;agent.data_store=None
        # Fixed machine summary: numeric claims use current canonical cleaned tables only.
        insight=agent.ask('Summarize recorded weather temperature and uncertainty.')
        insight['gold_tables']=[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rows':len(pd.read_csv(p))} for p in (output/'cleaned').glob('*_cleaned.csv')]
        insight['answer']['answer']=insight['answer']['answer'].split(' This is information,')[0]
        for c in insight['answer']['citations']:
            path=Path(c['source']);c['source']=path.name;c['source_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            suffix=c['row_id'].rsplit(':',1)[-1]
            if suffix!='aggregate':c['gold_row_id']=pd.read_csv(path).iloc[int(suffix)]['source_row_id']
        (output/'processed/insight_report.json').write_text(json.dumps(insight,indent=2,default=str))
    (output/'processed/quality_log.json').write_text(json.dumps(quality,indent=2,default=str))
    with (output/'manifest.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['file','source','source_url','query','fetched_at_utc','sha256','licence','licence_url','bytes','status']);writer.writeheader();writer.writerows(manifest)
    with sqlite3.connect(output/'warehouse.sqlite') as db:
        pd.DataFrame(manifest,columns=['file','source','source_url','query','fetched_at_utc','sha256','licence','licence_url','bytes','status']).to_sql('raw_manifest',db,if_exists='replace',index=False)
        for city in CONFIG:
            p=output/'cleaned'/f'{city.lower()}_cleaned.csv'
            if p.exists():pd.read_csv(p).to_sql(city.lower()+'_cleaned',db,if_exists='replace',index=False)
        pd.DataFrame([{'city':c,**{k:(json.dumps(value) if isinstance(value,(dict,list)) else value) for k,value in v.items()}} for c,v in cities.items()]).to_sql('latest_predictions',db,if_exists='replace',index=False)
    db.close()
    latest={'generated_at_utc':datetime.now(timezone.utc).isoformat(),'status':'ok' if not errors else 'partial' if any(r.get('status')=='ready' for r in cities.values()) else 'failed','cities':cities,'errors':errors,'elapsed_seconds':time.perf_counter()-started,'model_retrained':False,'scheduler':'GitHub Actions hourly, at minute 17 UTC; delays possible','raw_cleaned_processed_evidence':'GitHub Actions run artifact','scheduler_evidence':'GitHub Actions; no historical Prefect export supplied','quality_status':'review required' if quality else 'unavailable','data_quality_agent':'original source, fingerprint verified','insight_agent':'original source with trusted document retrieval and citations'}
    (output/'latest.json').write_text(json.dumps(latest,indent=2,default=str)+'\n')
    print(json.dumps(latest,indent=2),flush=True)
    return 0 if not errors else 1

def run(output):
    try:
        return _run(output)
    except Exception as error:
        output.mkdir(parents=True,exist_ok=True)
        latest={'generated_at_utc':datetime.now(timezone.utc).isoformat(),'status':'failed',
                'cities':{c:{'status':'unavailable','error':'Pipeline failed before a verified final result.'} for c in CONFIG},
                'errors':[{'stage':'unexpected pipeline failure','error':str(error)}],
                'quality_status':'unavailable','model_retrained':False}
        (output/'latest.json').write_text(json.dumps(latest,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(latest,indent=2),flush=True)
        return 1

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=ROOT/'automation/runs');args=parser.parse_args();sys.exit(run(args.output.resolve()))
