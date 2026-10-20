"""Recommended independent quality/leakage audit. No model training or scoring."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, csv, hashlib, json, platform, sys, zipfile, importlib.util
import numpy as np
import pandas as pd
STATIONS={'41780099999':'Karachi','41640099999':'Lahore','41675099999':'Multan'}
FIELDS={'temperature_2m (°C)':('temperature_c',-100,65),'relative_humidity_2m (%)':('relative_humidity_pct',0,100),'dew_point_2m (°C)':('dew_point_c',-100,65),'surface_pressure (hPa)':('surface_pressure_hpa',1,1200),'cloud_cover (%)':('cloud_cover_pct',0,100),'wind_speed_10m (km/h)':('wind_speed_10m_kmh',0,500),'shortwave_radiation (W/m²)':('shortwave_radiation_wm2',0,1600)}
WINDOWS=[('train','2022-01-01','2024-01-01'),('validation','2024-01-01','2024-03-01'),('calibration','2024-03-01','2024-04-01'),('test_locked','2024-04-01','2024-10-01'),('replay','2024-10-01','2025-01-01'),('reserve_2025','2025-01-01','2026-01-01')]
FEATURES={'station_id','temp_c','temp_lag24_c','temp_lag48_c','lag24_missing','lag48_missing','hour_pk','month_pk'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return pd.read_csv(p,dtype={'station_id':str})
def utc(s):return pd.to_datetime(s,utc=True,errors='raise')
def run(root,out):
 out.mkdir(parents=True,exist_ok=True); checks=[];profiles=[];missing=[];ns=[];os=[]
 def check(name,good):checks.append({'check':name,'result':'PASS' if bool(good) else 'FAIL'})
 m=json.loads((root/'manifest.json').read_text())
 with (root/'manifest.csv').open(newline='',encoding='utf-8') as f:mc=list(csv.DictReader(f))
 check('manifest unique paths',len({x['raw_file'] for x in m})==len(m))
 check('CSV/JSON manifest agreement',{x['raw_file']:x['sha256'] for x in m}=={x['raw_file']:x['sha256'] for x in mc})
 check('raw directory exact file set',{x['raw_file'] for x in m}=={p.relative_to(root).as_posix() for p in (root/'00_raw').glob('*.csv')})
 with zipfile.ZipFile(root/'source_snapshots.zip') as z:
  check('ZIP integrity',z.testzip() is None)
  for x in m:
   p=root/x['raw_file']; op=x['source']=='open_meteo';raw=pd.read_csv(p,skiprows=3 if op else 0,dtype=str,keep_default_na=False)
   t=utc(raw['time' if op else 'DATE']);ids=[x['sha256']+':'+str(i+1) for i in range(len(raw))]
   check('raw hash '+p.name,sha(p)==x['sha256']);check('snapshot hash '+p.name,hashlib.sha256(z.read(x['raw_file'])).hexdigest()==x['sha256'])
   check('raw row count '+p.name,len(raw)==x['raw_rows']);check('raw date bounds '+p.name,t.min()==pd.Timestamp(x['event_start_utc']) and t.max()==pd.Timestamp(x['event_end_utc']))
   check('hour aligned '+p.name,(t.dt.minute.eq(0)&t.dt.second.eq(0)).all())
   profiles.append({'file':p.name,'rows':len(raw),'exact_duplicate_rows':int(raw.duplicated().sum()),'first_utc':t.min().isoformat(),'last_utc':t.max().isoformat()})
   d=pd.DataFrame({'raw_row_id':ids,'city':x['city'],'event_time_utc':t,'source_file':x['raw_file'],'source_record_number':range(1,len(raw)+1)})
   if op:
    meta=pd.read_csv(p,nrows=1).iloc[0].to_dict()
    check('metadata '+p.name,meta==x['export_metadata']);check('timezone '+p.name,meta['utc_offset_seconds']==0 and meta['timezone']=='GMT')
    check('schema '+p.name,set(raw)=={'time',*FIELDS})
    check('complete hourly timeline '+p.name,list(t)==list(pd.date_range('2022-01-01','2024-12-31 23:00',freq='h',tz='UTC')))
    for old,(new,lo,hi) in FIELDS.items():
     v=pd.to_numeric(raw[old],errors='coerce');bad=v.notna()&(~np.isfinite(v)|~v.between(lo,hi));d[new]=v.mask(bad)
     missing.append({'file':p.name,'field':new,'missing':int(v.isna().sum()),'out_of_range':int(bad.sum())})
     check('finite/range '+p.name+' '+new,not bad.any())
    d.loc[d.dew_point_c>d.temperature_c+0.2,'dew_point_c']=np.nan;os.append(d)
   else:
    check('station identity '+p.name,raw.STATION.nunique()==1 and STATIONS.get(raw.STATION.iloc[0])==x['city'])
    check('TMP syntax '+p.name,raw.TMP.str.fullmatch(r'[+-]\d{4},[0-9A-Z]').all())
    tmp=raw.TMP.str.split(',',expand=True);v=pd.to_numeric(tmp[0],errors='raise')/10;qc=tmp[1]
    keep=v.ne(999.9)&qc.isin(['0','1','4','5'])&v.between(-93.2,61.8)
    d['station_id']=raw.STATION;d['temp_c']=v;d['qrank']=qc.map({'1':0,'5':0,'0':1,'4':1});d['rrank']=raw.REPORT_TYPE.map({'FM-12':0,'FM-15':1,'FM-16':2}).fillna(9)
    ns.append(d[keep]);missing.append({'file':p.name,'field':'temp_c','missing':int(v.eq(999.9).sum()),'out_of_range':int((v.ne(999.9)&~v.between(-93.2,61.8)).sum())})
 expected=pd.concat(ns).sort_values(['station_id','event_time_utc','qrank','rrank','source_file','source_record_number'],kind='stable').drop_duplicates(['station_id','event_time_utc']).set_index('raw_row_id')
 n=read(root/'01_clean/noaa_observations.csv');n['event_time_utc']=utc(n.event_time_utc);e=expected.reindex(n.raw_row_id)
 check('independent NOAA selection',set(n.raw_row_id)==set(expected.index));check('clean NOAA unique keys',n.raw_row_id.is_unique and n.row_id.is_unique and not n.duplicated(['station_id','event_time_utc']).any())
 check('NOAA values match original decoding',np.allclose(n.temp_c,e.temp_c));check('NOAA times/stations match original',list(n.event_time_utc)==list(e.event_time_utc) and list(n.station_id)==list(e.station_id))
 op=read(root/'01_clean/open_meteo_context.csv');eo=pd.concat(os).set_index('raw_row_id').reindex(op.raw_row_id)
 check('Open-Meteo exact retained rows',set(op.raw_row_id)==set(pd.concat(os).raw_row_id));check('Open-Meteo unique keys',op.row_id.is_unique and op.raw_row_id.is_unique and not op.duplicated(['city','event_time_utc']).any())
 check('Open-Meteo times/cities match original',list(utc(op.event_time_utc))==list(eo.event_time_utc) and list(op.city)==list(eo.city))
 for new,_,_ in FIELDS.values():check('Open-Meteo independent cleaning '+new,np.allclose(op[new],eo[new],equal_nan=True,atol=1e-6))
 check('context-only flag',op.historical_context_only.eq(1).all())
 rawgold=read(root/'02_final/model_data.csv');g=rawgold.copy();g['prediction_time_utc']=utc(g.prediction_time_utc);g['target_time_utc']=utc(g.target_time_utc);lookup=n.set_index('row_id')
 check('unique examples',g.example_id.is_unique and not g.duplicated(['station_id','prediction_time_utc']).any())
 check('current/target present finite',np.isfinite(g[['temp_c','target_temp_24h_c']]).all().all())
 for col,delta,val in [('current_row_id',0,'temp_c'),('lag24_row_id',-24,'temp_lag24_c'),('lag48_row_id',-48,'temp_lag48_c'),('target_row_id',24,'target_temp_24h_c')]:
  d=g[g[col].notna()];ref=lookup.reindex(d[col]);check(col+' exists',ref.event_time_utc.notna().all());check(col+' station',list(d.station_id)==list(ref.station_id));check(col+' time',list(d.prediction_time_utc+pd.Timedelta(hours=delta))==list(ref.event_time_utc));check(col+' value',np.allclose(d[val],ref.temp_c))
  if delta in [0,24]:check(col+' raw source ID',list(d['current_raw_row_id' if delta==0 else 'target_raw_row_id'])==list(ref.raw_row_id))
 for h in [24,48]:
  check(f'lag{h} missing flag',g[f'lag{h}_missing'].eq(g[f'temp_lag{h}_c'].isna().astype(int)).all());check(f'lag{h} ID missing agreement',g[f'lag{h}_row_id'].isna().equals(g[f'temp_lag{h}_c'].isna()))
 check('baseline fixed',g.baseline_temp_24h_c.eq(g.temp_c).all());check('horizon fixed',g.target_time_utc.sub(g.prediction_time_utc).eq(pd.Timedelta(hours=24)).all())
 pk=g.prediction_time_utc.dt.tz_convert('Asia/Karachi');check('PKT features',g.hour_pk.eq(pk.dt.hour).all() and g.month_pk.eq(pk.dt.month).all())
 labels=pd.Series('outside_plan',index=g.index)
 for label,start,end in WINDOWS:
  s,e=pd.Timestamp(start,tz='UTC'),pd.Timestamp(end,tz='UTC');mask=g.target_time_utc.ge(s)&g.target_time_utc.lt(e);labels.loc[mask]=label
  if label!='train':labels.loc[mask&g.target_time_utc.lt(s+pd.Timedelta(hours=24))]='boundary_gap'
 check('independent split assignments',g.split.equals(labels));parts={};seen=set();counts=[]
 for label in sorted(g.split.unique()):
  p=read(root/'02_final'/f'{label}.csv');parts[label]=p;check('exact partition '+label,p.equals(rawgold[rawgold.split==label].reset_index(drop=True)));check('disjoint examples '+label,not seen.intersection(p.example_id));seen.update(p.example_id)
  for city,d in p.groupby('city'):counts.append({'split':label,'city':city,'rows':len(d),'missing_lag24':int(d.temp_lag24_c.isna().sum()),'missing_lag48':int(d.temp_lag48_c.isna().sum())})
 for prev,nxt in zip(WINDOWS,WINDOWS[1:]):check('label available before next partition '+prev[0],utc(parts[prev[0]].target_time_utc).max()<utc(parts[nxt[0]].prediction_time_utc).min())
 keyset=set(zip(n.station_id,n.event_time_utc));eligible=n.apply(lambda r:(r.station_id,r.event_time_utc+pd.Timedelta(hours=24)) in keyset,axis=1)
 check('all and only eligible examples',set(g.current_row_id)==set(n.loc[eligible,'row_id']));check('missing-target exclusions reconcile',set(read(root/'quality/rows_without_target.csv').current_row_id)==set(n.loc[~eligible,'row_id']))
 contract=json.loads((root/'02_final/model_contract.json').read_text());check('contract feature allowlist',set(contract['features'])==FEATURES)
 tf=root.parent/'HeatShift_Training/train_model.py';sys.path.insert(0,str(tf.parent));spec=importlib.util.spec_from_file_location('training_audit',tf);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 check('training feature allowlist',set(mod.FEATURES)==FEATURES);tr=mod.load_partition(root/'02_final/train.csv');va=mod.load_partition(root/'02_final/validation.csv')
 if hasattr(mod,'validate_partitions'):mod.validate_partitions(tr,va);check('training entry guards',True)
 for idx,(a,b,_,_) in enumerate(mod.chronological_folds(tr),1):check(f'fold {idx} label separation',tr.loc[a,'target_time_utc'].max()<tr.loc[b,'target_time_utc'].min()-pd.Timedelta(hours=24));check(f'fold {idx} disjoint',not (a&b).any())
 pipe=mod.build_model(1.0);check('preprocessing in training pipeline',list(pipe.named_steps)==['prepare_inputs','ridge_regression']);check('median inside pipeline',pipe.named_steps['prepare_inputs'].transformers[0][1].named_steps['fill_missing_lags'].strategy=='median')
 coverage=[]
 for (city,year),d in n.groupby(['city',n.event_time_utc.dt.year]):
  d=d.sort_values('event_time_utc');gaps=d.event_time_utc.diff().dt.total_seconds()/3600;end=d.event_time_utc.max().floor('D')+pd.Timedelta(days=1);hours=int((end-pd.Timestamp(f'{year}-01-01',tz='UTC')).total_seconds()/3600)
  coverage.append({'city':city,'year':int(year),'accepted_readings':len(d),'hourly_reference_slots':hours,'coverage_pct':round(100*len(d)/hours,2),'median_spacing_hours':gaps.median(),'largest_gap_hours':gaps.max(),'conflicting_times':int(d.conflicting_temperature_at_time.sum())})
 for name,rows in [('audit_checks.csv',checks),('raw_profiles.csv',profiles),('raw_missing_and_ranges.csv',missing),('partition_quality.csv',counts),('station_coverage.csv',coverage)]:pd.DataFrame(rows).to_csv(out/name,index=False,lineterminator='\n')
 tr.groupby('city').agg(rows=('temp_c','size'),min_c=('temp_c','min'),max_c=('temp_c','max'),missing_lag24=('lag24_missing','sum'),missing_lag48=('lag48_missing','sum')).to_csv(out/'training_city_profile.csv')
 tr.groupby(['city','month_pk']).size().rename('rows').to_csv(out/'training_city_month_counts.csv')
 import sklearn
 result={'audited_at_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS_WITH_LIMITATIONS' if all(c['result']=='PASS' for c in checks) else 'FAIL','checks_passed':sum(c['result']=='PASS' for c in checks),'checks_failed':sum(c['result']=='FAIL' for c in checks),'raw_files':len(m),'raw_rows':sum(p['rows'] for p in profiles),'clean_noaa':len(n),'clean_open_meteo':len(op),'partitions':{k:len(v) for k,v in parts.items()},'conflicting_selected_noaa_times':int(n.conflicting_temperature_at_time.sum()),'training_missing_lag24':int(tr.temp_lag24_c.isna().sum()),'training_missing_lag48':int(tr.temp_lag48_c.isna().sum()),'allowed_train_targets_reused_as_later_48h_lags':len(set(parts['train'].target_row_id)&set(parts['validation'].lag48_row_id.dropna())),'model_fitted':False,'model_scored':False,'held_out_use':'Structural auditing only; no performance metrics or tuning.','historical_arrival_times':'Unverified; retrospective event-time availability assumption only.','open_meteo_original_collection':'Unverified without collector evidence.','python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__,'sklearn':sklearn.__version__,'input_sha256':{p.relative_to(root.parent).as_posix():sha(p) for p in sorted(root.rglob('*')) if p.is_file() and (p.parent.name in ['00_raw','01_clean','02_final'] or p.name in ['manifest.json','manifest.csv','audit_data.py','pipeline.py','build_warehouse.py'])}}
 for p in [tf,tf.parent/'validate_data.py']:
  if p.exists():result['input_sha256'][p.relative_to(root.parent).as_posix()]=sha(p)
 (out/'audit_results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'},indent=2))
 if result['checks_failed']:print([c for c in checks if c['result']=='FAIL']);raise SystemExit(1)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);a=p.parse_args();r=Path(__file__).resolve().parent;run(r,a.output or r/'audit')
