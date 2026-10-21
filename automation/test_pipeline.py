from pathlib import Path
import sys,tempfile,unittest,json
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import hourly_pipeline as pipeline

class FailureTests(unittest.TestCase):
    def test_failed_acquisition_is_not_replaced_with_old_predictions(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);(out/'cleaned').mkdir();(out/'cleaned/karachi_cleaned.csv').write_text('time,temperature_c\n2023-01-01,20\n')
            with patch.object(pipeline,'fetch',side_effect=RuntimeError('upstream unavailable')):
                self.assertEqual(pipeline.run(out),1)
            result=json.loads((out/'latest.json').read_text())
            self.assertEqual(result['status'],'failed')
            self.assertTrue(all(v['status']=='unavailable' for v in result['cities'].values()))
            self.assertTrue(all('prediction_c' not in v for v in result['cities'].values()))
            self.assertEqual(list((out/'cleaned').glob('*_cleaned.csv')),[])

if __name__=='__main__':unittest.main()
