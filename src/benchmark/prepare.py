"""Build read-only-source projections for the eight SQL benchmark workloads."""
import csv
from pathlib import Path
import time

import pandas as pd

from src.cleaning.source import clean_source, money_units
from src.ingestion.source import source_columns
from src.utils.config import RAW
from src.utils.files import file_sha256

DIMENSIONS = {
    'DimProduct': ['ProductKey', 'ProductSubcategoryKey', 'EnglishProductName', 'ListPrice'],
    'DimProductSubcategory': ['ProductSubcategoryKey', 'ProductCategoryKey'],
    'DimProductCategory': ['ProductCategoryKey', 'EnglishProductCategoryName'],
    'DimReseller': ['ResellerKey', 'GeographyKey', 'ResellerName', 'BusinessType'],
    'DimGeography': ['GeographyKey', 'CountryRegionCode', 'StateProvinceCode'],
    'DimDate': ['DateKey', 'FullDateAlternateKey'],
    'DimCustomer': ['CustomerKey'],
}
FACTS = {'FactInternetSales': ('Internet', 'CustomerKey'),
    'FactResellerSales': ('Reseller', 'ResellerKey')}


def raw_hashes(raw_dir):
    return {file.name: file_sha256(file) for file in sorted(Path(raw_dir).iterdir()) if file.is_file()}


def validate_tables(tables):
    for name, columns in DIMENSIONS.items():
        key = columns[0]
        if tables[name][key].isna().any() or tables[name][key].duplicated().any():
            raise ValueError(f'{name}: null or duplicate primary key {key}')
    relations = [
        ('DimProduct', 'ProductSubcategoryKey', 'DimProductSubcategory', False),
        ('DimProductSubcategory', 'ProductCategoryKey', 'DimProductCategory', True),
        ('DimReseller', 'GeographyKey', 'DimGeography', False),
    ]
    for name, (_, party_key) in FACTS.items():
        if tables[name].line_id.isna().any() or tables[name].line_id.duplicated().any():
            raise ValueError(f'{name}: null or duplicate line_id')
        relations.extend([(name, 'ProductKey', 'DimProduct', True),
            (name, 'OrderDateKey', 'DimDate', True),
            (name, party_key, 'DimCustomer' if party_key == 'CustomerKey' else 'DimReseller', True)])
    for child, key, parent, required in relations:
        values = tables[child][key]
        parent_key = DIMENSIONS[parent][0]
        if (required and values.isna().any()) or not values.dropna().isin(tables[parent][parent_key]).all():
            raise ValueError(f'{child}: invalid foreign key {key}')
    for name, frame in tables.items():
        for column in [c for c in frame if c.endswith('_units')]:
            if name in FACTS and frame[column].isna().any():
                raise ValueError(f'{name}: missing money {column}')
            # Bound every possible group sum, including groups containing losses.
            if sum(abs(int(value)) for value in frame[column].dropna()) > 2**63 - 1:
                raise ValueError(f'{name}: {column} exceeds safe int64 aggregation range')


def prepare_tables(raw_dir=RAW):
    start = time.perf_counter()
    raw_dir = Path(raw_dir).resolve()
    before = raw_hashes(raw_dir)
    schema = (raw_dir / 'instawdbdw.sql').read_text(encoding='utf-8-sig')
    tables, inputs = {}, {}
    for name in [*DIMENSIONS, *FACTS]:
        source = raw_dir / f'{name}.csv'
        columns = source_columns(schema, name)
        raw = pd.read_csv(source, sep='|', header=None, names=columns, dtype='string',
            quoting=csv.QUOTE_NONE, usecols=DIMENSIONS.get(name))
        clean, rejected, quality = clean_source(name, raw)
        if len(rejected) or quality['duplicates_removed']:
            raise ValueError(f'{name}: benchmark requires valid, non-duplicated source rows')
        if name in FACTS:
            channel, party_key = FACTS[name]
            clean['order_id'] = channel + ':' + clean.SalesOrderNumber
            clean['line_id'] = clean.order_id + ':' + clean.SalesOrderLineNumber
            clean['channel'] = channel
            clean = clean[['line_id', 'order_id', 'channel', 'ProductKey', 'OrderDateKey',
                party_key, 'revenue_units', 'cost_units', 'profit_units']].copy()
        elif name == 'DimProduct':
            price = clean.ListPrice.map(money_units).astype('Int64')
            if (clean.ListPrice.notna() & price.isna()).any():
                raise ValueError('DimProduct: invalid ListPrice')
            clean = clean.drop(columns='ListPrice').assign(list_price_units=price)
        elif name == 'DimDate':
            clean['FullDateAlternateKey'] = pd.to_datetime(clean.FullDateAlternateKey, errors='raise')
            if clean.FullDateAlternateKey.isna().any():
                raise ValueError('DimDate: missing calendar date')
        for column in [c for c in clean if c.endswith('Key')]:
            if column != 'FullDateAlternateKey':
                clean[column] = pd.to_numeric(clean[column], errors='raise').astype('Int64')
        tables[name] = clean
        inputs[name] = {'raw_file': source.name, 'raw_sha256': before[source.name], 'raw_bytes': source.stat().st_size,
            'source_columns': columns, 'rows_before': len(raw), 'rows_after': len(clean),
            'rejected_rows': len(rejected), 'duplicates_removed': quality['duplicates_removed']}
    validate_tables(tables)
    for name, frame in tables.items():
        inputs[name].update(
            pandas_schema={column: str(dtype) for column, dtype in frame.dtypes.items()},
            null_counts={column: int(count) for column, count in frame.isna().sum().items()})
    after = raw_hashes(raw_dir)
    if before != after:
        raise ValueError('Original source files changed during preparation')
    manifest = {'raw_directory': str(raw_dir), 'raw_sha256_before': before,
        'raw_sha256_after': after, 'raw_unchanged': True, 'tables': inputs,
        'preparation_seconds': time.perf_counter() - start,
        'money_scale': 10000, 'currency': 'USD', 'status': 'passed'}
    return tables, manifest
