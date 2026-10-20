"""Recommended pre-training leakage guards. No fitting or scoring."""
import numpy as np
import pandas as pd

def validate_partitions(train, validation):
    for name, frame, start, end in [('train',train,'2022-01-01','2024-01-01'),('validation',validation,'2024-01-02','2024-03-01')]:
        required={'example_id','station_id','prediction_time_utc','target_time_utc','split','temp_c','temp_lag24_c','temp_lag48_c','lag24_missing','lag48_missing','target_temp_24h_c','baseline_temp_24h_c','hour_pk','month_pk'}
        if not required<=set(frame):raise ValueError(f'{name}: missing audit columns')
        if frame.empty or not frame.example_id.is_unique:raise ValueError(f'{name}: empty or duplicate examples')
        issue=pd.to_datetime(frame.prediction_time_utc,utc=True,errors='raise');target=pd.to_datetime(frame.target_time_utc,utc=True,errors='raise')
        if not frame['split'].eq(name).all():raise ValueError(f'{name}: wrong split')
        if not (target.ge(pd.Timestamp(start,tz='UTC'))&target.lt(pd.Timestamp(end,tz='UTC'))).all():raise ValueError(f'{name}: outside fixed date window')
        if not target.sub(issue).eq(pd.Timedelta(hours=24)).all():raise ValueError(f'{name}: wrong prediction horizon')
        if frame.assign(issue=issue).duplicated(['station_id','issue']).any():raise ValueError(f'{name}: duplicate station/time')
        for col in ['temp_c','target_temp_24h_c','baseline_temp_24h_c']:
            if not np.isfinite(pd.to_numeric(frame[col],errors='coerce')).all():raise ValueError(f'{name}: invalid {col}')
        if not frame.baseline_temp_24h_c.eq(frame.temp_c).all():raise ValueError(f'{name}: changed baseline')
        for h in [24,48]:
            value=frame[f'temp_lag{h}_c'];flag=frame[f'lag{h}_missing']
            if not (value.isna()|np.isfinite(value)).all():raise ValueError(f'{name}: infinite lag')
            if not flag.eq(value.isna().astype(int)).all():raise ValueError(f'{name}: incorrect lag marker')
        pk=issue.dt.tz_convert('Asia/Karachi')
        if not pd.to_numeric(frame.hour_pk).eq(pk.dt.hour).all() or not pd.to_numeric(frame.month_pk).eq(pk.dt.month).all():raise ValueError(f'{name}: wrong PKT features')
    if set(train.example_id)&set(validation.example_id):raise ValueError('Overlapping examples')
    if pd.to_datetime(train.target_time_utc,utc=True).max()>=pd.to_datetime(validation.prediction_time_utc,utc=True).min():raise ValueError('Training labels cross validation issue time')
