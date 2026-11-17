import importlib

import pandas as pd
import pytest


def core():
    try:
        return importlib.import_module('retail_bi.pipeline')
    except ImportError:
        pytest.fail('Pipeline AdventureWorks chưa có')


def test_preserves_four_decimal_money_and_does_not_double_subtract_discount():
    api = core()
    raw = pd.DataFrame({'SalesOrderNumber': ['SO1', 'SO1', 'SO2'],
        'SalesOrderLineNumber': ['1', '1', '1'], 'ProductKey': ['1'] * 3,
        'SalesTerritoryKey': ['1'] * 3, 'CustomerKey': ['42'] * 3,
        'OrderDate': ['2013-01-01'] * 2 + ['bad'],
        'OrderQuantity': ['2'] * 3, 'ExtendedAmount': ['10.1234'] * 3,
        'DiscountAmount': ['1.0000'] * 3, 'SalesAmount': ['9.1234'] * 3,
        'TotalProductCost': ['4.4321'] * 3})
    clean, rejected, report = api.clean_source('FactInternetSales', raw)
    assert len(clean) == 1
    assert len(rejected) == 1
    assert clean.revenue_units.iloc[0] == 91234
    assert clean.cost_units.iloc[0] == 44321
    assert clean.profit_units.iloc[0] == 46913
    assert report['duplicates_removed'] == 1


def test_margin_is_weighted_and_losses_remain_visible():
    api = core()
    frame = pd.DataFrame({'order_id': ['a', 'b'], 'revenue_units': [1000000, 100000],
        'cost_units': [600000, 200000], 'profit_units': [400000, -100000]})
    out = api.kpis(frame)
    assert out['revenue_units'] == 1100000
    assert out['profit_units'] == 300000
    assert out['margin_pct'] == pytest.approx(27.27272727)
    assert api.kpis(frame.iloc[:0])['margin_pct'] is None


def test_month_gap_and_zero_denominator_are_not_invented_growth():
    api = core()
    frame = pd.DataFrame({'purchase_month': ['2013-01', '2013-03'],
        'revenue_units': [100, 200], 'profit_units': [30, 20]})
    result = api.monthly_sales(frame)
    assert result.revenue_units.tolist() == [100, 0, 200]
    assert result.profit_units.tolist() == [30, 0, 20]
    assert result.iloc[1].growth_pct == -100
    assert pd.isna(result.iloc[2].growth_pct)


def test_invalid_negative_revenue_is_quarantined():
    api = core()
    raw = pd.DataFrame({'SalesOrderNumber': ['SO1'], 'SalesOrderLineNumber': ['1'],
        'ProductKey': ['1'], 'SalesTerritoryKey': ['1'], 'ResellerKey': ['2'],
        'OrderDate': ['2013-01-01'], 'OrderQuantity': ['1'], 'ExtendedAmount': ['-10'],
        'DiscountAmount': ['0'], 'SalesAmount': ['-10'], 'TotalProductCost': ['5']})
    clean, rejected, _ = api.clean_source('FactResellerSales', raw)
    assert clean.empty
    assert len(rejected) == 1


def test_conflicting_line_key_cannot_silently_duplicate_revenue():
    api = core()
    raw = pd.DataFrame({'ProductCategoryKey': ['1', '1'],
        'EnglishProductCategoryName': ['Bikes', 'Clothing']})
    with pytest.raises(ValueError, match='ProductCategoryKey'):
        api.clean_source('DimProductCategory', raw)


def test_channel_order_ids_do_not_collide_and_bad_foreign_keys_fail():
    api = core()
    common = {'SalesOrderNumber': ['SO1'], 'SalesOrderLineNumber': ['1'],
        'ProductKey': ['1'], 'SalesTerritoryKey': ['1'], 'CurrencyKey': ['100'],
        'order_date': pd.to_datetime(['2013-01-01']), 'quantity': [1],
        'gross_units': [100], 'discount_units': [0], 'revenue_units': [100],
        'cost_units': [60], 'profit_units': [40]}
    tables = {
        'FactInternetSales': pd.DataFrame({**common, 'CustomerKey': ['1']}),
        'FactResellerSales': pd.DataFrame({**common, 'ResellerKey': ['1']}),
        'DimProduct': pd.DataFrame({'ProductKey': ['1'], 'ProductSubcategoryKey': ['10'],
            'EnglishProductName': ['Bike']}),
        'DimProductSubcategory': pd.DataFrame({'ProductSubcategoryKey': ['10'],
            'ProductCategoryKey': ['20'], 'EnglishProductSubcategoryName': ['Road']}),
        'DimProductCategory': pd.DataFrame({'ProductCategoryKey': ['20'],
            'EnglishProductCategoryName': ['Bikes']}),
        'DimSalesTerritory': pd.DataFrame({'SalesTerritoryKey': ['1'],
            'SalesTerritoryRegion': ['North'], 'SalesTerritoryCountry': ['US']}),
        'DimCurrency': pd.DataFrame({'CurrencyKey': ['100'], 'CurrencyAlternateKey': ['USD']}),
        'DimReseller': pd.DataFrame({'ResellerKey': ['1'], 'ResellerName': ['Bike Store'],
            'BusinessType': ['Specialty Bike Shop']}),
    }
    result = api.build_mart(tables)
    assert result.order_id.tolist() == ['Internet:SO1', 'Reseller:SO1']
    assert result.line_id.nunique() == 2
    assert api.kpis(result)['revenue_units'] == 200
    assert 'store_id' in result.columns, 'Mart phải giữ mã đại lý/cửa hàng có sẵn trong nguồn'
    assert result.store_id.iloc[1] == '1'
    assert pd.isna(result.store_id.iloc[0])
    assert 'Bike Store' in result.store.iloc[1]
    tables['FactResellerSales'].loc[0, 'ResellerKey'] = 'missing'
    with pytest.raises(ValueError, match='ResellerKey'):
        api.build_mart(tables)
    tables['FactResellerSales'].loc[0, 'ResellerKey'] = '1'
    tables['FactInternetSales'].loc[0, 'ProductKey'] = 'missing'
    with pytest.raises(ValueError, match='ProductKey'):
        api.build_mart(tables)


def test_duplicate_dimension_key_cannot_multiply_rows():
    api = core()
    left = pd.DataFrame({'ProductKey': ['1'], 'revenue_units': [100]})
    right = pd.DataFrame({'ProductKey': ['1', '1'], 'category': ['A', 'B']})
    with pytest.raises(pd.errors.MergeError):
        api.checked_join(left, right, 'ProductKey')


def test_failed_ingestion_keeps_previous_published_run(tmp_path):
    api = core()
    warehouse = tmp_path / 'warehouse'
    warehouse.mkdir()
    (warehouse / 'current.txt').write_text('previous-success', encoding='utf-8')
    with pytest.raises(FileNotFoundError):
        api.run(tmp_path / 'missing-raw', warehouse)
    assert (warehouse / 'current.txt').read_text(encoding='utf-8') == 'previous-success'


def test_published_run_proves_store_source_and_has_a_pipeline_log():
    import json
    api = core()
    run = api.current_run()
    manifest = json.loads((run / 'manifest.json').read_text(encoding='utf-8'))
    assert 'DimReseller.csv' in {item['file'] for item in manifest['files']}
    assert (run / 'pipeline.log').exists(), 'Cần log thực thi đi kèm run để làm minh chứng'
    assert 'DimReseller: 701 -> 701' in (run / 'pipeline.log').read_text(encoding='utf-8')
    sample = pd.read_csv(run / 'gold/sample_sales.csv')
    assert set(sample.channel) == {'Internet', 'Reseller'}, 'Mẫu bàn giao cần thể hiện cả hai kênh'
