import fitz
import pytest


def test_report_contains_measured_kpis_and_fictitious_source_notice(tmp_path):
    try:
        from retail_bi.report import build_report
    except ImportError:
        pytest.fail('Chưa có báo cáo PDF')
    output = tmp_path / 'report.pdf'
    build_report(output)
    with fitz.open(output) as pdf:
        text = '\n'.join(p.get_text() for p in pdf)
        assert len(pdf) >= 5
        assert '109,809,274.20' in text
        assert '12,551,366.25' in text
        assert 'giả lập' in text
        assert any('winter-1402' in link.get('uri', '') for page in pdf for link in page.get_links())


def test_markdown_report_reuses_measured_totals_and_comparable_month(tmp_path):
    from retail_bi import report
    assert hasattr(report, 'build_markdown_report'), 'Chưa có bản báo cáo đọc trực tiếp trên GitHub'
    output = report.build_markdown_report(tmp_path / 'report.md')
    content = output.read_text(encoding='utf-8')
    assert '109.809.274,20' in content
    assert '12.551.366,25' in content
    assert '2013-10' in content
    assert 'giả lập' in content
    assert 'https://github.com/winter-1402/' in content
