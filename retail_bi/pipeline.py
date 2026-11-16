"""Nạp nguồn Microsoft được ghim phiên bản, kiểm tra, lưu Parquet và tạo mart."""
import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.request

import pandas as pd

COMMIT = 'b47eadc85277f72843647223cde53aa1b85ffcb8'
REPO = 'https://github.com/microsoft/sql-server-samples'
BASE = f'https://raw.githubusercontent.com/microsoft/sql-server-samples/{COMMIT}/samples/databases/adventure-works/data-warehouse-install-script/'
TABLES = ['FactInternetSales', 'FactResellerSales', 'DimProduct', 'DimProductSubcategory',
    'DimProductCategory', 'DimSalesTerritory', 'DimCurrency', 'DimReseller']
SCALE = 10000
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data' / 'adventureworks'
RAW = ROOT / 'data' / 'raw'
MONEY = {'SalesAmount': 'revenue_units', 'TotalProductCost': 'cost_units',
    'DiscountAmount': 'discount_units', 'ExtendedAmount': 'gross_units'}


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


def money_units(value):
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number < 0:
            return pd.NA
        return int((number * SCALE).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError):
        return pd.NA


def clean_source(name, raw):
    frame = raw.copy()
    for col in frame:
        frame[col] = frame[col].astype('string').str.strip().replace('', pd.NA)
    duplicate_count = int(frame.duplicated().sum())
    frame = frame.drop_duplicates().copy()
    key = ['SalesOrderNumber', 'SalesOrderLineNumber'] if name.startswith('Fact') else [name[3:] + 'Key']
    missing_keys = set(key) - set(frame.columns)
    if missing_keys:
        raise ValueError(f'{name}: thiếu khóa {sorted(missing_keys)}')
    reasons = pd.Series('', index=frame.index, dtype='string')
    for col in key:
        reasons.loc[frame[col].isna()] += f'missing:{col};'
    if name.startswith('Fact'):
        required = ['OrderDate', 'OrderQuantity', 'ProductKey', 'SalesTerritoryKey', *MONEY]
        missing = set(required) - set(frame.columns)
        if missing:
            raise ValueError(f'{name}: thiếu cột {sorted(missing)}')
        for col in ['ProductKey', 'SalesTerritoryKey']:
            reasons.loc[frame[col].isna()] += f'missing:{col};'
        for source, target in MONEY.items():
            frame[target] = frame[source].map(money_units).astype('Int64')
            reasons.loc[frame[target].isna()] += f'invalid_money:{source};'
        frame['order_date'] = pd.to_datetime(frame.OrderDate, errors='coerce', format='mixed')
        reasons.loc[frame.order_date.isna()] += 'invalid_order_date;'
        quantity = pd.to_numeric(frame.OrderQuantity, errors='coerce')
        reasons.loc[quantity.isna() | quantity.le(0) | quantity.mod(1).ne(0)] += 'invalid_quantity;'
        frame['quantity'] = quantity.where(quantity.mod(1).eq(0)).astype('Int64')
        frame['profit_units'] = frame.revenue_units - frame.cost_units
        delta = (frame.gross_units - frame.discount_units - frame.revenue_units).abs()
        reasons.loc[delta.gt(1).fillna(False)] += 'revenue_reconciliation;'
    rejected = frame.loc[reasons.ne('')].copy()
    rejected['rejection_reason'] = reasons.loc[reasons.ne('')]
    clean = frame.loc[reasons.eq('')].copy()
    if clean.duplicated(key).any():
        raise ValueError(f'{name}: khóa {key} có dữ liệu xung đột')
    report = {'table': name, 'rows_before': len(raw), 'duplicates_removed': duplicate_count,
        'rows_rejected': len(rejected), 'rows_after': len(clean),
        'columns': [{'column': col, 'dtype_before': str(raw[col].dtype),
            'missing_before': int(raw[col].isna().sum()), 'dtype_after': str(clean[col].dtype),
            'missing_after': int(clean[col].isna().sum())} for col in raw],
        'missing_pct_before': float(raw.isna().sum().sum() / raw.size * 100) if raw.size else 0}
    return clean.reset_index(drop=True), rejected.reset_index(drop=True), report


def checked_join(left, right, key):
    result = left.merge(right, on=key, how='left', validate='many_to_one', indicator=True)
    if result['_merge'].ne('both').any():
        raise ValueError(f'Khóa ngoại {key} không tồn tại trong bảng chiều')
    return result.drop(columns='_merge')


def build_mart(tables):
    product = tables['DimProduct'][['ProductKey', 'ProductSubcategoryKey', 'EnglishProductName']]
    sub = tables['DimProductSubcategory'][['ProductSubcategoryKey', 'ProductCategoryKey', 'EnglishProductSubcategoryName']]
    categories = tables['DimProductCategory'][['ProductCategoryKey', 'EnglishProductCategoryName']]
    product = product.merge(sub, on='ProductSubcategoryKey', how='left', validate='many_to_one')
    product = product.merge(categories, on='ProductCategoryKey', how='left', validate='many_to_one')
    territory = tables['DimSalesTerritory'][['SalesTerritoryKey', 'SalesTerritoryRegion', 'SalesTerritoryCountry']]
    pieces = []
    for source, channel, party_key in [('FactInternetSales', 'Internet', 'CustomerKey'),
            ('FactResellerSales', 'Reseller', 'ResellerKey')]:
        frame = tables[source].copy()
        frame['channel'] = channel
        frame['order_id'] = channel + ':' + frame.SalesOrderNumber
        frame['line_id'] = frame.order_id + ':' + frame.SalesOrderLineNumber
        frame['party_id'] = channel + ':' + frame[party_key]
        if frame.party_id.isna().any():
            raise ValueError(f'{source}: thiếu khóa người mua')
        if channel == 'Reseller':
            frame = checked_join(frame, tables['DimReseller'][['ResellerKey', 'ResellerName', 'BusinessType']], 'ResellerKey')
            frame['store_id'] = frame.ResellerKey.astype('string')
            frame['store'] = frame.ResellerName + ' (#' + frame.ResellerKey + ')'
            frame['store_type'] = frame.BusinessType
        else:
            frame['store_id'] = pd.Series(pd.NA, index=frame.index, dtype='string')
            frame['store'] = 'Internet (không có mã cửa hàng)'
            frame['store_type'] = 'Không áp dụng'
        frame = checked_join(frame, product, 'ProductKey')
        frame = checked_join(frame, territory, 'SalesTerritoryKey')
        frame = checked_join(frame, tables['DimCurrency'][['CurrencyKey', 'CurrencyAlternateKey']], 'CurrencyKey')
        frame['category'] = frame.EnglishProductCategoryName.fillna('Unknown')
        frame['subcategory'] = frame.EnglishProductSubcategoryName.fillna('Unknown')
        frame['product'] = frame.EnglishProductName
        frame['region'] = frame.SalesTerritoryRegion
        frame['country'] = frame.SalesTerritoryCountry
        frame['purchase_month'] = frame.order_date.dt.strftime('%Y-%m')
        pieces.append(frame[['line_id', 'order_id', 'order_date', 'purchase_month', 'channel',
            'party_id', 'ProductKey', 'product', 'category', 'subcategory', 'region', 'country',
            'CurrencyAlternateKey', 'quantity', 'gross_units', 'discount_units',
            'revenue_units', 'cost_units', 'profit_units', 'store_id', 'store', 'store_type']])
    mart = pd.concat(pieces, ignore_index=True)
    if mart.line_id.duplicated().any():
        raise ValueError('Trùng line_id trong mart')
    return mart


def kpis(frame):
    revenue, cost, profit = (int(frame[c].sum()) for c in ['revenue_units', 'cost_units', 'profit_units'])
    return {'revenue_units': revenue, 'cost_units': cost, 'profit_units': profit,
        'margin_pct': profit / revenue * 100 if revenue else None,
        'orders': int(frame.order_id.nunique())}


def monthly_sales(frame):
    if frame.empty:
        return pd.DataFrame(columns=['purchase_month', 'revenue_units', 'profit_units', 'growth_pct'])
    months = pd.period_range(frame.purchase_month.min(), frame.purchase_month.max(), freq='M').astype(str)
    out = frame.groupby('purchase_month')[['revenue_units', 'profit_units']].sum().reindex(months, fill_value=0)
    out = out.rename_axis('purchase_month').reset_index()
    previous = out.revenue_units.shift(1)
    out['growth_pct'] = (out.revenue_units / previous.where(previous.ne(0)) - 1) * 100
    return out


def current_run(root=DATA / 'warehouse'):
    root = Path(root)
    return root / 'runs' / (root / 'current.txt').read_text(encoding='utf-8').strip()


def run(raw_dir=RAW, output_dir=DATA / 'warehouse'):
    start = time.perf_counter()
    raw_dir, output_dir = Path(raw_dir), Path(output_dir)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    destination = output_dir / 'runs' / run_id
    for sub in ['silver', 'gold', 'quarantine', 'quality']:
        (destination / sub).mkdir(parents=True)
    schema = (raw_dir / 'instawdbdw.sql').read_text(encoding='utf-8-sig')
    tables, reports, lineage, messages = {}, [], [], []
    for name in TABLES:
        path = raw_dir / (name + '.csv')
        columns = source_columns(schema, name)
        raw = pd.read_csv(path, sep='|', header=None, names=columns, dtype='string', quoting=csv.QUOTE_NONE)
        clean, rejected, quality = clean_source(name, raw)
        clean.to_parquet(destination / 'silver' / (name + '.parquet'), index=False, coerce_timestamps='us')
        rejected.to_parquet(destination / 'quarantine' / (name + '.parquet'), index=False, coerce_timestamps='us')
        tables[name] = clean
        reports.append(quality)
        lineage.append({'file': path.name, 'url': BASE + path.name,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size,
            'columns': columns})
        message = f'{name}: {len(raw):,} -> {len(clean):,}; rejected={len(rejected)}'
        messages.append(message)
        print(message, flush=True)
    fact = build_mart(tables)
    fact.to_parquet(destination / 'gold' / 'fact_sales.parquet', index=False, coerce_timestamps='us')
    fact.groupby('channel', sort=True, group_keys=False).head(10).to_csv(destination / 'gold' / 'sample_sales.csv', index=False)
    monthly_sales(fact).to_csv(destination / 'gold' / 'monthly_sales.csv', index=False)
    (destination / 'quality' / 'data_quality.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding='utf-8')
    pd.DataFrame([{k: r[k] for k in ['table', 'rows_before', 'duplicates_removed',
        'rows_rejected', 'rows_after', 'missing_pct_before']} for r in reports]).to_csv(
            destination / 'quality' / 'summary.csv', index=False)
    manifest = {'run_id': run_id, 'source': REPO, 'commit': COMMIT, 'license': 'MIT',
        'data_nature': 'Microsoft fictitious sample business, not observed real-world transactions',
        'money_scale': SCALE, 'reporting_currency': 'USD (AdventureWorks model base amounts)',
        'files': lineage, 'fact_rows': len(fact), 'kpis': kpis(fact),
        'date_min': str(fact.order_date.min()), 'date_max': str(fact.order_date.max()),
        'duration_seconds': time.perf_counter() - start,
        'raw_bytes': sum(x['bytes'] for x in lineage),
        'silver_bytes': sum(x.stat().st_size for x in (destination / 'silver').glob('*.parquet')),
        'fact_bytes': (destination / 'gold' / 'fact_sales.parquet').stat().st_size}
    (destination / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    published = f'Published run {run_id}; {manifest["duration_seconds"]:.2f}s'
    (destination / 'pipeline.log').write_text('\n'.join(messages + [published]) + '\n', encoding='utf-8')
    temp = output_dir / 'current.tmp'
    temp.write_text(run_id, encoding='utf-8')
    temp.replace(output_dir / 'current.txt')
    print(published, flush=True)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    if args.download:
        download()
    run()


if __name__ == '__main__':
    main()
