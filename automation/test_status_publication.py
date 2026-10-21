import base64,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import publish_status

class PublicationTests(unittest.TestCase):
    def test_failure_preserves_success_and_never_writes_main(self):
        previous={'last_successful_run':{'finished_at_utc':'2026-10-21T13:00:00Z','run_url':'https://github.com/waleedirfan2006-arch/Heat-Shift-/actions/runs/1'}}
        calls=[]
        def api(method,path,payload=None):
            calls.append((method,path,payload))
            if '/git/ref/' in path:return {'object':{'sha':'existing-runtime-head'}}
            if method=='GET':return {'sha':'previous-file-sha','content':base64.b64encode(json.dumps(previous).encode()).decode()}
            return {'commit':{'sha':'new-runtime-head'}}
        before=Path.cwd()
        with tempfile.TemporaryDirectory() as folder:
            try:
                os.chdir(folder);p=Path('automation/runs/latest.json');p.parent.mkdir(parents=True)
                p.write_text(json.dumps({'generated_at_utc':'2026-10-21T15:00:00Z','status':'failed','cities':{}}))
                with patch.object(publish_status,'api',side_effect=api),patch.dict(os.environ,{'GITHUB_RUN_ID':'2','GITHUB_SHA':'frozen-code'}):publish_status.main()
                out=json.loads(p.read_text())
                self.assertEqual(out['last_successful_run'],previous['last_successful_run'])
                body=next(payload for method,path,payload in calls if method=='PUT')
                self.assertEqual(body['branch'],'heatshift-runtime')
                self.assertFalse(any('/heads/main' in path or '/tags/' in path for _,path,_ in calls))
            finally:os.chdir(before)

if __name__=='__main__':unittest.main()
