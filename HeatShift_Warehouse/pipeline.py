"""Recommended warehouse runner. Restores raw snapshots and builds all layers.
This is NOT a Data Quality Agent or an hourly scheduler.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import csv
import hashlib
import json
import os
import shutil
import tempfile
import zipfile
import build_warehouse

PROJECT = Path(__file__).resolve().parent

def digest(data):
    return hashlib.sha256(data).hexdigest()

def run(output):
    manifest = json.loads((PROJECT / 'manifest.json').read_text(encoding='utf-8'))
    with (PROJECT/'manifest.csv').open(encoding='utf-8',newline='') as f:
        readable=list(csv.DictReader(f))
    if {r['raw_file']:r['sha256'] for r in readable}!={r['raw_file']:r['sha256'] for r in manifest}:
        raise ValueError('manifest.csv and manifest.json disagree. Stop and review.')
    output.mkdir(parents=True,exist_ok=True)
    lock=output/'warehouse_build.lock'
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    os.close(fd)
    restored=[]
    try:
        # Read the package, not the current working directory. Offline clean-start works.
        with zipfile.ZipFile(PROJECT/'source_snapshots.zip') as archive:
            pending=[]
            for item in manifest:
                relative=Path(item['raw_file'])
                if relative.is_absolute() or '..' in relative.parts or relative.parts[0]!='00_raw':
                    raise ValueError('Unsafe raw-file path in manifest.')
                path=output/relative
                blob=path.read_bytes() if path.exists() else archive.read(relative.as_posix())
                if digest(blob)!=item['sha256']:
                    raise ValueError('Raw SHA-256 mismatch; no build or repair performed: '+relative.as_posix())
                if not path.exists():pending.append((path,blob))
            # Do not start writing until every input has passed its hash check.
            for path,blob in pending:
                path.parent.mkdir(parents=True,exist_ok=True)
                with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as f:
                    f.write(blob);temporary=Path(f.name)
                temporary.replace(path)
                restored.append(str(path.relative_to(output)))
        if output != PROJECT:
            for name in ['manifest.json','manifest.csv']:
                shutil.copyfile(PROJECT/name,output/name)
        build_warehouse.ROOT=output
        build_warehouse.build()
        receipt={'rebuilt_at_utc':datetime.now(timezone.utc).isoformat(),
                 'mode':'verified_local_snapshot_reload',
                 'raw_files_verified':len(manifest),'raw_files_restored':restored,
                 'data_quality_agent':'NOT IMPLEMENTED: intentionally excluded by user',
                 'note':'Reload time is not original publisher fetch time. No model trained.'}
        (output/'quality'/'rebuild_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print('DONE: raw, cleaned, final and SQLite warehouse rebuilt. Data Quality Agent remains pending.')
    finally:
        lock.unlink(missing_ok=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=PROJECT,help='Destination; can be an empty directory.')
    run(p.parse_args().output.resolve())
