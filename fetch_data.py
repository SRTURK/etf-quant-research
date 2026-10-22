"""Optional snapshot recovery. Offline research.py never downloads data."""
from pathlib import Path
from urllib.request import Request, urlopen
import hashlib

URL='https://raw.githubusercontent.com/manisahni/marketdata/main/daily_adjclose.csv'
SHA='361efb287116fc8200582c15fcd315bcce2e218fa1e50b416bacc5acebff37b9'
if __name__=='__main__':
    content=urlopen(Request(URL,headers={'User-Agent':'ETF-research/1.0'}),timeout=60).read()
    if hashlib.sha256(content).hexdigest()!=SHA:
        raise RuntimeError('Upstream changed: refusing to overwrite the research snapshot')
    path=Path(__file__).resolve().parent/'data/raw/daily_adjclose.csv'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(content)
    print('Verified original snapshot restored.')
