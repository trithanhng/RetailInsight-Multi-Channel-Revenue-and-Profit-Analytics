import importlib
from io import BytesIO

import pandas as pd
import pytest


def analytics():
    try:
        return importlib.import_module('src.pipeline.analytics')
    except ImportError:
        pytest.fail('Chưa có lớp phân tích dùng chung cho dashboard')


def test_growth_uses_last_whole_month_shared_by_selected_channels():
    api = analytics()
    source = pd.DataFrame({
        'channel': ['Internet'] * 4 + ['Reseller'] * 3,
        'order_date': pd.to_datetime(['2013-01-01', '2013-02-01', '2013-03-31',
            '2013-04-30', '2013-01-01', '2013-02-01', '2013-03-15']),
        'revenue_units': [100, 150, 900, 900, 100, 150, 900],
        'profit_units': [10, 15, 90, 90, 10, 15, 90],
    })
    monthly = api.monthly_view(source, '2013-01-01', '2013-04-30', source)
    growth = api.growth_metric(monthly)
    assert growth['period'] == '2013-02'
    assert growth['growth_pct'] == 50
    assert monthly.complete.tolist() == [True, True, False, False]


def test_sparse_product_keeps_zero_months_and_zero_growth_denominator():
    api = analytics()
    scope = pd.DataFrame({'order_date': pd.to_datetime(['2013-01-01', '2013-03-31']),
        'revenue_units': [100, 200], 'profit_units': [20, 40]})
    source = pd.DataFrame({'channel': ['Internet', 'Internet'],
        'order_date': pd.to_datetime(['2013-01-01', '2013-03-31'])})
    result = api.monthly_view(scope, '2013-01-01', '2013-03-31', source)
    assert result.revenue_units.tolist() == [100, 0, 200]
    assert result.iloc[1].growth_pct == -100
    assert pd.isna(api.growth_metric(result)['growth_pct'])


def test_partial_previous_month_does_not_create_a_comparable_growth_value():
    api = analytics()
    source = pd.DataFrame({'channel': ['Internet', 'Internet'],
        'order_date': pd.to_datetime(['2013-01-15', '2013-02-28']),
        'revenue_units': [100, 200], 'profit_units': [20, 40]})
    result = api.monthly_view(source, '2013-01-15', '2013-02-28', source)
    assert api.growth_metric(result)['period'] == '2013-02'
    assert pd.isna(api.growth_metric(result)['growth_pct'])


def test_filter_intersection_and_end_day_are_applied_to_every_metric():
    api = analytics()
    frame = pd.DataFrame({'order_date': pd.to_datetime(['2013-01-31 23:59', '2013-02-01 00:00', '2013-01-31 00:00']),
        'channel': ['Internet', 'Internet', 'Reseller'], 'region': ['North'] * 3,
        'category': ['Bikes'] * 3, 'product': ['Bike'] * 3})
    out = api.filter_sales(frame, '2013-01-01', '2013-01-31', channel='Internet', region='North')
    assert out.index.tolist() == [0]


def test_grouped_margin_uses_totals():
    api = analytics()
    frame = pd.DataFrame({'channel': ['Internet', 'Internet'], 'order_id': ['a', 'b'],
        'revenue_units': [1000000, 100000], 'profit_units': [400000, -100000],
        'cost_units': [600000, 200000], 'quantity': [1, 2]})
    out = api.group_metrics(frame, ['channel'])
    assert out.revenue_usd.tolist() == [110]
    assert out.gross_profit_usd.tolist() == [30]
    assert out.margin_pct.iloc[0] == pytest.approx(27.27272727)
    assert out.orders.tolist() == [2]


def test_vietnamese_numbers_keep_exact_usd_and_negative_sign():
    api = analytics()
    assert api.number_vn(109809274.203) == '109.809.274,20'
    assert api.number_vn(-1234.5) == '-1.234,50'
    assert api.compact_money(109809274.203) == '109,81 triệu'


def test_csv_export_uses_filtered_usd_totals_and_public_column_names():
    api = analytics()
    frame = pd.DataFrame({'order_date': pd.to_datetime(['2013-01-01'] * 2),
        'channel': ['Internet', 'Reseller'], 'order_id': ['a', 'b'],
        'revenue_units': [1000000, 5000000], 'cost_units': [600000, 3500000],
        'profit_units': [400000, 1500000], 'quantity': [1, 5]})
    scope = api.filter_sales(frame, '2013-01-01', '2013-01-31', channel='Internet')
    assert hasattr(api, 'public_table'), 'Thiếu bảng xuất công khai dùng chung'
    assert hasattr(api, 'csv_bytes'), 'Thiếu hàm xuất CSV dùng cho nút tải'
    table = api.public_table(api.group_metrics(scope, ['channel']), ['channel'])
    decoded = pd.read_csv(BytesIO(api.csv_bytes(table)))
    assert decoded['Doanh thu (USD)'].tolist() == [100]
    assert decoded['Lợi nhuận gộp (USD)'].tolist() == [40]
    assert decoded['Kênh bán'].tolist() == ['Internet']
    assert not any(c.endswith('_units') for c in decoded.columns)


def test_store_filter_selects_the_named_reseller_without_changing_totals():
    api = analytics()
    source = pd.DataFrame({'order_date': pd.to_datetime(['2013-01-01'] * 2),
        'store': ['Bike Store (#1)', 'Bike Store (#2)']})
    result = api.filter_sales(source, '2013-01-01', '2013-01-31', store='Bike Store (#1)')
    assert result.index.tolist() == [0]
