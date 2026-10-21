"""Move only the user-requested final tag to an explicitly verified main commit.

No commit dates change and no refs are deleted. The former tag target remains
reachable in repository history and is recorded in the release notes/run log.
"""
import os,re
from publish_status import api,REPO

def main():
    expected=os.environ['FINAL_SHA'];old_expected=os.environ['PREVIOUS_TAG_SHA']
    if not re.fullmatch('[0-9a-f]{40}',expected) or not re.fullmatch('[0-9a-f]{40}',old_expected):
        raise ValueError('Use complete verified commit IDs.')
    main_ref=api('GET','/git/ref/heads/main')
    tag=api('GET','/git/ref/tags/v1.0-final')
    if main_ref['object']['sha']!=expected:raise ValueError('Main changed. Review before tagging.')
    if not tag or tag['object']['sha']!=old_expected:raise ValueError('Final tag changed. Review before moving it.')
    # The only forced update is the exact submission tag explicitly requested.
    api('PATCH','/git/refs/tags/v1.0-final',{'sha':expected,'force':True})
    verified=api('GET','/git/ref/tags/v1.0-final')
    if verified['object']['sha']!=expected:raise RuntimeError('Tag verification failed.')
    release=api('GET','/releases/tags/v1.0-final')
    body=f'''HeatShift final audited submission

Frozen code commit: `{expected}`. The previous tag target was `{old_expected}`; its history remains intact. This update does not backdate any file or commit.

- [Public Hugging Face dashboard](https://huggingface.co/spaces/Waleed-1234/HeatShift-Dashboard)
- [Final checklist](https://github.com/{REPO}/blob/v1.0-final/SUBMISSION_CHECKLIST.md)
- [Submission PDFs, slides and demo](https://github.com/{REPO}/tree/v1.0-final/submission)
- [Public demo, under three minutes](https://raw.githubusercontent.com/{REPO}/v1.0-final/submission/HeatShift_Demo.mp4)
- [AI use log](https://github.com/{REPO}/blob/v1.0-final/AI_Use_Log.md)

The Insight Agent now checks the entire request, refuses unsupported locations/times/advice, and attaches canonical gold-table hashes and original source row IDs. Original agent source and frozen model parameters remain unchanged. The Space shows freshness, quality status and the last successful run. Hourly operational data updates use the separate heatshift-runtime branch and do not change frozen main.

Known unmet historical requirements: no unedited Prefect export or Prefect dashboard screenshot was found for 20 October 16:00 to 21 October 16:00 PKT. The declaration first appears after the Monday noon deadline. Some original collection and JMA fitting records remain unavailable. These are documented gaps, not simulated evidence. All members still need to attend the viva and review their own contributions.

Reproduced reused-validation MAE: 1.102 C versus declared persistence 1.235 C on the same 1,783 rows. January loses; the bootstrap interval includes zero. March calibration bands do not prove future coverage. No retraining or new locked-test/replay/reserve scoring took place in the final audit.
'''
    if not release:raise ValueError('Existing release unavailable; tag verified but release notes need review.')
    api('PATCH','/releases/'+str(release['id']),{'name':'HeatShift v1.0-final - audited submission','body':body,'draft':False,'prerelease':False})
    print('Verified v1.0-final:',expected)
    print('Previous tag commit preserved in history:',old_expected)

if __name__=='__main__':main()
