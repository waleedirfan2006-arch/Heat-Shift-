"""Damaged copies for guard stress tests only. Never model training/evaluation."""
from pathlib import Path
from datetime import datetime,timezone
import json
import pandas as pd
from train_model import load_partition
from validate_data import validate_partitions
r=Path(__file__).resolve().parent
tr=load_partition(r.parent/'HeatShift_Warehouse/02_final/train.csv');va=load_partition(r.parent/'HeatShift_Warehouse/02_final/validation.csv')
validate_partitions(tr,va);results=[{'case':'actual partitions accepted','pass':True}]
def reject(name,fn):
 t,v=tr.copy(),va.copy();fn(t,v)
 try:validate_partitions(t,v)
 except ValueError as e:results.append({'case':name,'pass':True,'reason':str(e)});return
 raise AssertionError('Not rejected: '+name)
reject('changed baseline',lambda t,v:v.__setitem__('baseline_temp_24h_c',v.temp_c+1))
reject('wrong split',lambda t,v:v.__setitem__('split','test_locked'))
reject('wrong horizon',lambda t,v:v.__setitem__('target_time_utc',v.target_time_utc+pd.Timedelta(hours=1)))
reject('future training date',lambda t,v:t.__setitem__('target_time_utc',pd.Timestamp('2025-01-01',tz='UTC')))
reject('missing target',lambda t,v:v.__setitem__('target_temp_24h_c',float('nan')))
reject('incorrect lag markers',lambda t,v:v.__setitem__('lag24_missing',1-v.lag24_missing))
reject('duplicate examples',lambda t,v:v.__setitem__('example_id','duplicate'))
reject('incorrect PKT hour',lambda t,v:v.__setitem__('hour_pk','99'))
reject('infinite current value',lambda t,v:v.__setitem__('temp_c',float('inf')))
out=r.parent/'HeatShift_Warehouse/audit/guard_tests.json'
out.write_text(json.dumps({'at_utc':datetime.now(timezone.utc).isoformat(),'type':'SYNTHETIC COPY-ONLY STRESS TESTS; NOT MODEL EVALUATION','model_fitted':False,'results':results},indent=2)+'\n')
print(len(results),'guard stress tests passed; data files unchanged.')
