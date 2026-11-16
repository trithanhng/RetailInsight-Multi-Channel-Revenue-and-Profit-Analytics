from datetime import date
from streamlit.testing.v1 import AppTest


def app():
    app = AppTest.from_file('dashboard.py', default_timeout=30).run()
    assert not app.exception
    return app


def test_defaults_are_compact_and_financial_totals_are_correct():
    ui = app()
    assert not ui.multiselect
    assert ui.selectbox(key='channel').value == 'Tất cả'
    assert ui.selectbox(key='region').value == 'Tất cả'
    assert ui.metric[0].value == '109,81 triệu'
    assert ui.metric[2].value == '11,43%'
    assert ui.metric[3].value == '+36,50%'


def test_reset_does_not_show_duplicate_date_default_warning(monkeypatch):
    from streamlit.elements.lib import policies
    monkeypatch.setattr(policies, '_shown_default_value_warning', False)
    ui = app().selectbox(key='channel').set_value('Internet').run()
    ui.button(key='reset_filters').click().run()
    assert not ui.exception
    assert not ui.warning
    assert ui.metric[0].value == '109,81 triệu'


def test_clearing_a_date_requests_a_complete_range():
    ui = app().date_input(key='date_start').set_value(None).run()
    assert not ui.exception
    assert ui.warning
    assert not ui.metric


def test_channel_filter_updates_the_same_financial_scope():
    ui = app().selectbox(key='channel').set_value('Internet').run()
    assert not ui.exception
    assert ui.metric[0].value == '29,36 triệu'
    assert ui.metric[2].value == '41,15%'
    assert any('12/2013' in item.value for item in ui.caption)
    ui.selectbox(key='channel').set_value('Reseller').run()
    assert any('10/2013' in item.value for item in ui.caption)


def test_changing_category_resets_an_incompatible_product():
    ui = app().selectbox(key='category').set_value('Clothing').run()
    item = ui.selectbox(key='product').options[1]
    ui.selectbox(key='product').set_value(item).run()
    ui.selectbox(key='category').set_value('Bikes').run()
    assert not ui.exception
    assert ui.selectbox(key='product').value == 'Tất cả'


def test_empty_combination_and_reset_are_understandable():
    ui = app().selectbox(key='channel').set_value('Internet').run()
    ui.selectbox(key='category').set_value('Components').run()
    assert not ui.exception
    assert len(ui.metric) == 0
    assert any('Không có giao dịch' in item.value for item in ui.info)
    ui.button(key='reset_filters').click().run()
    assert not ui.exception
    assert ui.metric[0].value == '109,81 triệu'


def test_reversed_dates_show_a_validation_message_without_a_crash():
    ui = app()
    ui.date_input(key='date_start').set_value(date(2014, 1, 28)).run()
    ui.date_input(key='date_end').set_value(date(2011, 1, 1)).run()
    assert not ui.exception
    assert ui.error
    assert not ui.metric


def test_common_period_shortcut_sets_both_date_boundaries():
    ui = app().selectbox(key='period').set_value('Kỳ chung hai kênh').run()
    assert not ui.exception
    assert ui.date_input(key='date_start').value == date(2011, 1, 1)
    assert ui.date_input(key='date_end').value == date(2013, 10, 31)


def test_loss_making_product_remains_visible_in_metrics_and_ranking():
    ui = app().selectbox(key='channel').set_value('Reseller').run()
    ui.selectbox(key='product').set_value('AWC Logo Cap').run()
    ui.selectbox(key='ranking').set_value('Lợi nhuận thấp nhất').run()
    assert not ui.exception
    assert ui.metric[1].value.startswith('-')
    assert ui.metric[2].value.startswith('-')


def test_narrow_manual_dates_have_no_invented_growth_and_can_reset():
    ui = app()
    ui.date_input(key='date_start').set_value(date(2013, 1, 15)).run()
    ui.date_input(key='date_end').set_value(date(2013, 1, 31)).run()
    assert not ui.exception
    assert ui.selectbox(key='period').value == 'Tùy chọn'
    assert ui.metric[3].value == '—'
    ui.button(key='reset_filters').click().run()
    assert ui.date_input(key='date_start').value == date(2010, 12, 29)


def test_reseller_store_filter_and_reset_keep_a_consistent_scope():
    ui = app().selectbox(key='channel').set_value('Reseller').run()
    assert any(widget.key == 'store' for widget in ui.selectbox), 'Thiếu bộ lọc đại lý/cửa hàng'
    ui.selectbox(key='store').set_value('A Bike Store (#1)').run()
    assert not ui.exception
    assert ui.metric[0].value != '80,45 triệu'
    ui.button(key='reset_filters').click().run()
    assert ui.selectbox(key='store').value == 'Tất cả'
    assert ui.metric[0].value == '109,81 triệu'
