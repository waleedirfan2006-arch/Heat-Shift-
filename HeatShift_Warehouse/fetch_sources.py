"""Re-fetch known publisher URLs and check against frozen hashes.
Original snapshots and collection times are never overwritten. Unknown URLs are skipped honestly.
The main rebuild uses bundled snapshots and does not require network access.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,time,urllib.request

ROOT=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'new_fetch_checks')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    receipts=[]
    for item in json.loads((ROOT/'manifest.json').read_text()):
        receipt={'raw_file':item['raw_file'],'requested_url':item['source_url'],
                 'checked_at_utc':datetime.now(timezone.utc).isoformat()}
        if item['source']!='noaa' or not item['source_url']:
            receipt.update(status='SKIPPED',reason='Original Open-Meteo URL/settings unknown; no automated recollection authorised by this configuration.')
            receipts.append(receipt);continue
        last_error=None
        for attempt in range(3):
            try:
                req=urllib.request.Request(item['source_url'],headers={'User-Agent':'HeatShift-student-data-client/1.0'})
                with urllib.request.urlopen(req,timeout=60) as response:
                    payload=response.read();status=response.status
                actual=hashlib.sha256(payload).hexdigest()
                receipt.update(status='MATCH' if actual==item['sha256'] else 'CHANGED',http_status=status,
                               sha256=actual,expected_sha256=item['sha256'],bytes=len(payload),attempts=attempt+1,
                               fetched_at_utc=datetime.now(timezone.utc).isoformat())
                # Separate fresh download; do not alter frozen originals or promote changed data.
                candidate=args.output/('noaa_'+actual[:16]+'_'+Path(item['raw_file']).name)
                if not candidate.exists():candidate.write_bytes(payload)
                last_error=None;break
            except Exception as exc:
                last_error=str(exc)
                if attempt<2:time.sleep(2**attempt)
        if last_error:receipt.update(status='FAILED',reason=last_error)
        receipts.append(receipt)
    file=args.output/('receipts_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    file.write_text(json.dumps(receipts,indent=2)+'\n')
    print('Fetch checks saved:',file)
    print('Open-Meteo skipped; original snapshots were not changed.')
    if any(r['status'] in ['FAILED','CHANGED'] for r in receipts):raise SystemExit(1)

if __name__=='__main__':main()
