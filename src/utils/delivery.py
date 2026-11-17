"""Xuất minh chứng và gói mã nguồn để kiểm tra trước khi đưa lên GitHub."""
import argparse
import csv
import json
import re
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile, ZIP_DEFLATED

import pandas as pd

from src.pipeline.analytics import monthly_view
from src.pipeline.retail import current_run
from src.ingestion.source import source_columns
from .config import RAW, ROOT


def verify_tests(destination=ROOT / 'output' / 'evidence'):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, '-X', 'utf8', '-m', 'pytest', '-q']
    with (destination / 'tests.log').open('w', encoding='utf-8') as log:
        result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    (destination / 'test_status.json').write_text(json.dumps({
        'command': 'python -X utf8 -m pytest -q', 'exit_code': result.returncode}, indent=2), encoding='utf-8')
    print((destination / 'tests.log').read_text(encoding='utf-8'), flush=True)
    if result.returncode:
        raise RuntimeError('Kiểm thử thất bại; xem output/evidence/tests.log')
    return destination / 'tests.log'


def export_evidence(destination=ROOT / 'output' / 'evidence'):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    run = current_run()
    optional = {'benchmark.csv', 'benchmark_summary.csv', 'benchmark_environment.json',
        'spark_monthly.csv', 'spark_region.csv', 'spark_category.csv', 'spark_customer_segments.csv'}
    load_pattern = re.compile(r'^(?:load_scale_|scale)\d+_(?:benchmark(?:_summary)?\.csv|benchmark_environment\.json|synthetic_provenance\.json)$')
    # Reconcile only owned optional outputs; keep verification logs and reader files.
    for previous in destination.iterdir():
        if previous.is_file() and (previous.name in optional or load_pattern.fullmatch(previous.name)):
            previous.unlink()
    for name in ['manifest.json', 'benchmark.csv', 'benchmark_summary.csv', 'benchmark_environment.json',
            'spark_monthly.csv', 'spark_region.csv', 'spark_category.csv', 'spark_customer_segments.csv']:
        if (run / name).exists():
            shutil.copyfile(run / name, destination / name)
    for src, name in [('gold/sample_sales.csv', 'sample_sales.csv'),
            ('quality/data_quality.json', 'data_quality.json'), ('quality/summary.csv', 'quality_summary.csv')]:
        shutil.copyfile(run / src, destination / name)
    if (run / 'pipeline.log').exists():
        shutil.copyfile(run / 'pipeline.log', destination / 'pipeline.log')
    fact = pd.read_parquet(run / 'gold/fact_sales.parquet')
    month = monthly_view(fact, fact.order_date.min(), fact.order_date.max(), fact)
    month[['purchase_month', 'revenue_usd', 'gross_profit_usd', 'growth_pct', 'complete', 'comparable']].to_csv(
        destination / 'monthly_sales.csv', index=False)
    for load in run.glob('load_scale_*'):
        for name in ['benchmark.csv', 'benchmark_summary.csv', 'benchmark_environment.json', 'synthetic_provenance.json']:
            if (load / name).exists():
                shutil.copyfile(load / name, destination / (load.name + '_' + name))
    shutil.copyfile(RAW / 'license.txt', destination / 'MICROSOFT_LICENSE.txt')
    schema = (RAW / 'instawdbdw.sql').read_text(encoding='utf-8-sig')
    fields = ['SalesOrderNumber', 'SalesOrderLineNumber', 'OrderDate', 'OrderQuantity',
        'ExtendedAmount', 'DiscountAmount', 'SalesAmount', 'TotalProductCost']
    for table in ['FactInternetSales', 'FactResellerSales']:
        before = pd.read_csv(RAW / (table + '.csv'), sep='|', header=None,
            names=source_columns(schema, table), dtype='string', quoting=csv.QUOTE_NONE, nrows=8)
        before[fields].to_csv(destination / (table + '_before.csv'), index=False)
        after = pd.read_parquet(run / 'silver' / (table + '.parquet')).head(8)
        after[fields + ['revenue_units', 'cost_units', 'profit_units']].to_csv(
            destination / (table + '_after.csv'), index=False)
    print(f'Evidence exported to {destination}', flush=True)
    return destination


def build_package(output=ROOT / 'output/AdventureWorks_Retail_BI_GitHub.zip'):
    files = []
    allowed = {'.py', '.sql', '.md', '.css', '.png', '.svg', '.yml', '.yaml', '.json', '.csv', '.txt', '.log'}
    for folder in ['src', 'dashboard', 'tests', 'sql', 'docs', 'assets', '.github', 'output/evidence']:
        for file in (ROOT / folder).rglob('*'):
            if (file.is_file() and file.suffix.lower() in allowed
                    and '__pycache__' not in file.parts and 'local' not in file.parts
                    and not file.name.startswith('.env') and file.name not in {'kaggle.json', 'secrets.toml'}):
                files.append(file)
    for name in ['README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md', 'requirements.txt', 'pytest.ini',
            '.gitignore', '.gitattributes', 'setup.cmd', 'run.cmd', 'setup.ps1', 'run.ps1',
            '.streamlit/config.toml', 'output/Bao_cao_pipeline_dashboard.pdf']:
        file = ROOT / name
        if file.exists():
            files.append(file)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, 'w', ZIP_DEFLATED) as zipped:
        for file in sorted(set(files)):
            zipped.write(file, file.relative_to(ROOT).as_posix())
    with ZipFile(output) as zipped:
        bad = zipped.testzip()
        if bad:
            raise ValueError(f'Gói ZIP lỗi ở {bad}')
    print(f'Package created: {output} ({output.stat().st_size:,} bytes)', flush=True)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', action='store_true')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        verify_tests()
    export_evidence()
    if args.package:
        build_package()


if __name__ == '__main__':
    main()
