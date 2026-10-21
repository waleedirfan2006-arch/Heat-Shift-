"""Publish operational data to a separate branch; never move frozen code refs."""
import base64,json,os
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError

REPO='waleedirfan2006-arch/Heat-Shift-'
BRANCH='heatshift-runtime'
BASE='https://api.github.com/repos/'+REPO

def api(method,path,payload=None):
    token=os.environ['GITHUB_TOKEN']
    data=None if payload is None else json.dumps(payload).encode()
    request=Request(BASE+path,data=data,method=method,headers={
        'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json',
        'Content-Type':'application/json','X-GitHub-Api-Version':'2022-11-28'})
    try:
        with urlopen(request,timeout=30) as response:return json.load(response)
    except HTTPError as error:
        if error.code==404:return None
        raise RuntimeError('GitHub status publication failed, HTTP '+str(error.code)) from None

def main():
    latest_path=Path('automation/runs/latest.json')
    latest=json.loads(latest_path.read_text(encoding='utf-8'))
    if api('GET','/git/ref/heads/'+BRANCH) is None:
        api('POST','/git/refs',{'ref':'refs/heads/'+BRANCH,'sha':os.environ['GITHUB_SHA']})
    old=api('GET','/contents/runtime/latest.json?ref='+BRANCH)
    previous=json.loads(base64.b64decode(old['content'])) if old and old.get('content') else {}
    run_url='https://github.com/'+REPO+'/actions/runs/'+os.environ['GITHUB_RUN_ID']
    latest['run_url']=run_url
    latest['last_successful_run']=({'finished_at_utc':latest['generated_at_utc'],'run_url':run_url,'run_id':os.environ['GITHUB_RUN_ID']} if latest['status']=='ok' else previous.get('last_successful_run'))
    latest['publication_branch']=BRANCH
    latest_path.write_text(json.dumps(latest,indent=2)+'\n',encoding='utf-8')
    body={'message':'Refresh operational HeatShift status','branch':BRANCH,
          'content':base64.b64encode(latest_path.read_bytes()).decode()}
    if old:body['sha']=old['sha']
    api('PUT','/contents/runtime/latest.json',body)
    print('Published current status on '+BRANCH+'. Frozen main/tag unchanged.')

if __name__=='__main__':main()
