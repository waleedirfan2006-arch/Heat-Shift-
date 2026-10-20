"""Calibrate error bands after model selection. Never change fitted parameters.
Uses the uploaded March calibration split, not final-test/replay/reserve files.
Time dependence means conformal exchangeability assumptions are not guaranteed.
"""
from pathlib import Path
import gzip,hashlib,json,shutil
import joblib,numpy as np,pandas as pd
from train_weather_model import ROOT,DATA,OUT,attach_weather,features


def main():
    path=DATA/'calibration.csv'
    frame=pd.read_csv(path,dtype={'station_id':str})
    issue=pd.to_datetime(frame.prediction_time_utc,utc=True);target=pd.to_datetime(frame.target_time_utc,utc=True)
    if frame.empty or not frame.example_id.is_unique or not frame['split'].eq('calibration').all():raise ValueError('Invalid calibration split')
    if not (target.ge(pd.Timestamp('2024-03-02',tz='UTC'))&target.lt(pd.Timestamp('2024-04-01',tz='UTC'))).all():raise ValueError('Calibration dates changed')
    if not (target-issue).eq(pd.Timedelta(hours=24)).all():raise ValueError('Wrong horizon')
    if not np.isfinite(frame[['temp_c','target_temp_24h_c']].to_numpy()).all():raise ValueError('Missing current temperature or target')
    prepared=attach_weather(frame)
    artifact=OUT/'browser_weather_model.joblib';before=hashlib.sha256(artifact.read_bytes()).hexdigest()
    model=joblib.load(artifact)
    prediction=np.rint(frame.temp_c.to_numpy())+model['weight']*model['pipeline'].predict(features(prepared))
    error=np.abs(frame.target_temp_24h_c.to_numpy()-prediction)
    bands={};groups={}
    for city in sorted(frame.city.unique()):
        mask=frame.city.eq(city).to_numpy();values=np.sort(error[mask]);n=len(values)
        rank=min(n,int(np.ceil((n+1)*.9)))
        bands[city]=float(values[rank-1]);groups[city]={'examples':n,'half_width_c':bands[city],'calibration_coverage':float(np.mean(values<=bands[city]))}
    result={'calibration_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'model_sha256':before,'model_changed':False,'nominal_coverage':.9,'method':'Per-city split-conformal absolute error quantile with finite-sample rank correction','groups':groups,'raw_feature_sources':prepared.attrs['raw_feature_sources'],'limitations':['Time-series exchangeability is not guaranteed.','Coverage measured on calibration rows is not independent future coverage.','This does not choose or tune prediction-model parameters.']}
    (OUT/'calibration_metrics.json').write_text(json.dumps(result,indent=2)+'\n')
    report=frame[['example_id','city','prediction_time_utc','target_time_utc','target_temp_24h_c','temp_c']].copy();report['prediction_c']=prediction;report['absolute_error_c']=error;report.to_csv(OUT/'calibration_predictions.csv',index=False)
    exported=json.loads(gzip.decompress((OUT/'browser_weather_model.json.gz').read_bytes()));exported['training_oof_bands_c']=exported.get('training_oof_bands_c',exported['bands_c']);exported['bands_c']=bands;exported['band_source']='separate March 2024 calibration split; no future coverage guarantee'
    with gzip.GzipFile(filename=str(OUT/'browser_weather_model.json.gz'),mode='wb',mtime=0) as f:f.write(json.dumps(exported,separators=(',',':')).encode())
    metrics=json.loads((OUT/'browser_model_metrics.json').read_text());metrics['calibration']=result;metrics['compressed_model_sha256']=hashlib.sha256((OUT/'browser_weather_model.json.gz').read_bytes()).hexdigest();(OUT/'browser_model_metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
    shutil.copyfile(OUT/'browser_weather_model.json.gz',ROOT/'HeatShift_Static_Space/station_weather_model.json.gz');shutil.copyfile(OUT/'browser_model_metrics.json',ROOT/'HeatShift_Static_Space/weather_model_metrics.json')
    assert before==hashlib.sha256(artifact.read_bytes()).hexdigest()
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
