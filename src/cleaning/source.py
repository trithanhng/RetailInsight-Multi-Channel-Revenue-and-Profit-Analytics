"""Validate source rows, normalize money and quarantine invalid records."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import pandas as pd

from src.utils.config import SCALE

MONEY = {'SalesAmount': 'revenue_units', 'TotalProductCost': 'cost_units',
    'DiscountAmount': 'discount_units', 'ExtendedAmount': 'gross_units'}


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
