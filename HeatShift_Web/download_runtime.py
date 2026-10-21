"""Fetch the pinned Pyodide runtime into this static deployment folder."""
from pathlib import Path
from urllib.request import urlopen
import concurrent.futures,json,hashlib
ROOT=Path(__file__).resolve().parent
BASE='https://cdn.jsdelivr.net/pyodide/v0.27.7/full/'
def main():
    lock=json.load(urlopen(BASE+'pyodide-lock.json',timeout=60))
    packages=[lock['packages'][n] for n in ['pandas','numpy','python-dateutil','pytz','six']]
    names=['pyodide.js','pyodide.asm.js','pyodide.asm.wasm','python_stdlib.zip','pyodide-lock.json']+[p['file_name'] for p in packages]
    def fetch(name):
        data=urlopen(BASE+name,timeout=120).read()
        expected=next((p['sha256'] for p in packages if p['file_name']==name),None)
        if expected and hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Package fingerprint mismatch: '+name)
        (ROOT/name).write_bytes(data)
        return name
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for name in pool.map(fetch,names):print(name)
if __name__=='__main__':main()
