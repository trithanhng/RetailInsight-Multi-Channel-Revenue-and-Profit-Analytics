import pandas as pd
import pytest


def test_pandas_and_spark_queries_match_hand_calculated_totals(tmp_path):
    try:
        from src.pipeline.benchmark import compare
    except ImportError:
        pytest.fail('Chưa có phép so sánh pandas với Spark SQL')
    frame = pd.DataFrame({'order_id': ['a', 'a', 'b'],
        'party_id': ['u', 'u', 'v'],
        'purchase_month': ['2018-01', '2018-01', '2018-02'],
        'region': ['SP', 'SP', 'RJ'], 'category': ['x', 'y', 'x'],
        'channel': ['Internet', 'Internet', 'Reseller'],
        'revenue_units': [1000, 2000, 5000],
        'cost_units': [600, 1000, 5500], 'profit_units': [400, 1000, -500]})
    path = tmp_path / 'fact.parquet'
    frame.to_parquet(path, index=False)
    measurements = compare(path, tmp_path, repeats=1)
    assert len(measurements) == 6
    assert measurements['matches_baseline'].all()
    actual = pd.read_csv(tmp_path / 'spark_monthly.csv')
    assert actual.revenue_units.tolist() == [3000, 5000]
    assert actual.profit_units.tolist() == [1400, -500]
    assert actual.orders.tolist() == [1, 1]
