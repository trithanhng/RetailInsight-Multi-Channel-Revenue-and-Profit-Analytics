from decimal import Decimal
import json

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src.benchmark.prepare import DIMENSIONS, FACTS, prepare_tables, raw_hashes, validate_tables
from src.ingestion.source import download
from src.benchmark import runner as sql_benchmark
from src.benchmark.mart import spark_session
from src.benchmark.queries import (
    QUERIES, normalize_result, register_spark_tables, run_pandas_query, spark_query)


@pytest.fixture
def tables():
    data = {
        'DimProduct': pd.DataFrame({'ProductKey': [1, 2, 3, 4],
            'ProductSubcategoryKey': [1, 1, None, 1], 'EnglishProductName': ['a', 'b', 'c', 'd'],
            'list_price_units': [999999, 1000000, 1000001, None]}),
        'DimProductSubcategory': pd.DataFrame({'ProductSubcategoryKey': [1], 'ProductCategoryKey': [1]}),
        'DimProductCategory': pd.DataFrame({'ProductCategoryKey': [1], 'EnglishProductCategoryName': ['Bikes']}),
        'DimReseller': pd.DataFrame({'ResellerKey': [1, 2, 3, 4, 5, 6],
            'GeographyKey': [1, 1, 1, 1, 2, None], 'ResellerName': list('abcdef'),
            'BusinessType': ['Bike'] * 4 + [None, 'Specialty']}),
        'DimGeography': pd.DataFrame({'GeographyKey': [1, 2],
            'CountryRegionCode': ['US', 'CA'], 'StateProvinceCode': ['CA', 'CA']}),
        'DimDate': pd.DataFrame({'DateKey': [20131231, 20140101, 20141231],
            'FullDateAlternateKey': pd.to_datetime(['2013-12-31', '2014-01-01', '2014-12-31'])}),
        'DimCustomer': pd.DataFrame({'CustomerKey': list(range(1, 13))}),
    }
    for name, (channel, key) in FACTS.items():
        parties = [1, 1, 2, 3, 4, 5, 6] if channel == 'Reseller' else list(range(1, 13)) + [1]
        revenue = [100, 100, 200, 200, 50, 200, 0] if channel == 'Reseller' else [100] * 12 + [50]
        data[name] = pd.DataFrame({key: parties,
            'line_id': [f'{channel}:line{i}' for i in range(len(parties))],
            'order_id': [f'{channel}:order{i}' for i in parties], 'channel': channel,
            'ProductKey': [i % 4 + 1 for i in range(len(parties))],
            'OrderDateKey': [[20131231, 20140101, 20141231][i % 3] for i in range(len(parties))],
            'revenue_units': revenue, 'cost_units': [60] * len(parties),
            'profit_units': [value - 60 for value in revenue]})
    for name, frame in data.items():
        for column in frame:
            if column.endswith('Key') and column != 'FullDateAlternateKey' or column.endswith('_units'):
                frame[column] = frame[column].astype('Int64')
            elif column != 'FullDateAlternateKey':
                frame[column] = frame[column].astype('string')
    return data


@pytest.fixture(scope='module')
def spark():
    session = spark_session()
    yield session
    session.stop()


def write_raw(directory, tables):
    directory.mkdir()
    definitions = []
    for name, frame in tables.items():
        raw = frame.copy()
        if name in FACTS:
            raw['SalesOrderNumber'] = raw.order_id
            raw['SalesOrderLineNumber'] = pd.Series(range(1, len(raw) + 1), dtype='string')
            raw['SalesTerritoryKey'], raw['OrderQuantity'] = '1', '1'
            raw['OrderDate'] = raw.OrderDateKey.map(dict(zip(tables['DimDate'].DateKey,
                tables['DimDate'].FullDateAlternateKey.dt.strftime('%Y-%m-%d'))))
            for source, target in [('revenue_units', 'SalesAmount'), ('revenue_units', 'ExtendedAmount'),
                    ('cost_units', 'TotalProductCost')]:
                raw[target] = raw[source].map(lambda value: str(Decimal(int(value)) / 10000))
            raw['DiscountAmount'] = '0'
            raw = raw.drop(columns=['line_id', 'order_id', 'channel', 'revenue_units', 'cost_units', 'profit_units'])
        elif name == 'DimProduct':
            raw['ListPrice'] = raw.list_price_units.map(
                lambda value: None if pd.isna(value) else str(Decimal(int(value)) / 10000))
            raw = raw.drop(columns='list_price_units')
        definitions.append(f'CREATE TABLE [dbo].[{name}](\n' +
            '\n'.join(f'[{column}] [nvarchar](100) NULL,' for column in raw) + '\n) ON [PRIMARY];')
        raw.to_csv(directory / f'{name}.csv', sep='|', header=False, index=False)
    (directory / 'instawdbdw.sql').write_text('\n'.join(definitions))
    return directory


def test_preparation_preserves_raw_and_validates_money(tmp_path, tables):
    raw = write_raw(tmp_path / 'raw', tables)
    before = raw_hashes(raw)
    prepared, manifest = prepare_tables(raw)
    assert raw_hashes(raw) == before == manifest['raw_sha256_before']
    assert manifest['raw_unchanged']
    assert len(manifest['tables']) == 9
    actual = prepared['DimProduct']
    assert list(tmp_path.iterdir()) == [raw]
    assert actual.list_price_units.iloc[:3].tolist() == [999999, 1000000, 1000001]
    assert pd.isna(actual.list_price_units.iloc[3])
    assert all(value['rejected_rows'] == 0 for value in manifest['tables'].values())


def test_source_download_never_overwrites_existing_files(tmp_path, monkeypatch):
    for name in ['DimDate.csv', 'instawdbdw.sql', 'license.txt']:
        (tmp_path / name).write_text('original-content')
    before = raw_hashes(tmp_path)

    def forbidden(*args, **kwargs):
        pytest.fail('Existing sources must not be downloaded again')

    monkeypatch.setattr('urllib.request.urlopen', forbidden)
    download(tmp_path, tables=['DimDate'])
    assert before == raw_hashes(tmp_path)


def test_invalid_source_price_is_not_silently_dropped(tmp_path, tables):
    tables['DimProduct'].loc[0, 'list_price_units'] = -1
    raw = write_raw(tmp_path / 'raw', tables)
    before = raw_hashes(raw)
    with pytest.raises(ValueError, match='ListPrice'):
        prepare_tables(raw)
    assert raw_hashes(raw) == before


@pytest.mark.parametrize('problem', ['duplicate_dimension', 'null_primary_key', 'missing_fk', 'overflow'])
def test_invalid_tables_are_rejected(tables, problem):
    if problem == 'duplicate_dimension':
        tables['DimProduct'] = pd.concat([tables['DimProduct']] * 2, ignore_index=True)
    elif problem == 'null_primary_key':
        tables['DimCustomer'].loc[0, 'CustomerKey'] = pd.NA
    elif problem == 'missing_fk':
        tables['FactResellerSales'].loc[0, 'ResellerKey'] = 999
    else:
        tables['FactInternetSales']['revenue_units'] = 2**62
    with pytest.raises(ValueError):
        validate_tables(tables)


@pytest.mark.parametrize('case', ['normal', 'empty', 'large_money'])
def test_all_eight_queries_match_exactly(spark, tables, case):
    if case == 'empty':
        tables = {name: frame.iloc[:0] for name, frame in tables.items()}
    elif case == 'large_money':
        tables['FactInternetSales'].loc[0, 'revenue_units'] = 2**53 + 1
        tables['FactInternetSales'].loc[0, 'profit_units'] = 2**53 + 1 - 60
    validate_tables(tables)
    register_spark_tables(spark, tables)
    results = {}
    for query in QUERIES:
        actual = normalize_result(query, spark_query(query, spark).toPandas())
        baseline = run_pandas_query(query, tables)
        assert_frame_equal(actual, baseline, check_dtype=False, check_exact=True)
        results[query] = actual
        if case == 'empty':
            assert actual.empty
    if case == 'normal':
        assert results['Q1'].ProductKey.tolist() == [2, 3]
        assert results['Q2'].set_index('ResellerKey').loc[1, ['revenue_units', 'orders']].tolist() == [200, 1]
        assert results['Q3'].ProductCategoryKey.isna().any()
        assert results['Q3'].revenue_units.sum() == 2100
        assert results['Q3'].profit_units.sum() == 900
        assert results['Q4'].revenue_units.sum() == 850
        assert results['Q4'].CountryRegionCode.isna().any()
        assert set(results['Q5'].purchase_month) == {'2013-12', '2014-01', '2014-12'}
        assert results['Q5'].revenue_units.tolist() == [450, 300, 400, 150, 400, 400]
        us = results['Q6'].loc[results['Q6'].CountryRegionCode.eq('US')]
        assert us.ResellerKey.tolist() == [1, 2, 3]
        assert us['rank'].tolist() == [1, 2, 3]
        assert len(results['Q6']) == 5
        assert results['Q7'].orders.sum() == 6
        assert results['Q7'].BusinessType.isna().any()
        assert results['Q7'].set_index('BusinessType').loc['Specialty', 'profit_units'] == -60
        assert results['Q8'].CustomerKey.tolist() == list(range(1, 11))
        assert results['Q8'].revenue_units.iloc[0] == 150
    elif case == 'large_money':
        assert results['Q8'].revenue_units.iloc[0] == 2**53 + 51


def test_extended_runner_saves_complete_evidence(tmp_path, tables, monkeypatch):
    from pyspark.sql.readwriter import DataFrameReader

    def forbidden(*args, **kwargs):
        pytest.fail('SQL benchmark must not read or write Parquet')

    monkeypatch.setattr(pd, 'read_parquet', forbidden)
    monkeypatch.setattr(pd.DataFrame, 'to_parquet', forbidden)
    monkeypatch.setattr(DataFrameReader, 'parquet', forbidden)
    raw = write_raw(tmp_path / 'raw', tables)
    monkeypatch.setattr(sql_benchmark, 'hardware_info', lambda: {'cpu_model': 'fixture', 'ram_bytes': 1})
    destination = sql_benchmark.run_benchmark(tmp_path / 'output', raw, repeats=1)
    metadata = json.loads((destination / 'environment.json').read_text())
    assert metadata['status'] == 'passed'
    assert metadata['raw_unchanged'] and metadata['sql_unchanged']
    assert metadata['spark_table_setup_seconds'] >= 0
    assert set(metadata['sql_statements']) == set(QUERIES)
    assert len(pd.read_csv(destination / 'measurements.csv')) == 16
    assert len(list((destination / 'plans').glob('*.txt'))) == 16
    assert len(list((destination / 'results').glob('*.csv'))) == 16
    assert not (destination / 'queries').exists()
    assert not (destination / 'tables').exists()
    assert not list(destination.rglob('*.parquet'))
    assert (tmp_path / 'output/current.txt').read_text() == destination.name
    assert (destination / 'REPORT.md').is_file()


def test_wrong_result_cannot_publish_a_successful_run(tmp_path, tables, monkeypatch):
    raw = write_raw(tmp_path / 'raw', tables)
    original = sql_benchmark.run_pandas_query

    def wrong(query, inputs):
        result = original(query, inputs)
        if query == 'Q1':
            result.loc[0, 'list_price_units'] += 1
        return result

    monkeypatch.setattr(sql_benchmark, 'run_pandas_query', wrong)
    monkeypatch.setattr(sql_benchmark, 'hardware_info', lambda: {})
    with pytest.raises(AssertionError):
        sql_benchmark.run_benchmark(tmp_path / 'output', raw, repeats=1)
    assert not (tmp_path / 'output/current.txt').exists()
    destination = next((tmp_path / 'output/runs').iterdir())
    assert json.loads((destination / 'environment.json').read_text())['status'] == 'failed'
    assert not pd.read_csv(destination / 'measurements.csv').matches_baseline.all()


def test_invalid_run_preserves_previous_publication(tmp_path, monkeypatch):
    output, raw = tmp_path / 'output', tmp_path / 'raw'
    output.mkdir()
    raw.mkdir()
    (output / 'current.txt').write_text('previous-success')
    monkeypatch.setattr(sql_benchmark, 'hardware_info', lambda: {})
    with pytest.raises(FileNotFoundError):
        sql_benchmark.run_benchmark(output, raw, repeats=1)
    assert (output / 'current.txt').read_text() == 'previous-success'
    failed = next((output / 'runs').iterdir())
    assert json.loads((failed / 'environment.json').read_text())['status'] == 'failed'
    with pytest.raises(ValueError, match='outside'):
        sql_benchmark.run_benchmark(raw, raw)
    with pytest.raises(ValueError, match='repeats'):
        sql_benchmark.run_benchmark(output, raw, repeats=0)
