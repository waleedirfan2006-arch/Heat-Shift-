"""Reproducible station-only challenger. Select on training folds, never test sets.
Uses only current station temperature and prediction-time calendar available live.
This is a new experiment, not reconstruction of the older JMA model.
"""
from pathlib import Path
import hashlib,json,time,os,importlib.metadata
os.environ.setdefault('OMP_NUM_THREADS','2')
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error,root_mean_squared_error
from validate_data import validate_partitions

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'HeatShift_Warehouse/02_final'
OUT=Path(__file__).resolve().parent/'station_results'
STATIONS=['41780099999','41640099999','41675099999']

def features(df):
 t=pd.to_datetime(df.prediction_time_utc,utc=True).dt.tz_convert('Asia/Karachi')
 # Keep integer station inputs consistent with manual METAR form.
 temp=np.rint(df.temp_c.to_numpy(float))
 return np.column_stack([temp,np.sin(2*np.pi*t.dt.hour/24),np.cos(2*np.pi*t.dt.hour/24),np.sin(2*np.pi*(t.dt.dayofyear-1)/365.2425),np.cos(2*np.pi*(t.dt.dayofyear-1)/365.2425),*[df.station_id.eq(s).astype(float) for s in STATIONS]])

def estimator(c):
 if c['kind']=='ridge':return make_pipeline(StandardScaler(),Ridge(alpha=c['alpha']))
 return HistGradientBoostingRegressor(loss='absolute_error',max_iter=c['iterations'],max_leaf_nodes=c['leaves'],learning_rate=.05,l2_regularization=10,min_samples_leaf=40,early_stopping=False,random_state=20261021)

def metrics(df,p):
 y=df.target_temp_24h_c.to_numpy();base=df.temp_c.to_numpy()
 return {'examples':len(df),'mae_c':float(mean_absolute_error(y,p)),'rmse_c':float(root_mean_squared_error(y,p)),'baseline_mae_c':float(mean_absolute_error(y,base))}

def main():
 OUT.mkdir(exist_ok=True)
 train=pd.read_csv(DATA/'train.csv',dtype={'station_id':str});val=pd.read_csv(DATA/'validation.csv',dtype={'station_id':str});validate_partitions(train,val)
 X=features(train);y=train.target_temp_24h_c.to_numpy()-train.temp_c.to_numpy();targets=pd.to_datetime(train.target_time_utc,utc=True);issues=pd.to_datetime(train.prediction_time_utc,utc=True)
 # Predeclared expanding folds with label availability strict at validation start.
 windows=[('2022-07-01','2023-01-01'),('2023-01-01','2023-07-01'),('2023-07-01','2024-01-01')]
 folds=[]
 for start,end in windows:
  a=pd.Timestamp(start,tz='UTC');b=pd.Timestamp(end,tz='UTC');fit=np.flatnonzero(targets<a);check=np.flatnonzero((issues>=a)&(targets<b));folds.append((fit,check))
 candidates=[{'id':'persistence','kind':'baseline'}]+[{'id':f'ridge_{a}','kind':'ridge','alpha':a} for a in [1,10,100,1000]]+[{'id':f'hgb_{n}_{l}','kind':'hgb','iterations':n,'leaves':l} for n in [100,250] for l in [7,15]]
 rows=[];cache={};started=time.perf_counter()
 for c in candidates:
  preds=[];truth=[];fold_scores=[]
  for fit,check in folds:
   if c['kind']=='baseline':p=train.temp_c.to_numpy()[check]
   else:
    m=estimator(c);m.fit(X[fit],y[fit]);p=m.predict(X[check])+train.temp_c.to_numpy()[check]
   preds.extend(p);truth.extend(check.tolist());fold_scores.append(metrics(train.iloc[check],p))
  score=metrics(train.iloc[truth],np.array(preds));rows.append({'candidate':c,**score,'folds':fold_scores});cache[c['id']]=(np.array(truth),np.array(preds));print(c['id'],score,flush=True)
 best=min(rows,key=lambda r:r['mae_c']);selected=best['candidate'];idx,p=cache[selected['id']]
 # Final selection is made before validation is scored. No test/replay/reserve access.
 if selected['kind']=='baseline':vp=val.temp_c.to_numpy();fitted=None
 else:
  fitted=estimator(selected);fitted.fit(X,y);vp=fitted.predict(features(val))+val.temp_c.to_numpy()
 if fitted is not None:
  joblib.dump({'model':fitted,'feature_spec':'current_temp_rounded, hour sin/cos, day sin/cos, Karachi/Lahore/Multan one-hot','prediction_mode':'current_plus_residual','candidate':selected},OUT/'station_challenger.joblib')
 by_city={city:metrics(val.loc[mask],vp[mask]) for city in sorted(val.city.unique()) for mask in [val.city.eq(city).to_numpy()]}
 band=float(np.quantile(abs(train.iloc[idx].target_temp_24h_c.to_numpy()-p),.9))
 result={'created_at_utc':pd.Timestamp.now(tz='UTC').isoformat(),'purpose':'station-only fallback; not a replacement for JMA primary','training_rows':len(train),'training_sha256':hashlib.sha256((DATA/'train.csv').read_bytes()).hexdigest(),'validation_sha256':hashlib.sha256((DATA/'validation.csv').read_bytes()).hexdigest(),'selection':'pooled MAE across three expanding training-only folds; baseline eligible','fold_windows':windows,'candidates':rows,'selected':selected,'validation':metrics(val,vp),'validation_by_city':by_city,'historical_oof_q90_half_width_c':band,'validation_band_coverage':float(np.mean(abs(val.target_temp_24h_c.to_numpy()-vp)<=band)),'elapsed_seconds':time.perf_counter()-started,'limitations':['Not a fresh independent final evaluation: this validation period has been examined previously.','Not compared head-to-head against JMA model: archived JMA training inputs absent from repository.','Historical station reports lack original arrival times.','No locked-test, replay or reserve files read.','Do not infer live METAR accuracy from historical NOAA validation alone.']}
 result['environment']={n:importlib.metadata.version(n) for n in ['numpy','pandas','scikit-learn','joblib','scipy','threadpoolctl','python-dateutil','pytz','tzdata','six']}
 (OUT/'requirements.txt').write_text('\n'.join(n+'=='+v for n,v in result['environment'].items())+'\n')
 (OUT/'metrics.json').write_text(json.dumps(result,indent=2)+'\n')
 # Small portable fallback. Only baseline or linear models are exported here.
 if selected['kind']=='baseline':portable={'kind':'persistence','label':'Same as observed temperature','historical_error_band_c':band}
 elif selected['kind']=='ridge':
  scaler,reg=fitted.steps[0][1],fitted.steps[1][1];portable={'kind':'linear_residual','means':scaler.mean_.tolist(),'scales':scaler.scale_.tolist(),'coefficients':reg.coef_.tolist(),'intercept':float(reg.intercept_),'stations':STATIONS,'historical_error_band_c':band}
 else:
  # Do not silently replace primary/export an unverified tree implementation.
  portable={'kind':'persistence','label':'Same as observed temperature','reason':'Selected challenger requires separate export; conservative persistence fallback retained.'}
 (OUT/'fallback.json').write_text(json.dumps(portable,indent=2)+'\n')
 pred=val[['example_id','city','prediction_time_utc','target_time_utc','target_temp_24h_c','temp_c']].copy();pred['candidate_prediction_c']=vp;pred.to_csv(OUT/'validation_predictions.csv',index=False)
 print('SELECTED',selected,'VALIDATION',result['validation'],flush=True)
if __name__=='__main__':main()
