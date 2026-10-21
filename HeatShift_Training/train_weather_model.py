"""Recommended broader experiment using uploaded station data only.
Select using expanding training folds. Score fixed validation only after selection.
No downloads. No agent imports. No final-test/replay/reserve access.
"""
import os
os.environ.setdefault('OMP_NUM_THREADS','2')
from pathlib import Path
import gzip,hashlib,importlib.metadata,json,time
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor,ExtraTreesRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error,root_mean_squared_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from validate_data import validate_partitions

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'HeatShift_Warehouse/02_final'
OUT=Path(__file__).resolve().parent/'weather_results'
STATIONS=['41780099999','41640099999','41675099999']
NAMES=['current_c','dew_c','dew_spread_c','wind_kt','wind_sin','wind_cos','dew_missing','wind_missing','hour_sin','hour_cos','year_sin','year_cos','karachi','lahore','multan']
WINDOWS=[('2022-07-01','2023-01-01'),('2023-01-01','2023-07-01'),('2023-07-01','2024-01-01')]
WEIGHTS=[.25,.5,.75,1.0]

def attach_weather(frame):
    clean=pd.read_csv(ROOT/'HeatShift_Warehouse/01_clean/noaa_observations.csv',usecols=['row_id','source_file','source_record_number'])
    wanted=frame[['current_row_id']].merge(clean[['row_id','source_file','source_record_number']],left_on='current_row_id',right_on='row_id',how='left',validate='one_to_one')
    if wanted.source_file.isna().any():raise ValueError('Missing current raw source link')
    values=np.full((len(frame),3),np.nan)
    good={'0','1','4','5'}
    for name,group in wanted.groupby('source_file'):
        if Path(name).parts[0]!='00_raw' or len(Path(name).parts)!=2 or not Path(name).name.startswith('noaa_'):raise ValueError('Unexpected source path')
        raw=pd.read_csv(ROOT/'HeatShift_Warehouse'/name,usecols=['DEW','WND'],dtype=str,keep_default_na=False)
        for index,record in group.iterrows():
            item=raw.iloc[int(record.source_record_number)-1]
            dew=item.DEW.split(',');wind=item.WND.split(',')
            if len(dew)>=2 and dew[0]!='+9999' and dew[1] in good:
                d=float(dew[0])/10
                if -98.2<=d<=36.8:values[index,0]=np.rint(d)
            if len(wind)>=5:
                if wind[0]!='999' and wind[1] in good:
                    direction=float(wind[0])
                    if 1<=direction<=360:values[index,1]=direction
                if wind[3]!='9999' and wind[4] in good:
                    speed=float(wind[3])/10
                    if 0<=speed<=90:values[index,2]=np.rint(speed/0.5144444444444445)
    result=frame.copy();result[['dew_c','wind_dir','wind_kt']]=values
    result.attrs['raw_feature_sources']={name:hashlib.sha256((ROOT/'HeatShift_Warehouse'/name).read_bytes()).hexdigest() for name in wanted.source_file.unique()}
    return result

def features(frame,hide_history=False):
    local=pd.to_datetime(frame.prediction_time_utc,utc=True).dt.tz_convert('Asia/Karachi')
    current=np.rint(frame.temp_c.to_numpy(float));dew=frame.dew_c.to_numpy(float);wind=frame.wind_kt.to_numpy(float);direction=np.deg2rad(frame.wind_dir.to_numpy(float))
    direction[wind==0]=np.nan
    if hide_history:dew=dew*float('nan');wind=wind*float('nan');direction=direction*float('nan')
    return np.column_stack([current,dew,current-dew,wind,np.sin(direction),np.cos(direction),np.isnan(dew),np.isnan(wind),np.sin(2*np.pi*local.dt.hour/24),np.cos(2*np.pi*local.dt.hour/24),np.sin(2*np.pi*(local.dt.dayofyear-1)/365.2425),np.cos(2*np.pi*(local.dt.dayofyear-1)/365.2425),*[frame.station_id.eq(s).astype(float) for s in STATIONS]])

def build(config):
    if config['kind']=='ridge':return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),Ridge(alpha=config['alpha']))
    if config['kind']=='extra_trees':
        model=ExtraTreesRegressor(n_estimators=200,min_samples_leaf=config['leaf'],max_features=.8,n_jobs=2,random_state=20261021)
    else:
        model=HistGradientBoostingRegressor(loss=config['loss'],max_iter=config['iterations'],max_leaf_nodes=config['leaves'],learning_rate=.05,l2_regularization=config['l2'],min_samples_leaf=40,early_stopping=False,random_state=20261021)
    return make_pipeline(SimpleImputer(strategy='median'),model)

def score(frame,prediction):
    y=frame.target_temp_24h_c.to_numpy();b=frame.temp_c.to_numpy()
    return {'examples':len(frame),'mae_c':float(mean_absolute_error(y,prediction)),'rmse_c':float(root_mean_squared_error(y,prediction)),'baseline_mae_c':float(mean_absolute_error(y,b)),'baseline_rmse_c':float(root_mean_squared_error(y,b))}

def export_hgb(pipeline,weight,model_path):
    model=pipeline.steps[-1][1]
    trees=[]
    for iteration in model._predictors:
        for predictor in iteration:
            trees.append([{'value':float(n['value']),'feature':int(n['feature_idx']),'bin':int(n['bin_threshold']),'left':int(n['left']),'right':int(n['right']),'leaf':bool(n['is_leaf'])} for n in predictor.nodes])
    return {'format':'heatshift-hgb-js-v1','numeric_features':NAMES,'medians':pipeline.steps[0][1].statistics_.tolist(),'means':[0.]*len(NAMES),'scales':[1.]*len(NAMES),'categorical_features':[],'categories':[],'bin_thresholds':[x.tolist() for x in model._bin_mapper.bin_thresholds_],'baseline':float(model._baseline_prediction.ravel()[0]),'trees':trees,'residual_weight':weight,'source_sha256':hashlib.sha256(model_path.read_bytes()).hexdigest()}

def main():
    started=time.perf_counter();OUT.mkdir(exist_ok=True)
    train=pd.read_csv(DATA/'train.csv',dtype={'station_id':str});validation=pd.read_csv(DATA/'validation.csv',dtype={'station_id':str})
    validate_partitions(train,validation)
    train=attach_weather(train);validation=attach_weather(validation)
    X=features(train);baseline=np.rint(train.temp_c.to_numpy());residual=train.target_temp_24h_c.to_numpy()-baseline
    targets=pd.to_datetime(train.target_time_utc,utc=True);issues=pd.to_datetime(train.prediction_time_utc,utc=True)
    folds=[]
    for start,end in WINDOWS:
        a=pd.Timestamp(start,tz='UTC');b=pd.Timestamp(end,tz='UTC')
        folds.append((np.flatnonzero(targets<a),np.flatnonzero((issues>=a)&(targets<b))))
    configs=[{'id':f'ridge_{a}','kind':'ridge','alpha':a} for a in [10,100,1000,10000]]
    configs += [{'id':f'hgb_{loss}_{iterations}_{leaves}_{l2}','kind':'hgb','loss':loss,'iterations':iterations,'leaves':leaves,'l2':l2} for loss in ['absolute_error','squared_error'] for iterations,leaves,l2 in [(120,7,10),(300,7,10),(200,15,10),(200,7,100)]]
    configs += [{'id':f'extra_trees_{leaf}','kind':'extra_trees','leaf':leaf} for leaf in [20,60]]
    idx=np.concatenate([v for _,v in folds]);rows=[];cached={}
    base_score=score(train.iloc[idx],baseline[idx])
    for config in configs:
        oof=[]
        for fit,check in folds:
            estimator=build(config);estimator.fit(X[fit],residual[fit]);oof.extend(estimator.predict(X[check]))
        r=np.array(oof);cached[config['id']]=r
        for weight in WEIGHTS:
            prediction=baseline[idx]+weight*r
            details=[];offset=0
            for _,check in folds:
                details.append(score(train.iloc[check],prediction[offset:offset+len(check)]));offset+=len(check)
            rows.append({'config':config,'weight':weight,**score(train.iloc[idx],prediction),'folds':details})
        print(config['id'],min(x['mae_c'] for x in rows if x['config']['id']==config['id']),flush=True)
    # Fixed before inspecting validation: choose CV score; never choose by held-out score.
    winner=min(rows,key=lambda x:x['mae_c'])
    selected=winner['config'];weight=winner['weight']
    pipeline=build(selected);pipeline.fit(X,residual)
    artifact=OUT/'weather_challenger.joblib';joblib.dump({'pipeline':pipeline,'weight':weight,'numeric_features':NAMES,'feature_policy':'Whole-degree station current and dew-point temperature, integer wind knots, wind direction, calendar PKT','selected':selected},artifact,compress=3)
    val_prediction=np.rint(validation.temp_c.to_numpy())+weight*pipeline.predict(features(validation))
    no_history=np.rint(validation.temp_c.to_numpy())+weight*pipeline.predict(features(validation,hide_history=True))
    oof_prediction=baseline[idx]+weight*cached[selected['id']]
    bands={}
    for city in sorted(train.city.unique()):
        mask=train.iloc[idx].city.eq(city).to_numpy();bands[city]=float(np.quantile(abs(train.iloc[idx].target_temp_24h_c.to_numpy()[mask]-oof_prediction[mask]),.9))
    result={'created_at_utc':pd.Timestamp.now(tz='UTC').isoformat(),'training_examples':len(train),'validation_examples':len(validation),'training_sha256':hashlib.sha256((DATA/'train.csv').read_bytes()).hexdigest(),'validation_sha256':hashlib.sha256((DATA/'validation.csv').read_bytes()).hexdigest(),'selection':'lowest pooled training-only chronological MAE; all 56 config/weight comparisons fixed before validation','windows':WINDOWS,'weights':WEIGHTS,'candidates':rows,'selected':selected,'selected_weight':weight,'training_cv':{k:v for k,v in winner.items() if k not in ['config']},'training_cv_baseline':base_score,'validation':score(validation,val_prediction),'validation_without_weather_stress_test':score(validation,no_history),'validation_by_city':{city:score(validation.loc[mask],val_prediction[mask]) for city in sorted(validation.city.unique()) for mask in [validation.city.eq(city).to_numpy()]},'training_oof_q90_bands_c':bands,'raw_feature_sources':{**train.attrs['raw_feature_sources'],**validation.attrs['raw_feature_sources']},'weather_coverage':{c:{'train_present':int(train[c].notna().sum()),'validation_present':int(validation[c].notna().sum())} for c in ['dew_c','wind_dir','wind_kt']},'runtime_seconds':time.perf_counter()-started,'environment':{n:importlib.metadata.version(n) for n in ['numpy','pandas','scikit-learn','joblib','scipy','threadpoolctl']},'limitations':['Validation has previously been inspected; it is not a fresh final test.','No test_locked, replay or reserve data used.','Station training/validation does not independently establish live METAR performance.','Raw observation arrival/revision times are unknown.','Current JMA primary cannot be rescored from repository because its archived training feature data is absent.']}
    (OUT/'metrics.json').write_text(json.dumps(result,indent=2)+'\n')
    pred=validation[['example_id','city','prediction_time_utc','target_time_utc','target_temp_24h_c','temp_c','temp_lag24_c','temp_lag48_c']].copy();pred['prediction_c']=val_prediction;pred['prediction_without_weather_c']=no_history;pred.to_csv(OUT/'validation_predictions.csv',index=False)
    if selected['kind']=='hgb':
        exported=export_hgb(pipeline,weight,artifact)
        with gzip.GzipFile(filename=str(OUT/'weather_model.json.gz'),mode='wb',mtime=0) as handle:handle.write(json.dumps(exported,separators=(',',':')).encode())
    else:(OUT/'weather_model.json.gz').unlink(missing_ok=True)
    print(json.dumps({'winner':selected,'weight':weight,'validation':result['validation'],'without_history':result['validation_without_weather_stress_test'],'by_city':result['validation_by_city']},indent=2),flush=True)
if __name__=='__main__':main()
