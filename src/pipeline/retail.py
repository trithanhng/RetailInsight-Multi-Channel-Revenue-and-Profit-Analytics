"""Build and publish validated Parquet runs and the retail data mart."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import pandas as pd

from src.cleaning.source import clean_source
from src.ingestion.source import BASE, COMMIT, REPO, TABLES, download, source_columns
from src.utils.config import DATA, RAW, SCALE
from .analytics import kpis, monthly_sales


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
