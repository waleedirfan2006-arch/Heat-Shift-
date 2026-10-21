"""Select best already-compared HGB by training CV for the existing browser engine.
Other estimator families remain research comparisons. Validation is development
validation, not a fresh final test. Never reads final-test/replay/reserve files.
"""
import gzip,json,hashlib,time
from pathlib import Path
import joblib,numpy as np,pandas as pd
from train_weather_model import ROOT,DATA,OUT,features,attach_weather,build,score,export_hgb,NAMES
from validate_data import validate_partitions


def main():
    comparisons=json.loads((OUT/'metrics.json').read_text())
    eligible=[r for r in comparisons['candidates'] if r['config']['kind']=='hgb']
    choice=min(eligible,key=lambda r:r['mae_c'])
    train=pd.read_csv(DATA/'train.csv',dtype={'station_id':str});validation=pd.read_csv(DATA/'validation.csv',dtype={'station_id':str})
    validate_partitions(train,validation)
    train=attach_weather(train);validation=attach_weather(validation)
    X=features(train);V=features(validation)
    weight=choice['weight'];config=choice['config']
    pipeline=build(config);start=time.perf_counter();pipeline.fit(X,train.target_temp_24h_c.to_numpy()-np.rint(train.temp_c.to_numpy()))
    artifact=OUT/'browser_weather_model.joblib'
    joblib.dump({'pipeline':pipeline,'weight':weight,'selected':config,'features':NAMES},artifact,compress=3)
    prediction=np.rint(validation.temp_c.to_numpy())+weight*pipeline.predict(V)
    exported=export_hgb(pipeline,weight,artifact)
    exported['selected_candidate']=config['id'];exported['purpose']='station weather context forecast; no JMA input'
    # Training-only OOF residuals for this fixed candidate provide historical ranges.
    targets=pd.to_datetime(train.target_time_utc,utc=True);issues=pd.to_datetime(train.prediction_time_utc,utc=True)
    oof=[];indices=[]
    for a,b in comparisons['windows']:
        begin=pd.Timestamp(a,tz='UTC');end=pd.Timestamp(b,tz='UTC')
        fit=np.flatnonzero(targets<begin);check=np.flatnonzero((issues>=begin)&(targets<end))
        fold=build(config);fold.fit(X[fit],train.target_temp_24h_c.to_numpy()[fit]-np.rint(train.temp_c.to_numpy()[fit]))
        oof.extend(np.rint(train.temp_c.to_numpy()[check])+weight*fold.predict(X[check]));indices.extend(check)
    subset=train.iloc[indices];oof=np.array(oof)
    exported['bands_c']={city:float(np.quantile(abs(subset.loc[mask,'target_temp_24h_c'].to_numpy()-oof[mask]),.9)) for city in sorted(subset.city.unique()) for mask in [subset.city.eq(city).to_numpy()]}
    with gzip.GzipFile(filename=str(OUT/'browser_weather_model.json.gz'),mode='wb',mtime=0) as f:f.write(json.dumps(exported,separators=(',',':')).encode())
    residual=pipeline.predict(V)
    vectors=[{'row':{k:None if not np.isfinite(value) else float(value) for k,value in zip(NAMES,row)},'expected_residual':float(expected),'expected_prediction':float(row[0]+weight*expected)} for row,expected in zip(V,residual)]
    with gzip.GzipFile(filename=str(OUT/'browser_parity_vectors.json.gz'),mode='wb',mtime=0) as f:f.write(json.dumps(vectors,separators=(',',':')).encode())
    delta=abs(validation.target_temp_24h_c.to_numpy()-validation.temp_c.to_numpy())-abs(validation.target_temp_24h_c.to_numpy()-prediction)
    # Day-block bootstrap of validation error differences; report uncertainty, no tuning.
    day=pd.to_datetime(validation.target_time_utc,utc=True).dt.floor('D');first=day.min();blocks=((day-first).dt.days//7).to_numpy();unique=np.unique(blocks);rng=np.random.default_rng(20261021)
    sums=np.array([delta[blocks==b].sum() for b in unique]);counts=np.array([(blocks==b).sum() for b in unique]);sample=rng.integers(0,len(unique),size=(2000,len(unique)));boot=sums[sample].sum(axis=1)/counts[sample].sum(axis=1)
    result={'selected':config,'residual_weight':weight,'selection':'best training-CV HGB among browser-engine-compatible candidates','overall_cv_winner':comparisons['selected'],'matches_overall_cv_winner':choice['config']==comparisons['selected'] and choice['weight']==comparisons['selected_weight'],'training_examples':len(train),'validation':score(validation,prediction),'validation_by_city':{city:score(validation.loc[mask],prediction[mask]) for city in sorted(validation.city.unique()) for mask in [validation.city.eq(city).to_numpy()]},'metar_precision_baseline_mae_c':float(np.mean(abs(validation.target_temp_24h_c.to_numpy()-np.rint(validation.temp_c.to_numpy())))),'mean_validation_mae_improvement_c':float(delta.mean()),'seven_day_block_bootstrap_95pct_improvement_interval_c':np.quantile(boot,[.025,.975]).tolist(),'blocks':len(unique),'historical_bands_c':exported['bands_c'],'training_sha256':hashlib.sha256((DATA/'train.csv').read_bytes()).hexdigest(),'validation_sha256':hashlib.sha256((DATA/'validation.csv').read_bytes()).hexdigest(),'artifact_sha256':exported['source_sha256'],'compressed_model_sha256':hashlib.sha256((OUT/'browser_weather_model.json.gz').read_bytes()).hexdigest(),'runtime_seconds':time.perf_counter()-start,'limitations':['Validation was reused during development; no independent final-performance claim.','Not compared directly against JMA primary on matching archived features.','Live METAR measurements can differ from historical NOAA reports.','Raw event arrival/revision times are unverified.','Historical OOF bands are not calibrated coverage guarantees.'],'raw_feature_sources':{**train.attrs['raw_feature_sources'],**validation.attrs['raw_feature_sources']},'source_documentation':'https://www.ncei.noaa.gov/pub/data/noaa/isd-format-document.pdf'}
    (OUT/'browser_model_metrics.json').write_text(json.dumps(result,indent=2)+'\n')
    output=validation[['example_id','city','prediction_time_utc','target_time_utc','target_temp_24h_c','temp_c','dew_c','wind_dir','wind_kt']].copy();output['prediction_c']=prediction;output.to_csv(OUT/'browser_validation_predictions.csv',index=False)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
