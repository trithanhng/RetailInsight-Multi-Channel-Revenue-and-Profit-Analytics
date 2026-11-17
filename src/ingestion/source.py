"""Download pinned Microsoft sources and read their SQL schema."""
from pathlib import Path
import re
import urllib.request

from src.utils.config import RAW

COMMIT = 'b47eadc85277f72843647223cde53aa1b85ffcb8'
REPO = 'https://github.com/microsoft/sql-server-samples'
BASE = f'https://raw.githubusercontent.com/microsoft/sql-server-samples/{COMMIT}/samples/databases/adventure-works/data-warehouse-install-script/'
TABLES = ['FactInternetSales', 'FactResellerSales', 'DimProduct', 'DimProductSubcategory',
    'DimProductCategory', 'DimSalesTerritory', 'DimCurrency', 'DimReseller']


def download(raw_dir=RAW):
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    for name in [t + '.csv' for t in TABLES] + ['instawdbdw.sql', 'license.txt']:
        target = raw_dir / name
        if target.exists():
            continue
        url = f'https://raw.githubusercontent.com/microsoft/sql-server-samples/{COMMIT}/license.txt' if name == 'license.txt' else BASE + name
        temp = target.with_suffix(target.suffix + '.part')
        with urllib.request.urlopen(url, timeout=120) as response, temp.open('wb') as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        temp.replace(target)
        print(f'Downloaded {name}: {target.stat().st_size:,} bytes', flush=True)


def source_columns(sql, table):
    match = re.search(r'CREATE TABLE \[dbo\]\.\[' + re.escape(table) + r'\]\((.*?)\) ON', sql, re.S)
    if not match:
        raise ValueError(f'Không tìm thấy schema {table}')
    return re.findall(r'^\s*\[([^\]]+)\]', match.group(1), re.M)
