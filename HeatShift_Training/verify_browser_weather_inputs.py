"""Software parity test, not a new accuracy evaluation or training run."""
import csv,json,subprocess,tempfile,gzip
from datetime import datetime,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]
rows=[]
vectors=json.loads(gzip.decompress((ROOT/'HeatShift_Training/weather_results/browser_parity_vectors.json.gz').read_bytes()))
with (ROOT/'HeatShift_Training/weather_results/browser_validation_predictions.csv').open() as handle:
    for index,item in enumerate(csv.DictReader(handle)):
        if not item['dew_c'] or not item['wind_kt']:continue
        issue=datetime.fromisoformat(item['prediction_time_utc'])
        speed=int(float(item['wind_kt']))
        rows.append({'city':item['city'],'temperature':int(round(float(item['temp_c']))),'stamp':issue.astimezone(ZoneInfo('Asia/Karachi')).strftime('%Y-%m-%dT%H:%M'),'now':int((issue+timedelta(hours=1)).timestamp()*1000),'dewpoint':int(float(item['dew_c'])),'windSpeed':speed,'windDirection':int(float(item['wind_dir'])) if item['wind_dir'] and speed else None,'expected':float(item['prediction_c']),'reference_features':vectors[index]['row']})
if not rows:raise RuntimeError('No usable validation reports')
with tempfile.NamedTemporaryFile('w',suffix='.json',delete=False) as handle:
    json.dump(rows,handle);path=Path(handle.name)
try:subprocess.run(['node',str(ROOT/'HeatShift_Static_Space/check_weather_inputs.js'),str(path)],check=True)
finally:path.unlink(missing_ok=True)
